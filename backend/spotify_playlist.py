import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from backend.credintals import Credintals


class SpotifyPlaylistManager:

    def __init__(self, playlists: list[str], evening_played_ids: set = None):
        self.playlists = playlists
        self.sp = spotipy.Spotify(auth_manager=Credintals.OAuth)
        self._cached_tracks = []
        self.played_ids = set()          # reset jede Runde
        self.session_played_ids = evening_played_ids if evening_played_ids is not None else set()
        self._queue = []                 # vorausberechnete Song-Warteschlange
        self.current_track = None

    # ------------------------------------------------------------------
    # Öffentliche API
    # ------------------------------------------------------------------

    def getrandomsong(self) -> dict:
        if not self._queue:
            self._build_queue()

        if not self._queue:
            raise RuntimeError("Keine gültigen Tracks in den angegebenen Playlists gefunden.")

        track = self._queue.pop(0)
        self.played_ids.add(track['uri'])
        self.session_played_ids.add(track['uri'])

        return {
            "track_id": track["uri"],
            "title": track["name"],
            "artist": ", ".join(a["name"] for a in track["artists"]),
            "artwork_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
            "playlist": {
                "uri": track["_origin_playlist"]["uri"],
                "name": track["_origin_playlist"]["name"]
            }
        }

    # ------------------------------------------------------------------
    # Queue-Aufbau
    # ------------------------------------------------------------------

    def _build_queue(self):
        """
        Baut eine ausgeglichene, shuffled Warteschlange auf.

        Algorithmus:
        1. Tracks nach Playlist gruppieren.
        2. Pro Playlist: frische Songs (nicht in session_played_ids) zuerst,
           bereits gespielter Songs danach – jeweils intern gemischt.
        3. Round-Robin über alle Playlists: je eine Gruppe aus N Songs
           (einer pro Playlist) wird zufällig durchgemischt und angehängt.
           → Keine Playlist dominiert, aber die Reihenfolge ist trotzdem
             nicht vorhersagbar.
        """
        if not self._cached_tracks:
            self._refresh_track_pool()

        # Tracks nach Playlist-URI gruppieren
        tracks_by_playlist: dict[str, list] = {}
        for t in self._cached_tracks:
            pl_uri = t['_origin_playlist']['uri']
            tracks_by_playlist.setdefault(pl_uri, []).append(t)

        if not tracks_by_playlist:
            return

        # Pro Playlist: frisch zuerst, alt danach – beide Gruppen intern shuffeln
        playlist_pools: dict[str, list] = {}
        for uri, tracks in tracks_by_playlist.items():
            fresh = [t for t in tracks if t['uri'] not in self.session_played_ids]
            old   = [t for t in tracks if t['uri'] in self.session_played_ids]
            random.shuffle(fresh)
            random.shuffle(old)
            playlist_pools[uri] = fresh + old

        playlist_uris = list(playlist_pools.keys())
        max_len = max(len(q) for q in playlist_pools.values())

        queue = []
        for i in range(max_len):
            # Gruppe: ein Song aus jeder Playlist (falls noch vorhanden)
            group = [
                playlist_pools[uri][i]
                for uri in playlist_uris
                if i < len(playlist_pools[uri])
            ]
            # Gruppe mischen → Playlist-Reihenfolge unvorhersagbar
            random.shuffle(group)
            queue.extend(group)

        self._queue = queue
        print(f"[QUEUE] Rebuilt queue: {len(self._queue)} tracks "
              f"from {len(playlist_uris)} playlist(s)")

    # ------------------------------------------------------------------
    # Track-Pool laden
    # ------------------------------------------------------------------

    def _refresh_track_pool(self):
        """Lädt alle Tracks aus allen Playlists einmalig in den Cache."""
        all_tracks = []
        for uri in self.playlists:
            try:
                playlist_info = self.sp.playlist(uri, fields="name,uri")
                tracks = self._get_all_tracks(uri)
                for t in tracks:
                    t['_origin_playlist'] = playlist_info
                    all_tracks.append(t)
            except SpotifyException as e:
                print(f"Warnung: Playlist {uri} konnte nicht geladen werden: {e}")

        # Nur Tracks behalten, die im Markt verfügbar sind
        self._cached_tracks = [t for t in all_tracks if 'AT' in t.get('available_markets', [])]
        print(f"[POOL] Loaded {len(self._cached_tracks)} tracks total")

    def _get_all_tracks(self, playlist_uri: str) -> list[dict]:
        """Lädt alle Tracks einer Playlist (inkl. Paging). Lokale Tracks werden ausgeschlossen."""
        results = self.sp.playlist_items(
            playlist_uri,
            additional_types=["track"],
            limit=100
        )

        tracks = []
        while results:
            for item in results["items"]:
                track = item.get("track")
                if track and not track.get("is_local"):
                    tracks.append(track)
            results = self.sp.next(results) if results["next"] else None

        return tracks
