# J.A.R.V.I.S. — free DIY voice assistant 🤖

Your own Jarvis for the laptop. **100% free — no card needed.**

## 🚀 Make the EXE (release build)

No Python needed for the end user — one file does everything:

1. Open this folder, double-click **`build-exe.bat`**
2. Wait a few minutes → **`dist\JARVIS.exe`** is created
3. Share `JARVIS.exe` — anyone can double-click and use it!

The exe opens the beautiful web UI automatically. First run: click ⚙ **Settings** in the UI and paste a free Gemini API key (from aistudio.google.com, no card).

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
