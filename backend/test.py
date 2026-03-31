import socket
import asyncio
import json
import psutil
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# Deine Spotify-Klassen
from spotify_playlist import SpotifyPlaylistManager
from SpotifyPlayer import SpotifyPlayer

app = FastAPI()

# --- Setup Spotify ---
playlists = [
    "spotify:playlist:5X9rtYxwwCOTpgQprZnZT4",
    "spotify:playlist:6kV9srvKjxWhsGobF9Csb3"
]

sp_player = SpotifyPlayer()
sp_manager = SpotifyPlaylistManager(playlists)

# --- Hilfsfunktion für Song-Start & Display ---
async def play_next_random_song(websocket: WebSocket):
    """Holt einen Song, startet ihn und schreibt Infos aufs Display"""
    song = sp_manager.getrandomsong()
    title = song["title"]
    artist = song["artist"]
    
    # Anzeige auf dem Buzzer-Display
    # Zeile 0: Titel, Zeile 1: Interpret
    await websocket.send_json({"cmd": "write", "line": 0, "txt": title[:20], "clear": True})
    await websocket.send_json({"cmd": "write", "line": 1, "txt": f"von {artist[:16]}", "clear": False})
    await websocket.send_json({"cmd": "write", "line": 3, "txt": "--- MUSIC ON ---", "clear": False})
    
    # Spotify Playback
    sp_player.startsong(song["track_id"], start_second=40)
    print(f"[*] Spiele: {title} - {artist}")

# --- UDP Announcer (unverändert) ---
async def udp_announcer():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        for snic in [s for i in psutil.net_if_addrs().values() for s in i if s.family == socket.AF_INET]:
            try: 
                addr = f"{'.'.join(snic.address.split('.')[:-1])}.255"
                sock.sendto(b"SONGBUZZ_SERVER", (addr, 8888))
            except: pass
        await asyncio.sleep(3)

# --- WebSocket Logik ---
@app.websocket("/ws/buzzer/{mac}")
async def websocket_endpoint(websocket: WebSocket, mac: str):
    await websocket.accept()
    print(f"[+] {mac} verbunden.")
    
    # Initialer Song-Start beim Verbinden
    try:
        await play_next_random_song(websocket)
    except Exception as e:
        print(f"Fehler beim ersten Song: {e}")

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            btn = msg.get("val")

            if btn == "BIG":
                # Buzzer gedrückt: Musik Pause
                sp_player.pause()
                await websocket.send_json({"cmd": "led", "r": 0, "g": 255, "b": 0})
                await websocket.send_json({"cmd": "write", "line": 3, "txt": "!!! GEBUZZT !!!", "clear": False})

            elif btn == "RIGHT":
                # Nächster Song (Skip-Funktion)
                await play_next_random_song(websocket)
                await websocket.send_json({"cmd": "led", "r": 0, "g": 0, "b": 255})

            elif btn == "LEFT":
                # Musik fortsetzen
                sp_player.play()
                await websocket.send_json({"cmd": "write", "line": 3, "txt": "Weiter gehts...", "clear": False})
                await websocket.send_json({"cmd": "led", "r": 255, "g": 0, "b": 0})

    except WebSocketDisconnect:
        print(f"[-] {mac} getrennt.")
    except Exception as e:
        print(f"Fehler im Loop: {e}")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(udp_announcer())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)