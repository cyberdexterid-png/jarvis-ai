#!/usr/bin/env python3
"""
CYBER AI - free DIY voice + gesture assistant for Windows.
100% free, no card needed.

FREE stack:
  Voice in  -> SpeechRecognition, bilingual English + Sinhala (si-LK) auto-detect
               Web UI: always-on mic with wake word "CYBER"
  Voice out -> pyttsx3 offline (English) + gTTS (Sinhala voice), auto-picked
  Hands in  -> MediaPipe hand tracking, auto-started (Iron Man style)
  Brain     -> Google Gemini free tier (free key from aistudio.google.com)
               Works offline with built-in answers if no key is set.

Run:  python jarvis.py               (CYBER AI web HUD - DEFAULT, camera auto-on)
      python jarvis.py --no-gesture  (web HUD without camera)
      python jarvis.py --terminal    (terminal mode, no pretty UI)
      python jarvis.py --hud         (desktop cyber HUD window)
      python gesture.py              (hand tracking only)
"""

import datetime
import json
import os
import platform
import re
import sys
import urllib.parse
import urllib.request
import webbrowser

# ---------------------------------------------------------------- optional deps
try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    from google import genai as genai_client
    from google.genai import types as genai_types
except ImportError:
    genai_client = None
    genai_types = None

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    from playsound import playsound
except ImportError:
    playsound = None

# ------------------------------------------------------------------- settings
ASSISTANT_NAME = "CYBER AI"
VERSION = "6.0.0"
GEMINI_MODEL = "gemini-2.0-flash"   # fast + free tier friendly
SILENT = os.environ.get("JARVIS_SILENT") == "1"   # for testing: no audio
WEB_MODE = False                    # True when serving the web HUD
_web_replies = []
_web_lock = None                    # threading.Lock, created in run_web


def resource_path(name):
    """File path that works both as script and as PyInstaller exe."""
    base = getattr(sys, "_MEIPASS",
                   os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def _config_dir():
    """Writable dir for settings (APPDATA on Windows, script dir else)."""
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            d = os.path.join(appdata, "JARVIS")
            os.makedirs(d, exist_ok=True)
            return d
    return os.path.dirname(os.path.abspath(__file__))


def _config_path():
    return os.path.join(_config_dir(), "jarvis_config.json")


def load_config():
    try:
        with open(_config_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    """Save config. Returns (ok: bool, error: str)."""
    try:
        with open(_config_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        return True, ""
    except Exception as e:
        return False, str(e)


def get_api_key():
    """Priority: env var -> api_key.txt -> key saved via web UI."""
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key
    try:
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            file_key = f.read().strip()
        if file_key and file_key != KEY_PLACEHOLDER and " " not in file_key:
            return file_key
    except Exception:
        pass
    return load_config().get("gemini_api_key", "").strip()


def _app_base():
    """Folder next to the script (or exe) — where api_key.txt lives."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


KEY_FILE = os.path.join(_app_base(), "api_key.txt")
KEY_PLACEHOLDER = "PASTE_YOUR_FREE_GEMINI_KEY_HERE"


def ensure_key_file():
    """Create api_key.txt with a placeholder so the user knows where to paste."""
    try:
        if not os.path.exists(KEY_FILE):
            with open(KEY_FILE, "w", encoding="utf-8") as f:
                f.write(KEY_PLACEHOLDER + "\n")
    except Exception:
        pass


def brain_connected():
    return bool(get_api_key()) and genai_client is not None

_engine = None
_recognizer = None
_chat = None

SYSTEM_PROMPT = (
    "You are CYBER AI, a witty and loyal AI assistant like Iron Man's JARVIS. "
    "You are fluent in both English and Sinhala - ALWAYS reply in the same "
    "language the user used. Keep replies short and conversational (1-3 "
    "sentences) unless the user asks for detail. Be helpful, a little "
    "playful, never robotic. You know everything - answer any question "
    "about the world accurately."
)

# ------------------------------------------------------------------ language
def contains_sinhala(text):
    """True if text has any Sinhala unicode characters."""
    return any("\u0d80" <= c <= "\u0dff" for c in text)


def clean_heard(text):
    """Collapse accidental mic duplications: 'open youtube open youtube'."""
    t = text.strip()
    prev = None
    while prev != t:  # repeat until stable (handles triple repeats)
        prev = t
        t = re.sub(r"(?i)\b([\w\s]{2,}?)\s+\1\b", r"\1", t)
    t = re.sub(r"(?i)\b(\w+)(\s+\1\b)+", r"\1", t)  # 'open open youtube'
    return t.strip()


# ------------------------------------------------------------------ voice out
def _get_engine():
    global _engine
    if _engine is None and pyttsx3 is not None and not SILENT:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", 175)
        try:  # prefer a male English voice if one exists
            for v in _engine.getProperty("voices"):
                if "david" in v.name.lower() or "male" in v.name.lower():
                    _engine.setProperty("voice", v.id)
                    break
        except Exception:
            pass
    return _engine


def _speak_english(text):
    engine = _get_engine()
    if engine is None:
        return False
    try:
        engine.say(text)
        engine.runAndWait()
        return True
    except Exception as e:
        print(f"[voice error: {e}]")
        return False


def _speak_sinhala(text):
    """Sinhala voice via free gTTS. Returns False if unavailable."""
    if gTTS is None or playsound is None:
        return False
    try:
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp.close()
        gTTS(text=text, lang="si").save(tmp.name)
        playsound(tmp.name)
        os.unlink(tmp.name)
        return True
    except Exception as e:
        print(f"[sinhala voice unavailable: {e}]")
        return False


def speak(text):
    """Say text out loud (and always print it). Auto-picks English/Sinhala."""
    print(f"{ASSISTANT_NAME}: {text}")
    hud_log(f"{ASSISTANT_NAME}: {text}")
    if WEB_MODE:
        # browser does the speaking; just capture replies for the API
        with _web_lock:
            _web_replies.append(text)
        return
    if SILENT:
        return
    if contains_sinhala(text):
        if _speak_sinhala(text):
            return
        print("[sinhala voice missing: pip install gTTS playsound==1.2.2]")
    _speak_english(text)


def stop_speaking():
    engine = _get_engine()
    if engine is not None:
        try:
            engine.stop()
        except Exception:
            pass


# ------------------------------------------------------------------- voice in
def _get_recognizer():
    global _recognizer
    if _recognizer is None and sr is not None:
        _recognizer = sr.Recognizer()
        _recognizer.energy_threshold = 300
        _recognizer.pause_threshold = 0.8
    return _recognizer


def _typed_input():
    """Fallback: let the user type instead of speaking."""
    try:
        text = input("You (type): ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    if text:
        hud_log(f"You: {text}")
    return text or None


def listen():
    """Listen once. Bilingual EN+SI auto-detect. Typed fallback if mic fails."""
    rec = _get_recognizer()
    audio = None
    if rec is not None:
        try:
            with sr.Microphone() as source:
                print("[listening... speak now]")
                hud_status("LISTENING")
                rec.adjust_for_ambient_noise(source, duration=0.5)
                audio = rec.listen(source, timeout=10, phrase_time_limit=20)
        except sr.WaitTimeoutError:
            hud_status("ONLINE")
            print("[didn't hear anything - listening again]")
            return None
        except Exception as e:
            hud_status("ONLINE")
            print(f"[mic unavailable ({e}) - type instead]")
            return _typed_input()
    if audio is None:
        return _typed_input()
    # --- recognize (bilingual) ---
    hud_status("THINKING")
    heard = {}
    for lang in ("en-US", "si-LK"):
        try:
            heard[lang] = rec.recognize_google(audio, language=lang)
        except sr.UnknownValueError:
            pass
        except Exception as e:
            print(f"[speech service issue: {e}]")
    si_text = heard.get("si-LK", "")
    en_text = heard.get("en-US", "")
    # prefer the Sinhala result only if it actually has Sinhala script
    text = si_text if (si_text and contains_sinhala(si_text)) else (en_text or si_text)
    hud_status("ONLINE")
    if text:
        print(f"You: {text}")
        hud_log(f"You: {text}")
        return text
    print("[couldn't understand - try again]")
    return None


# ---------------------------------------------------------------------- brain
def _get_chat():
    """Lazy Gemini chat session (new google-genai SDK). None if unavailable."""
    global _chat
    if _chat is not None:
        return _chat
    api_key = get_api_key()
    if not api_key or genai_client is None:
        return None
    try:
        client = genai_client.Client(api_key=api_key)
        _chat = client.chats.create(
            model=GEMINI_MODEL,
            config=genai_types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT),
        )
        return _chat
    except Exception as e:
        print(f"[Gemini setup failed: {e}]")
        return None


OFFLINE_ANSWERS = [
    (r"\bwho are you\b", "I am CYBER AI, your personal AI assistant. At your service."),
    (r"\bhow are you\b", "Running at full capacity, sir. How can I help?"),
    (r"\bthank", "Always a pleasure."),
    (r"\b(hello|hi|hey)\b", "Hello! What can I do for you?"),
    (r"ආයුබෝවන්|හෙලෝ|හායි", "ආයුබෝවන්! මම JARVIS. මට මොනවගේ උදව්වක් කරන්නද?"),
    (r"ඔයා කවුද|ඔබ කවුද", "මම CYBER AI, ඔබේ පෞද්ගලික AI සහායකයා."),
    (r"ස්තූතියි", "සතුටක්!"),
]


def ask_brain(question):
    """Ask Gemini; fall back to small offline answers if no API key."""
    chat = _get_chat()
    if chat is not None:
        try:
            resp = chat.send_message(question)
            return resp.text.strip()
        except Exception as e:
            print(f"[Gemini error: {e}]")
    for pattern, answer in OFFLINE_ANSWERS:
        if re.search(pattern, question, re.IGNORECASE):
            return answer
    if contains_sinhala(question):
        return ("මගේ AI මොළය තාම සම්බන්ධ වෙලා නැහැ - නොමිලේ GEMINI_API_KEY එකක් "
                "set කරන්න. එතකන් 'time', 'open youtube', 'weather', 'joke' "
                "වගේ commands try කරන්න.")
    return ("My AI brain isn't connected yet - set a free GEMINI_API_KEY to "
            "unlock full answers. Meanwhile, try commands like 'time', "
            "'open youtube', 'weather', or 'joke'.")


# ------------------------------------------------------------------ commands
def get_weather(city=""):
    try:
        url = f"https://wttr.in/{urllib.parse.quote(city or '')}?format=3"
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.read().decode().strip()
    except Exception:
        return "Couldn't reach the weather service right now."


def get_wiki_summary(topic):
    try:
        url = ("https://en.wikipedia.org/api/rest_v1/page/summary/"
               + urllib.parse.quote(topic))
        req = urllib.request.Request(url, headers={"User-Agent": "jarvis-diy/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = r.read().decode()
        m = re.search(r'"extract":"(.*?)"[},]', data)
        if m:
            summary = m.group(1).encode().decode("unicode_escape")
            return ". ".join(summary.split(". ")[:3]) + "."
        return f"Couldn't find a Wikipedia article on {topic}."
    except Exception:
        return "Wikipedia is unreachable right now."


JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I told my computer I needed a break... now it won't stop sending me KitKat ads.",
    "Why did the AI cross the road? To optimize the other side.",
    "There are only 10 kinds of people: those who understand binary and those who don't.",
    "My WiFi went down for five minutes today. So I had to talk to my family. They seem like nice people.",
]

SITE_SHORTCUTS = {
    "youtube": "https://youtube.com",
    "google": "https://google.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "facebook": "https://facebook.com",
    "whatsapp": "https://web.whatsapp.com",
    "netflix": "https://netflix.com",
    "spotify": "https://open.spotify.com",
}


# ------------------------------------------------------- windows key control
def _press_vk(vk):
    """Tap one virtual key (Windows only)."""
    if os.name != "nt":
        return False
    import ctypes
    ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk, 0, 2, 0)  # key up
    return True


def _press_combo(*vks):
    """Press a key combo like Win+D or Alt+F4 (Windows only)."""
    if os.name != "nt":
        return False
    import ctypes
    for vk in vks:
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
    for vk in reversed(vks):
        ctypes.windll.user32.keybd_event(vk, 0, 2, 0)
    return True


VK_VOLUME_MUTE, VK_VOLUME_DOWN, VK_VOLUME_UP = 0xAD, 0xAE, 0xAF
VK_MEDIA_NEXT, VK_MEDIA_PREV, VK_MEDIA_PLAY = 0xB0, 0xB1, 0xB3
VK_LWIN, VK_MENU, VK_F4 = 0x5B, 0x12, 0x73
VK_D = 0x44


def take_screenshot():
    try:
        from PIL import ImageGrab
    except ImportError:
        return "Install Pillow for screenshots: pip install pillow"
    try:
        folder = os.path.join(os.path.expanduser("~"), "Pictures")
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(
            folder, "jarvis_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".png")
        ImageGrab.grab().save(path)
        return f"Screenshot saved to {path}"
    except Exception as e:
        return f"Screenshot failed: {e}"


def battery_status():
    if os.name != "nt":
        return "Battery info is Windows-only."
    try:
        import ctypes

        class PS(ctypes.Structure):
            _fields_ = [("ACLineStatus", ctypes.c_byte),
                        ("BatteryFlag", ctypes.c_byte),
                        ("BatteryLifePercent", ctypes.c_byte),
                        ("Reserved1", ctypes.c_byte),
                        ("BatteryLifeTime", ctypes.c_ulong),
                        ("BatteryFullLifeTime", ctypes.c_ulong)]

        ps = PS()
        if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(ps)):
            pct = ps.BatteryLifePercent
            if pct > 100:
                return "No battery detected - probably a desktop."
            state = "and charging" if ps.ACLineStatus == 1 else "on battery"
            return f"Battery at {pct} percent, {state}."
        return "Couldn't read battery status."
    except Exception:
        return "Couldn't read battery status."


def open_windows_app(name):
    """Open a built-in Windows app or folder. Returns True if handled."""
    apps = {
        "notepad": "notepad",
        "calculator": "calc",
        "paint": "mspaint",
        "settings": "start ms-settings:",
        "file explorer": "explorer",
        "explorer": "explorer",
        "downloads": "explorer shell:Downloads",
        "documents": "explorer shell:MyDocuments",
        "pictures": "explorer shell:MyPictures",
        "cmd": "start cmd",
        "terminal": "start cmd",
        "chrome": "start chrome",
        "edge": "start msedge",
        "task manager": "taskmgr",
        "control panel": "control",
    }
    for key, cmd in apps.items():
        if key in name:
            os.system(cmd)
            return True
    return False


def handle_command(raw):
    """Run a command. Returns 'exit' to quit, else None."""
    raw = clean_heard(raw or "")
    q = raw.strip().lower()
    if not q:
        return None

    if any(w in q for w in ("exit", "quit", "goodbye", "bye jarvis", "sleep")):
        speak("Powering down. Goodbye!")
        return "exit"

    if q in ("stop", "be quiet", "quiet", "shut up", "nawathinna", "නිශ්ශබ්ද"):
        stop_speaking()
        speak("Okay.")
        return None

    if "time" in q:
        now = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {now}.")
        return None

    if "date" in q or "today" in q or "දවස" in q:
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        speak(f"Today is {today}.")
        return None

    # ---- media & volume ----
    if q in ("play", "pause", "resume", "play pause"):
        if _press_vk(VK_MEDIA_PLAY):
            speak("Toggled.")
        else:
            speak("Media keys need Windows.")
        return None
    if q.startswith("play ") and len(q) > 5:
        song = q[5:].strip()
        webbrowser.open("https://www.youtube.com/results?search_query="
                        + urllib.parse.quote(song))
        speak(f"Playing {song} on YouTube.")
        return None
    if q in ("next", "next song", "next track"):
        _press_vk(VK_MEDIA_NEXT)
        speak("Next.")
        return None
    if q in ("previous", "previous song", "last song"):
        _press_vk(VK_MEDIA_PREV)
        speak("Previous.")
        return None
    if any(w in q for w in ("volume up", "turn it up", "louder", "sound up")):
        if _press_vk(VK_VOLUME_UP):
            speak("Volume up.")
        else:
            speak("Volume control needs Windows.")
        return None
    if any(w in q for w in ("volume down", "turn it down", "quieter", "sound down")):
        if _press_vk(VK_VOLUME_DOWN):
            speak("Volume down.")
        else:
            speak("Volume control needs Windows.")
        return None
    if "mute" in q or "unmute" in q:
        if _press_vk(VK_VOLUME_MUTE):
            speak("Muted." if "unmute" not in q else "Unmuted.")
        else:
            speak("Volume control needs Windows.")
        return None

    # ---- screen & windows ----
    if "screenshot" in q or "screen shot" in q:
        speak(take_screenshot())
        return None
    if q == "close" or "close window" in q or "close this" in q:
        if _press_combo(VK_MENU, VK_F4):
            speak("Window closed.")
        else:
            speak("Window control needs Windows.")
        return None
    if "show desktop" in q or "minimize all" in q or "desktop" in q and "show" in q:
        if _press_combo(VK_LWIN, VK_D):
            speak("Desktop shown.")
        else:
            speak("Window control needs Windows.")
        return None

    # ---- system ----
    if "battery" in q:
        speak(battery_status())
        return None
    if "system info" in q or "pc info" in q or "about this pc" in q:
        info = f"{platform.system()} {platform.release()}, {platform.machine()}."
        speak(info + " " + battery_status())
        return None
    if q.startswith("open "):
        target = q[5:].strip()
        for site, url in SITE_SHORTCUTS.items():
            if site in target:
                webbrowser.open(url)
                speak(f"Opening {site}.")
                return None
        if open_windows_app(target):
            speak(f"Opening {target}.")
            return None
        webbrowser.open("https://www.google.com/search?q="
                        + urllib.parse.quote(target))
        speak(f"Searching the web for {target}.")
        return None
    if re.search(r"\block\b", q):
        speak("Locking the system.")
        if os.name == "nt":
            import ctypes
            ctypes.windll.user32.LockWorkStation()
        return None
    if "restart" in q:
        speak("Restarting in 10 seconds. Say cancel to stop.")
        if os.name == "nt":
            os.system("shutdown /r /t 10")
        return None
    if "shutdown" in q:
        speak("Shutting down in 10 seconds. Say cancel to stop.")
        if os.name == "nt":
            os.system("shutdown /s /t 10")
        return None
    if "cancel shutdown" in q or "abort shutdown" in q or "cancel restart" in q:
        if os.name == "nt":
            os.system("shutdown /a")
        speak("Cancelled.")
        return None

    # ---- web knowledge ----
    if q.startswith(("search ", "google ")):
        query = re.sub(r"^(search|google)\s+", "", q)
        webbrowser.open("https://www.google.com/search?q="
                        + urllib.parse.quote(query))
        speak(f"Searching Google for {query}.")
        return None
    if q.startswith("wikipedia ") or q.startswith("wiki "):
        topic = re.sub(r"^(wikipedia|wiki)\s+", "", q)
        speak(get_wiki_summary(topic))
        return None
    if "weather" in q:
        m = re.search(r"weather(?: in)?\s+(.+)", q)
        city = m.group(1).strip() if m else ""
        speak(get_weather(city))
        return None
    if "joke" in q:
        import random
        speak(random.choice(JOKES))
        return None

    # default: ask the AI brain (knows everything)
    speak(ask_brain(raw))
    return None


# ------------------------------------------------------------------ HUD (gui)
_hud_queue = None


def hud_log(msg):
    if _hud_queue is not None:
        _hud_queue.put(("log", msg))


def hud_status(msg):
    if _hud_queue is not None:
        _hud_queue.put(("status", msg))


def run_hud():
    """Cyber-style HUD window. The assistant runs in a background thread."""
    import queue
    import threading
    import tkinter as tk

    global _hud_queue
    _hud_queue = queue.Queue()

    root = tk.Tk()
    root.title("J.A.R.V.I.S.")
    root.geometry("520x620")
    root.configure(bg="#05080f")

    cyan = "#00e5ff"
    dim = "#0a1626"

    tk.Label(root, text="J.A.R.V.I.S.",
             font=("Consolas", 28, "bold"), fg=cyan, bg="#05080f").pack(pady=10)
    tk.Label(root, text="Just A Rather Very Intelligent System",
             font=("Consolas", 10), fg="#4a7a9a", bg="#05080f").pack()

    status = tk.Label(root, text="● INITIALIZING", font=("Consolas", 12, "bold"),
                      fg=cyan, bg="#05080f")
    status.pack(pady=8)

    log = tk.Text(root, font=("Consolas", 10), fg=cyan, bg=dim,
                  insertbackground=cyan, wrap="word", state="disabled")
    log.pack(fill="both", expand=True, padx=12, pady=8)

    entry = tk.Entry(root, font=("Consolas", 11), fg=cyan, bg=dim,
                     insertbackground=cyan)
    entry.pack(fill="x", padx=12, pady=(0, 12))

    def ui_log(msg):
        log.configure(state="normal")
        log.insert("end", msg + "\n")
        log.see("end")
        log.configure(state="disabled")

    def on_enter(_event=None):
        text = entry.get().strip()
        entry.delete(0, "end")
        if text:
            ui_log(f"You: {text}")
            threading.Thread(target=lambda: handle_command(text),
                             daemon=True).start()

    entry.bind("<Return>", on_enter)

    def worker():
        speak("Systems online. How can I help?")
        while True:
            cmd = listen()
            if cmd is None:
                continue
            if handle_command(cmd) == "exit":
                root.after(0, root.destroy)
                break

    def poll():
        try:
            while True:
                kind, msg = _hud_queue.get_nowait()
                if kind == "log":
                    ui_log(msg)
                elif kind == "status":
                    status.config(text="● " + msg)
        except queue.Empty:
            pass
        root.after(100, poll)

    threading.Thread(target=worker, daemon=True).start()
    root.after(100, poll)
    root.mainloop()


# ------------------------------------------------------------ gesture control
_gesture_thread = None
_gesture_stop_event = None
_gesture_reason = "not started yet"


def gesture_running():
    return _gesture_thread is not None and _gesture_thread.is_alive()


def gesture_status():
    return {"running": gesture_running(), "reason": _gesture_reason}


def start_gesture_mode():
    """Start Iron Man hand tracking in the background. True if running."""
    global _gesture_thread, _gesture_stop_event, _gesture_reason
    if gesture_running():
        _gesture_reason = "running"
        return True
    try:
        import gesture as gesture_mod
    except Exception as e:
        _gesture_reason = f"gesture.py error: {e}"
        print(f"[gesture unavailable: {e}]")
        return False
    if not gesture_mod.GESTURE_AVAILABLE:
        _gesture_reason = "missing packages — run: pip install opencv-python mediapipe pyautogui"
        print(f"[gesture needs: {_gesture_reason}]")
        return False
    cam_index = gesture_mod.find_camera()
    if cam_index is None:
        _gesture_reason = "no camera found (tried 0,1,2) — is it used by another app?"
        print("[gesture: no camera found]")
        return False
    import threading
    _gesture_stop_event = threading.Event()
    _gesture_thread = threading.Thread(
        target=gesture_mod.run, args=(_gesture_stop_event, cam_index), daemon=True)
    _gesture_thread.start()
    _gesture_reason = "running"
    print(f"[gesture control ON - camera {cam_index} active]")
    return True


def stop_gesture_mode():
    if _gesture_stop_event is not None:
        _gesture_stop_event.set()
    return True


# ----------------------------------------------------------------- web server
def run_web(port=8080):
    """Serve the beautiful web HUD on localhost. Browser handles voice."""
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    global WEB_MODE, _web_lock
    WEB_MODE = True
    _web_lock = threading.Lock()
    ensure_key_file()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    hud_path = resource_path("web_hud.html")
    try:
        with open(hud_path, "r", encoding="utf-8") as f:
            hud_html = f.read()
    except FileNotFoundError:
        print("web_hud.html not found next to jarvis.py")
        return

    def send_json(handler, obj):
        body = json.dumps(obj).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # keep the terminal clean

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                body = hud_html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/api/status":
                send_json(self, {"brain": brain_connected(),
                                 "version": VERSION,
                                 "has_key": bool(get_api_key()),
                                 "sdk": genai_client is not None})
            else:
                self.send_error(404)

        def do_POST(self):
            if self.path == "/api/gesture":
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    data = json.loads(self.rfile.read(length) or b"{}")
                except Exception:
                    data = {}
                action = str(data.get("action", "status"))
                if action == "start":
                    start_gesture_mode()
                elif action == "stop":
                    stop_gesture_mode()
                send_json(self, gesture_status())
                return
            if self.path == "/api/config":
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    data = json.loads(self.rfile.read(length) or b"{}")
                except Exception:
                    data = {}
                key = str(data.get("gemini_api_key", "")).strip()
                cfg = load_config()
                if key:
                    cfg["gemini_api_key"] = key
                elif "gemini_api_key" in cfg:
                    del cfg["gemini_api_key"]
                ok, err = save_config(cfg)
                global _chat
                _chat = None  # reconnect with the new key next time
                send_json(self, {"ok": ok, "error": err,
                                 "brain": brain_connected(),
                                 "sdk": genai_client is not None,
                                 "has_key": bool(get_api_key())})
                return
            if self.path != "/api/command":
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                data = {}
            text = str(data.get("text", "")).strip()
            with _web_lock:
                _web_replies.clear()
            result = handle_command(text) if text else None
            with _web_lock:
                replies = list(_web_replies)
            send_json(self, {"replies": replies, "exit": result == "exit"})

    # find a free port starting at 8080
    server = None
    for p in range(port, port + 20):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", p), Handler)
            port = p
            break
        except OSError:
            continue
    if server is None:
        print("No free port found.")
        return

    url = f"http://127.0.0.1:{port}"
    print("=" * 56)
    print("  CYBER AI web HUD is running!")
    print(f"  Open in your browser: {url}")
    print("  (opening automatically...)")
    print("=" * 56)
    # camera hand tracking: always on unless disabled
    if "--no-gesture" not in sys.argv:
        start_gesture_mode()
    else:
        print("[gesture control disabled by --no-gesture]")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[could not auto-open browser: {e}]")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nWeb server stopped.")


# ---------------------------------------------------------------------- main
def run_terminal():
    ensure_key_file()
    speak("Systems online. Speak or type a command. Say 'exit' to quit.")
    while True:
        try:
            cmd = listen()
        except KeyboardInterrupt:
            cmd = "exit"
        if cmd is None:
            continue
        if handle_command(cmd) == "exit":
            break


def main():
    if "--terminal" in sys.argv:
        run_terminal()
        return
    if "--hud" in sys.argv:
        run_hud()
        return
    # default: beautiful web UI
    run_web()


if __name__ == "__main__":
    main()
