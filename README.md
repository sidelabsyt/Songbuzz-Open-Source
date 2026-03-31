# 🎵 SongBuzz

> A self-hosted, hardware-powered music quiz game. Spotify songs stream to your speakers, players smash physical buzzers, and a live scoreboard runs on any screen in the room.

---

## How It Works

A FastAPI server runs on any machine in your local network and streams music via the Spotify API. Each player holds a custom-built ESP32 buzzer unit. When a song plays, the first one to hit the big button locks in their buzz — the judge confirms right or wrong, points get awarded, and the chaos continues.

The game host controls everything from a browser: playlist management, lobby, playback, and scoring. Players join from their phone by scanning the QR code or navigating to the server IP.

---

## Project Structure

```
SongBuzz/
├── main.py                        # FastAPI entry point
├── requirements.txt
├── backend/
│   ├── game_manager.py            # Core game state machine + WebSocket logic
│   ├── buzzer_manager.py          # Buzzer registration + UDP discovery
│   ├── spotify_playlist.py        # Smart song queue with balanced playlist distribution
│   ├── SpotifyPlayer.py           # Spotify playback control via Spotipy
│   └── credintals_template.py     # → copy to credintals.py and fill in your keys
├── frontend/
│   ├── index.html
│   ├── app.js                     # Vue 3 app, routing, WebSocket client
│   └── components/
│       ├── HomeScreen.js          # Host dashboard
│       ├── LobbyScreen.js         # Player list + playlist pool manager
│       ├── PlaybackScreen.js      # Live playback + buzz timer
│       ├── JudgeScreen.js         # Judge view (correct / wrong buttons)
│       ├── GameScreen.js          # Player view during game
│       ├── SongRevealScreen.js    # Song reveal after round
│       ├── WinScreen.js           # End screen with winner
│       └── JoinScreen.js          # Player join form (phone-facing)
├── assets/
│   ├── playlists/playlists.json   # Persisted playlist pool
│   ├── uploads/                   # Player avatar images
│   └── winsounds/                 # MP3s played on round win
└── Hardware/
    ├── Pinout                     # Pin reference file
    ├── SongBuzz/SongBuzz.ino      # Arduino firmware for the buzzer units
    └── 3D_Files/                  # Printable enclosure parts (.stl / .3mf)
```

---

## Software Setup

### Requirements

- Python 3.11+
- A Spotify Premium account
- A Spotify Developer App (for API credentials)

### Installation

```bash
# Clone the repo
git clone https://github.com/yourname/SongBuzz.git
cd SongBuzz

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Spotify Credentials

Copy the credentials template and fill in your app details:

```bash
cp backend/credintals_template.py backend/credintals.py
```

Then open `backend/credintals.py` and replace `client_id` and `client_secret` with your values from the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard). Make sure the redirect URI `http://127.0.0.1:8888/callback` is registered in your app settings.

### Start the Server

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Then open `http://localhost:8000` in a browser on the host machine. Players connect via `http://<your-local-ip>:8000/join` from their phones.

---

## Hardware — The Buzzer Units

Each buzzer is a self-contained ESP32-based device with a display, RGB LEDs, and three buttons. It connects automatically to the game server over WiFi via UDP broadcast discovery — no manual IP configuration needed.

### Components

| Component | Details |
|---|---|
| Microcontroller | ESP32 (any dev board with sufficient GPIO) |
| Display | SSD1306 128×64 OLED (I2C) |
| LEDs | NeoPixel strip, 8 LEDs |
| Buttons | 3× momentary pushbutton (LEFT, BIG, RIGHT) |

### Pin Assignment

```
GPIO 2   →  BIG button (the main buzz button)
GPIO 5   →  LEFT button
GPIO 6   →  RIGHT button
GPIO 3   →  NeoPixel data line (8 LEDs)
GPIO 8   →  I2C SCL  (OLED display)
GPIO 9   →  I2C SDA  (OLED display)

OLED I2C address: 0x3C
OLED resolution:  128 × 64 px
```

All buttons are wired between the GPIO pin and GND, using internal `INPUT_PULLUP`. No external resistors needed.

### Wiring Diagram (simplified)

