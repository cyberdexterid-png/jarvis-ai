# CYBER AI 🤖 — free Iron Man-style assistant

Your own CYBER AI for the laptop. **100% free — no card needed.**

🎤 **Always-on voice** — say **"CYBER"** + your command (no button!)
🖐️ **Hand gestures** — camera auto-starts, control like Iron Man
🌐 Bilingual English + Sinhala | 🖥️ Full PC control | 🎨 Hacker-style UI

## 🖐️ Gesture controls (camera)

| Gesture | Action |
|---|---|
| ☝️ Point (index finger) | Move mouse cursor |
| 🤏 Pinch (thumb + index) | Left click |
| ✊ Fist | Play / pause |
| ✌️ 2 fingers | Volume up |
| 🤟 3 fingers | Volume down |
| 🖐️ Open palm | Mute |

Camera starts automatically. Disable with `python jarvis.py --no-gesture`.

**Camera not showing?**
1. Use the **latest zip** and run `pip install -r requirements.txt` again
   (camera needs `opencv-python`, `mediapipe`, `pyautogui`)
2. Close other apps using the camera (Zoom, Meet...)
3. In the web UI, **click the 🖐 pill** to retry — hover it to see the exact reason

**Wake word:** say "CYBER" before commands. Don't want that?
Open ⚙ Settings → uncheck *REQUIRE WAKE WORD* — then everything you say is a command.

## 🔑 API key — 3 easy ways (pick one)

1. **`api_key.txt`** (easiest) — open it in Notepad, replace the placeholder
   with your key, save. Done — the app reads it every start.
2. **`start.bat`** — asks for the key on first run and saves it permanently.
3. **Web UI** — click ⚙ Settings, paste the key, SAVE KEY.

Free key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey) (no card).
⚠️ Never upload your real key to GitHub — the repo copy is a placeholder only.

## ⚡ Quick start (2 minutes)

1. Install Python 3.10+ (tick "Add to PATH"), then:
   ```
   pip install -r requirements.txt
   ```
2. Double-click **`start.bat`** — paste your free Gemini key when asked
   (from [aistudio.google.com/apikey](https://aistudio.google.com/apikey), no card).
   It's saved permanently — you type it only once.
3. Click anywhere on the page, allow the mic, say **"CYBER"** + your command.

## 🌐 Go online — control your laptop from anywhere

Your laptop stays the "body" (PC control + camera must run on it), but you can
reach CYBER AI from your phone or any device:

1. Download **cloudflared.exe** (free, no account/card) from
   [cloudflare.com](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
   and put it next to `go-online.bat`
2. Double-click **`go-online.bat`**
3. Copy the `https://....trycloudflare.com` link it prints — open it on your phone!

Mic, voice, chat and PC commands all work through the link (it's HTTPS).

⚠️ **Security:** anyone with the link can command your PC — never share it.
For a private alternative, use [Tailscale](https://tailscale.com) (free VPN)
and open `http://<laptop-tailscale-ip>:8080`.

## 🚀 Make the EXE (release build)

No Python needed for the end user — one file does everything:

1. Open this folder, double-click **`build-exe.bat`**
2. Wait a few minutes → **`dist\CyberAI.exe`** is created
3. Share `CyberAI.exe` — anyone can double-click and use it!

The exe opens the hacker web UI automatically. First run: click ⚙ **Settings** in the UI and paste a free Gemini API key (from aistudio.google.com, no card).

> Note: the exe is built on your PC (Windows builds can't be made on other systems). Build once, share everywhere.

## What it does (v2)

- 🎤 **Bilingual voice** — speaks & understands **English + Sinhala** (auto-detect)
- 🔊 **Sinhala voice replies** — real Sinhala TTS voice
- 🧠 **Answers anything** — full world knowledge via free Gemini AI brain
- 🖥️ **Full PC control**:
  - `volume up / down / mute` — system volume
  - `play / pause / next / previous` — media keys
  - `play <song name>` — plays on YouTube
  - `take a screenshot` — saves to Pictures
  - `close window`, `show desktop`
  - `open notepad / calculator / task manager / downloads...`
  - `battery`, `system info`
  - `lock`, `shutdown`, `restart` (10s warning, say cancel)
  - `stop` — makes Jarvis stop talking
- ⚡ **Commands**: time, date, google search, wikipedia, weather, jokes

Example: *"volume up"*, *"play baila songs"*, *"take a screenshot"*, *"අද දවස මොකද්ද"* (Sinhala works!)

## Run from source (developers)

**1. Install Python**
- Download from python.org (3.10 or newer)
- ✅ Tick **"Add python.exe to PATH"** during install

**2. Install Jarvis**
```
pip install -r requirements.txt
```

**3. API key — two easy ways**
- **Easiest:** run Jarvis, click ⚙ **Settings** in the web UI, paste the free key (from aistudio.google.com — no card). Saved on your PC only.
- Or terminal (one time): `setx GEMINI_API_KEY "your-key"` then reopen the terminal.

**4. Run it** 🚀
- Double-click **`start.bat`** → beautiful web UI opens in your browser 🌐
- Or in VS Code terminal: `python jarvis.py`
- (Old style terminal: `python jarvis.py --terminal`)
- Allow mic access when the browser asks

## Tips

- Speak English commands for best mic accuracy. You can ask questions in Sinhala too — the brain understands, but the voice replies in English (offline voices).
- Say **"exit"** to quit.
- Jarvis keeps listening in a loop — no wake word needed in v1.

## Files

| File | What |
|---|---|
| `jarvis.py` | everything — voice, brain, commands, HUD |
| `start.bat` | double-click launcher (HUD mode) |
| `requirements.txt` | Python packages |

---
Made free, for fun. No accounts, no subscriptions, no card. 🔓
