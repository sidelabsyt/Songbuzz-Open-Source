import time
import spotipy
import re
import socket
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from backend.credintals import Credintals

class SpotifyPlayer:
    playing = False
    current_track: dict = None
    regex = re.compile('[^a-zA-Z0-9]')
    
    def __init__(self):
        self.sp = spotipy.Spotify(
            auth_manager=Credintals.OAuth
        )
        # Wir initialisieren die Variable mit None
        self._cached_device_id = None

    def _get_active_device_id(self) -> str:
        # Falls wir schon eine ID haben, geben wir diese direkt zurück
        if self._cached_device_id:
            return self._cached_device_id

        devices = self.sp.devices().get("devices", [])
        local_pc_name = re.sub(self.regex, ' ', socket.gethostname().split('.')[0])
        
        target_id = None

        # 1. Suche nach lokalem PC
        for d in devices:
            if re.sub(self.regex, ' ', d.get('name')) == local_pc_name:
                print(f'>> local pc with spotify detected << ==> {d}')
                target_id = d['id']
                break

        # 2. Falls kein lokaler PC, nimm das aktuell aktive Gerät
        if not target_id:
            for d in devices:
                if d.get("is_active"):
                    target_id = d["id"]
                    break
        
        # 3. Failsafe (deine bestehende ID)
        if not target_id:
            target_id = ''

        # Speichere die ID für zukünftige Aufrufe
        self._cached_device_id = target_id
        return target_id

    def startsong(self, songdict: dict, start_second: int = 0):
        # Nutzt jetzt die gecachte ID oder sucht sie beim ersten Mal
        device_id = self._get_active_device_id()
        try:
            self.sp.start_playback(
                device_id=device_id,
                uris=[songdict['track_id'] if 'track_id' in songdict else songdict['uri']],
                position_ms=start_second * 1000
            )
            self.current_track = songdict
            self.playing = True
        except SpotifyException as e:
            # Falls ein Fehler auftritt (z.B. Device nicht mehr verfügbar), 
            # setzen wir den Cache zurück, damit beim nächsten Mal neu gesucht wird.
            self._cached_device_id = None
            raise RuntimeError(f"Spotify start_playback fehlgeschlagen: {e}")

    def pause(self):
        """
        Pausiert die aktuelle Wiedergabe.
        """
        try:
            self.sp.pause_playback()
            self.playing = False
        except SpotifyException as e:
            raise RuntimeError(f"Spotify pause fehlgeschlagen: {e}")

    def play(self):
        """
        Setzt die aktuelle Wiedergabe fort.
        """
        try:
            self.sp.start_playback()
            self.playing = True
        except SpotifyException as e:
            raise RuntimeError(f"Spotify play fehlgeschlagen: {e}")
