import tkinter as tk
import asyncio
import threading
import json
import websockets

# Definition der Button-Typen
class BuzzerButton():
    BIG = 'BIG'
    LEFT = 'LEFT'
    RIGHT = 'RIGHT'

class VirtualBuzzer:
    def __init__(self, root, index, mac):
        self.mac = mac
        self.index = index
        self.websocket = None
        self.loop = None
        
        # Frame für einen einzelnen Buzzer
        self.frame = tk.Frame(root, bg='#2d2d2d', padx=15, pady=15, highlightbackground="#444", highlightthickness=2)
        self.frame.grid(row=0, column=index-1, padx=10, pady=20)

        # 1. Virtuelles OLED Display (schwarz mit grüner Schrift)
        self.display_lines = ["", "", "", ""]
        self.display_var = tk.StringVar(value=f"Buzzer {index}\nVerbunden")
        self.display_label = tk.Label(
            self.frame, textvariable=self.display_var, bg="black", fg="#00FF00", 
            font=("Courier", 10, "bold"), width=18, height=4, justify="left", anchor="nw", padx=5, pady=5
        )
        self.display_label.pack(pady=5)

        # 2. Der Große Buzzer (BIG Button)
        self.main_button = tk.Button(
            self.frame, text="⭕", bg="#555555", fg="white", 
            font=("Arial", 30), width=3, height=1,
            command=lambda: self.trigger_buzz(BuzzerButton.BIG)
        )
        self.main_button.pack(pady=10)

        # 3. Die zwei kleinen Buttons (LEFT, RIGHT)
        btn_frame = tk.Frame(self.frame, bg='#2d2d2d')
        btn_frame.pack(fill="x", pady=5)

        self.btn_left = tk.Button(btn_frame, text="◀", bg="#333333", fg="white", width=4, 
                                 command=lambda: self.trigger_buzz(BuzzerButton.LEFT))
        self.btn_right = tk.Button(btn_frame, text="▶", bg="#333333", fg="white", width=4, 
                                  command=lambda: self.trigger_buzz(BuzzerButton.RIGHT))

        self.btn_left.pack(side="left", expand=True, padx=2)
        self.btn_right.pack(side="left", expand=True, padx=2)

        # MAC Label
        tk.Label(self.frame, text=mac, bg='#2d2d2d', fg='#888', font=("Arial", 7)).pack()

        # Netzwerk-Thread starten
        threading.Thread(target=self.start_async_loop, daemon=True).start()

    def start_async_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect())

    async def connect(self):
        uri = f"ws://localhost:8000/ws/buzzer/{self.mac}"
        while True:
            try:
                async with websockets.connect(uri) as ws:
                    self.websocket = ws
                    self.update_ui_display("Verbunden...", 0)
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        self.handle_command(data)
            except Exception:
                self.update_ui_display("Suche Server...", 0)
                await asyncio.sleep(2)

    def handle_command(self, data):
        cmd = data.get("cmd")
        if cmd == "setled":
            color = data.get("color", "#555555")
            self.main_button.after(0, lambda: self.main_button.config(bg=color))
        
        elif cmd == "write":
            text = data.get("txt", "")
            line = data.get("line", 0)
            if data.get("clear"):
                self.display_lines = ["", "", "", ""]
            
            if 0 <= line < 4:
                self.display_lines[line] = text
                full_text = "\n".join(self.display_lines)
                self.main_button.after(0, lambda: self.display_var.set(full_text))

    def update_ui_display(self, text, line):
        self.display_lines[line] = text
        full_text = "\n".join(self.display_lines)
        self.main_button.after(0, lambda: self.display_var.set(full_text))

    def trigger_buzz(self, btn_type):
        if self.websocket and self.loop:
            # FIX: Sende das Format {"type":"BTN", "val":"..."} damit der KeyError behoben ist
            msg = json.dumps({"type": "BTN", "val": btn_type})
            asyncio.run_coroutine_threadsafe(self.websocket.send(msg), self.loop)

# GUI Setup
root = tk.Tk()
root.title("SongBuzz Hardware Simulator")
root.configure(bg='#1a1a1a')

# Erzeuge 4 Buzzer mit fiktiven MACs
buzzers = []
for i in range(1, 5):
    m = f"00:00:00:00:00:0{i}"
    buzzers.append(VirtualBuzzer(root, i, m))

root.mainloop()