```
ESP32                  OLED SSD1306
GPIO 8 (SCL) ───────── SCL
GPIO 9 (SDA) ───────── SDA
3.3V         ───────── VCC
GND          ───────── GND

ESP32                  NeoPixel Strip
GPIO 3       ───────── DIN
5V           ───────── VCC
GND          ───────── GND

ESP32                  Buttons (×3)
GPIO 2  ── [BIG BTN] ── GND
GPIO 5  ── [LEFT BTN] ─ GND
GPIO 6  ── [RIGHT BTN]─ GND
```

### Required Arduino Libraries

Install these via the Arduino Library Manager:

- `WebSockets` by Markus Sattler
- `ArduinoJson` by Benoit Blanchon
- `Adafruit GFX Library`
- `Adafruit SSD1306`
- `Adafruit NeoPixel`

### Links
Original buzzer design (used as a starting point):
https://www.thingiverse.com/thing:675...

Parts used (*Affiliate Links – I earn a small commission if you buy through these links):

*PLA Translucent: https://amzn.to/4lZ9CcU

*OLED Display: https://amzn.to/484HW0s

*ESP32 C3 Super Mini: https://amzn.to/48lJ9R8

*LED Ring: https://amzn.to/4cfy5Ye

### Firmware Configuration

Open `Hardware/SongBuzz/SongBuzz.ino` and set your WiFi credentials:

```cpp
const char* WIFI_SSID     = "YourNetwork";
const char* WIFI_PASSWORD = "YourPassword";
```

Flash to the ESP32 via Arduino IDE (board: `ESP32 Dev Module`). The buzzer will automatically find the server on the local network — no IP address needed.

### Auto-Discovery Protocol

On startup the server broadcasts `SONGBUZZ_SERVER` packets via UDP to port `8888` every 3 seconds. When a buzzer receives this packet, it connects to the server via WebSocket at `ws://<server-ip>:8000/ws/buzzer/<MAC>`. The MAC address serves as the unique buzzer identifier.

### What the Display Shows

The OLED gives the player feedback throughout the game — connecting status, their assigned name, whether they successfully buzzed, and whether their answer was correct or wrong. The server can push arbitrary text and control the NeoPixels (color, brightness) via WebSocket commands.

### 3D Printed Enclosure

The `Hardware/3D_Files/` folder contains all printable parts:

| File | Description |
|---|---|
| `Base.stl` | Main enclosure body |
| `Cover.stl` | Top cover |
| `CoverLid.stl` | Lid for cable access |
| `Button_Translucent.3mf` | Big buzz button (print in translucent PETG for LED glow) |
| `Keycaps.3mf` | LEFT / RIGHT button caps |
| `Slider_Translucent.3mf` | Decorative LED diffuser slider |
| `Spring_PETG.stl` | Button return spring |
| `Stecken.3mf` | Internal mounting pegs |

---

## Gameplay

1. Start the server and open the host dashboard in a browser
2. Add Spotify playlists to the pool via the Lobby screen (paste URL or URI, optionally give it a custom name)
3. Players join from their phones and pick up their buzzer units
4. The host starts the game — a random song from the pool begins playing on the active Spotify device
5. Players buzz by hitting the big button; the first buzz locks everyone else out
6. The judge (via the Judge view) confirms correct or wrong — wrong answers eliminate the player for that round
7. Points are awarded and the next round begins
8. At the end, the Win Screen shows the final standings with a celebration sound

---

## Song Queue System

SongBuzz uses a pre-planned queue rather than picking songs randomly on the fly. Before each round, the queue is built by:

1. Grouping all available tracks by source playlist
2. Separating tracks into "fresh" (not yet played this evening) and "already played" per playlist
3. Shuffling each group independently (fresh tracks always come first)
4. Interleaving all playlists in round-robin order, shuffling each group of one-per-playlist

This ensures balanced representation across all playlists while keeping the order unpredictable. Songs played earlier in the evening automatically sink to the back of the queue even across multiple rounds, so repetition is minimized without being completely eliminated.

---

## Virtual Buzzers (Development)

For testing without hardware, `virtual_buzzers.py` simulates buzzer connections via the terminal. Run it separately alongside the server.

---

## License

© 2025 Elias Köhle. This project is licensed under [Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/).

**You are free to:** share, copy, modify, and build upon this project — as long as you give appropriate credit and **do not use it for commercial purposes**.
