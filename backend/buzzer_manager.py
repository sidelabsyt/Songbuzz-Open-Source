import asyncio
import socket
import json
import psutil
from fastapi import WebSocket, WebSocketDisconnect
from collections.abc import Awaitable, Callable
from enum import Enum

"""
BUZZER STATES

Default reset: -> PG1

PreGame:
[PG1] connected & unassigned to player                  -> PG2
[PG2] connected & assigned to player    (not ready)     -> PG3
[PG3] connected & assigned to player    (ready)         -> IGP1

InGame:
[IGP1] RandomJudgeAssign        -> IGP2, IGJ1   
[IGP2] Player & not buzzed      -> IGP3           
[IGP3] Player & buzzed          -> IGP4, IGP5
[IGP4] Player & eliminated      -> IGP1
[IGP5] Player & won             -> IGP1

[IGJ1] Judge & wait for start   -> IGJ2
[IGJ2] Judge & music playing    -> IGJ3
[IGJ3] Judge & buzzed (decision OK/FAIL) -> IGJ2, IGP1

"""

class BuzzerState(Enum):
    UNDEFINED = -1
    PreGameConnectedUnassigned = "PreGameConnectedUnassigned"
    PreGameConnectedAssignedNotReady = "PreGameConnectedAssignedNotReady"
    PreGameConnectedAssignedReady = "PreGameConnectedAssignedReady"
    InGameRandomJudgeAssign = "InGameRandomJudgeAssign"
    InGamePlayerMusicPlaying = "InGamePlayerMusicPlaying"
    InGamePlayerNotBuzzed = "InGamePlayerNotBuzzed"
    InGamePlayerBuzzed = "InGamePlayerBuzzed"
    InGamePlayerEliminated = "InGamePlayerEliminated"
    InGamePlayerWon = "InGamePlayerWon"
    InGameAfterSong = "InGameAfterSong"
    InGameJudgeMusicPlaying = "InGameJudgeMusicPlaying"
    InGameJudgeBuzzedDecision = "InGameJudgeBuzzedDecision"
    PostGame = "PostGame"

class BuzzerButton():
    BIG = 'BIG'
    LEFT = 'LEFT'
    RIGHT = 'RIGHT'

class Buzzer:
    websocket: WebSocket
    mac: str
    on_message_listeners: list = []
    disconnect_callback: Callable
    _buzzer_state: BuzzerState = BuzzerState.UNDEFINED

    id: int = -1

    def __init__(self, websocket: WebSocket, mac: str, disconnect_callback: Callable, id: int):
        self.websocket = websocket
        self.mac = mac
        self.disconnect_callback = disconnect_callback
        self.on_message_listeners = []
        self.id = id
        print(f'[Buzzer] ctor - {self.mac} - id={self.id}')
        
    def toDict(self):
        return {
            'mac': self.mac,
            'id': self.id,
        }

    def register_on_message_callback(self, on_message_callback: Callable):
        self.on_message_listeners.append(on_message_callback)

    def set_state(self, state: BuzzerState):
        print(f'buzzer STATE_TRANSITION {self.mac}: {self._buzzer_state} -> {state}')
        self._buzzer_state = state

    def get_state(self):
        return self._buzzer_state

    async def poll_websocket_until_error(self):
        try:
            while True:
                # Empfange Button-Daten
                data = await self.websocket.receive_text()
                msg = json.loads(data)
                for cb in self.on_message_listeners:
                    cb(self, msg)
                
        except WebSocketDisconnect as e:
            # Manager bereinigt sich selbst in send_to_buzzer, 
            # aber wir printen es hier zur Info
            print(f'exception: {e}')
            if self.disconnect_callback is not None:
                self.disconnect_callback(self)

class BuzzerManager:
    active_buzzers: list[Buzzer] = []

    def __init__(self):
        self.active_buzzers = [] # mac -> websocket
        self.udp_port = 8888

    def buzzer_for_id(self, id: int) -> Buzzer:
        ret = [b for b in self.active_buzzers if b.id == id]
        if len(ret) < 1:
            raise ValueError(f'No such buzzer with id={id}')
        return ret[0]

    async def start_udp_discovery(self):
        """Sendet Broadcasts auf absolut jedem verfügbaren Interface."""
        print(f"UDP Discovery gestartet auf Port {self.udp_port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        message = b"SONGBUZZ_SERVER"
        
        while True:
            try:
                # Wir sammeln alle möglichen Broadcast-Adressen
                addresses = ["255.255.255.255"]
                for interface, snics in psutil.net_if_addrs().items():
                    for snic in snics:
                        if snic.family == socket.AF_INET:
                            # Erstelle Broadcast-IP für dieses Interface (z.B. 192.168.0.255)
                            parts = snic.address.split('.')
                            if len(parts) == 4:
                                broadcast = f"{parts[0]}.{parts[1]}.{parts[2]}.255"
                                addresses.append(broadcast)
                
                # Sende an alle gefundenen Adressen
                for addr in set(addresses):
                    try:
                        sock.sendto(message, (addr, self.udp_port))
                    except:
                        pass
                
                await asyncio.sleep(2) # Alle 2 Sek senden für schnellen Connect
            except Exception as e:
                print(f"UDP Error: {e}")
                await asyncio.sleep(5)

    def _next_free_buzzer_id(self) -> int:
        i = 1
        for i in range(1, 10):
            if len([b for b in self.active_buzzers if b.id == i]) == 0:
                break
        return i

    async def register_buzzer(self, mac: str, websocket: WebSocket):
        """Handshake und Registrierung."""
        await websocket.accept()
        # check if we already have an active buzzer with this mac, filter it and replace!
        ret = [b for b in self.active_buzzers if b.mac == mac]
        if len(ret) > 0:
            self.unregister_buzzer(ret[0])
        buzzer = Buzzer(websocket, mac, self.unregister_buzzer, self._next_free_buzzer_id())
        buzzer.set_state(BuzzerState.PreGameConnectedUnassigned)
        self.active_buzzers.append(buzzer)
        print(f"[+] Hardware verbunden: {mac}")
        
        # Sofort-Feedback an Hardware
        await self.writetext(mac, 0, "SongBuzz ONLINE", clear=True)
        await self.setled(mac, "#00FF00")
        return buzzer

    def unregister_buzzer(self, buzzer: Buzzer):
        """Connection close / error"""
        try:
            self.active_buzzers.remove(buzzer)
        except:
            pass
        print(f"Buzzer {buzzer.mac} getrennt.")

    def get_by_states(self, states: list[BuzzerState]) -> list[Buzzer]:
        return [b for b in self.active_buzzers if b.get_state() in states]

    async def writetext(self, mac, zeile, text, clear=False, mode="", size=0):
        replacements = {
            'ä': 'ae', 'ö': 'oe', 'ü': 'ue',
            'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue',
            'ß': 'ss'
        }
        clean_text = str(text)
        for char, rep in replacements.items():
            clean_text = clean_text.replace(char, rep)
        # -----------------------------

        await self.send_to_buzzer(mac, {
            "cmd": "write", 
            "line": zeile, 
            "txt": clean_text,
            "clear": clear, 
            "mode": mode, 
            "size": size
        })

    async def setled(self, mac, color_hex):
        h = color_hex.lstrip('#')
        r, g, b = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        await self.send_to_buzzer(mac, {"cmd": "led", "r": r, "g": g, "b": b})

    async def send_to_buzzer(self, mac, data):
        ret = [b for b in self.active_buzzers if b.mac == mac]
        if len(ret) > 0:
            buzzer = ret[0]
            try:
                await buzzer.websocket.send_json(data)
            except:
                del buzzer

