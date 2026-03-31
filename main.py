from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import uuid
import shutil
from typing import List, Dict
import asyncio
from backend.buzzer_manager import *
from contextlib import asynccontextmanager
import json
import os

from backend.game_manager import *
import socket
import psutil

app = FastAPI()

buzzer_manager = BuzzerManager()
game_manager = GameManager(buzzer_manager)

# Use absolute paths so static serving works regardless of cwd
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
ASSETS_DIR = BASE_DIR / "assets"
FRONTEND_INDEX = FRONTEND_DIR / "index.html"

UPLOAD_DIR = ASSETS_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SOUNDS_DIR = ASSETS_DIR / "winsounds"
@app.get("/api/sounds")
async def get_sounds():
    """Gibt die Liste der MP3-Dateien an das Frontend zurück"""
    try:
        if not SOUNDS_DIR.exists():
            return []
        sounds = [f for f in os.listdir(str(SOUNDS_DIR)) if f.endswith('.mp3')]
        return sorted(sounds)
    except Exception as e:
        print(f"Fehler beim Lesen des Verzeichnisses: {e}")
        return []

# Statische Mounts (Spezifisch vor Allgemein)
app.mount("/winsounds", StaticFiles(directory=str(SOUNDS_DIR)), name="winsounds")
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

async def udp_announcer():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        for snic in [s for i in psutil.net_if_addrs().values() for s in i if s.family == socket.AF_INET]:
            try: 
                if not snic.address.startswith("127."):
                    addr = f"{'.'.join(snic.address.split('.')[:-1])}.255"
                    sock.sendto(b"SONGBUZZ_SERVER", (addr, 8888))
            except: pass
        await asyncio.sleep(3)


# WebSocket endpoint for game updates
@app.websocket("/ws")
async def ws_root(websocket: WebSocket):
    await websocket.accept()
    game_connection = game_manager.register_connection(websocket)
    try:
        # Send initial state
        await game_manager.broadcast_state()
        await game_connection.poll_websocket_until_error()
    except WebSocketDisconnect:
        pass
    finally:
        game_manager.unregister_connection(game_connection)
			

@app.post("/api/join")
async def join(
            name: str = Form(...), 
            avatar: UploadFile = File(...),
            buzzer_id: int = Form(1),    # NEU: Standardwert 1, falls nicht gesendet
            color: str = Form("#6366F1"), # NEU: Standardfarbe
            sound: str = Form("")):
    if not name.strip():
        raise HTTPException(status_code=400, detail="Name is required")
    if not avatar.content_type or not avatar.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Avatar must be an image")

    ext = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif"
    }.get(avatar.content_type, ".jpg")

    player_id = str(uuid.uuid4())
    filename = f"{player_id}{ext}"
    dest = UPLOAD_DIR / filename

    with dest.open("wb") as out_file:
        shutil.copyfileobj(avatar.file, out_file)

    # Update in-memory players and broadcast lobby update
    
    try:
        player = await game_manager.register_player({
            "id": player_id,
            "name": name.strip(),
            "avatar_url": f"/assets/uploads/{filename}",
            "buzzer_id": buzzer_id,
            "color": color,
            "sound": sound
        })

        return JSONResponse({
            "ok": True,
            "id": player.id,
            "name": player.name,
            "avatar_url": player.avatar_url
        })
    except Exception as e:
         raise HTTPException(status_code=500, detail=f'Interner Fehler: {e}')

@app.get("/join")
async def join_page():
	if FRONTEND_INDEX.exists():
		return FileResponse(FRONTEND_INDEX)
	raise HTTPException(status_code=404, detail="Frontend index not found")


@app.get("/")
async def root_page():
	if FRONTEND_INDEX.exists():
		return FileResponse(FRONTEND_INDEX)
	raise HTTPException(status_code=404, detail="Frontend index not found")

# Start mit: uvicorn main:app --reload
#python -m uvicorn main:app --reload
#python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload


@app.on_event("startup")
async def startup_event():
    # Startet BEIDE Discovery-Tasks
    game_manager.set_state(GameState.UDP_BROADCAST_SETUP)
    asyncio.create_task(udp_announcer())
    asyncio.create_task(buzzer_manager.start_udp_discovery())

@app.websocket("/ws/buzzer/{mac}")
async def websocket_endpoint(websocket: WebSocket, mac: str):
    await game_manager.register_buzzer(mac, websocket)

# Frontend statisch unter /frontend bereitstellen; Root liefert index.html
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Muss nicht existieren, triggert nur die Interface-Wahl
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip