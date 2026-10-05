#!/usr/bin/env python3
"""
CYBER AI gesture control - Iron Man style hand tracking.

  Point (index finger) .... move the mouse cursor
  Pinch (thumb + index) ... left click
  Fist .................... play / pause media
  2 fingers ............... volume up
  3 fingers ............... volume down
  Open palm ............... mute toggle

Press Q in the camera window (or stop from the web UI) to quit.

Needs: pip install opencv-python mediapipe pyautogui
"""

import math
import time

try:
    import cv2
    import mediapipe as mp
    import pyautogui
    pyautogui.FAILSAFE = False
    GESTURE_AVAILABLE = True
except ImportError:
    GESTURE_AVAILABLE = False

# tuning
PINCH_THRESHOLD = 0.045   # normalized thumb-index distance
CLICK_COOLDOWN = 0.6
ACTION_COOLDOWN = 1.0
SMOOTHING = 0.35          # cursor smoothing 0..1 (higher = snappier)

HELP = (
    "Point=index moves cursor | Pinch=click | Fist=play/pause | "
    "2 fingers=vol+ | 3 fingers=vol- | Palm=mute | Q=quit"
)

# latest camera frame for the web UI preview (thread-safe)
import threading as _threading
_frame_lock = _threading.Lock()
latest_frame = None


def get_preview_frame():
    """Return a small BGR frame copy for the web preview, or None."""
    with _frame_lock:
        return None if latest_frame is None else latest_frame.copy()


def _publish_frame(frame):
    global latest_frame
    small = cv2.resize(frame, (320, 240))
    with _frame_lock:
        latest_frame = small


def _landmarks(hand_lms):
    return [(p.x, p.y) for p in hand_lms.landmark]


def fingers_up(pts):
    """Which of index/middle/ring/pinky are raised. Returns [bool x4]."""
    tips = (8, 12, 16, 20)
    pips = (6, 10, 14, 18)
    return [pts[t][1] < pts[p][1] for t, p in zip(tips, pips)]


def pinch_distance(pts):
    x1, y1 = pts[4]
    x2, y2 = pts[8]
    return math.hypot(x1 - x2, y1 - y2)


def map_range(v, a, b):
    v = max(a, min(b, v))
    return (v - a) / (b - a)


def detect_gesture(pts):
    """Return (gesture_name, finger_count)."""
    ups = fingers_up(pts)
    count = sum(ups)
    if pinch_distance(pts) < PINCH_THRESHOLD and ups[0]:
        return "pinch", count
    if count == 0:
        return "fist", count
    if count == 1 and ups[0]:
        return "point", count
    if count == 2:
        return "vol_up", count
    if count == 3:
        return "vol_down", count
    if count >= 4:
        return "palm", count
    return "none", count


def _press_vk(vk):
    import ctypes
    ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk, 0, 2, 0)


def do_action(name):
    """Fire a PC action for a gesture. Windows media/volume keys."""
    import os
    if os.name != "nt":
        print(f"[gesture:{name}] (Windows only)")
        return
    VK = {"vol_up": 0xAF, "vol_down": 0xAE, "mute": 0xAD,
          "play": 0xB3, "next": 0xB0, "prev": 0xB1}
    if name == "click":
        pyautogui.click()
    elif name in VK:
        _press_vk(VK[name])


def find_camera(max_index=3):
    """Return first working camera index, or None. Some laptops use 1 or 2."""
    if not GESTURE_AVAILABLE:
        return None
    for i in range(max_index):
        try:
            cap = cv2.VideoCapture(i)
            ok = cap.isOpened()
            cap.release()
            if ok:
                return i
        except Exception:
            continue
    return None


def run(stop_event=None, cam_index=0):
    """Main loop. Returns True if it ran, False if camera/deps missing."""
    if not GESTURE_AVAILABLE:
        print("[gesture deps missing: pip install opencv-python mediapipe pyautogui]")
        return False
    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        print("[camera not found]")
        return False

    screen_w, screen_h = pyautogui.size()
    cur_x, cur_y = screen_w / 2, screen_h / 2
    hands = mp.solutions.hands.Hands(
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7)
    draw = mp.solutions.drawing_utils

    last_click = 0.0
    last_action = 0.0
    frame_count = 0
    print("[CYBER AI gesture control ON] " + HELP)
    cv2.namedWindow("CYBER AI - Gesture Control", cv2.WINDOW_NORMAL)

    try:
        while True:
            if stop_event is not None and stop_event.is_set():
                break
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)  # mirror view
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = hands.process(rgb)
            label = "no hand"

            if res.multi_hand_landmarks:
                hand = res.multi_hand_landmarks[0]  # primary hand
                draw.draw_landmarks(frame, hand,
                                    mp.solutions.hands.HAND_CONNECTIONS)
                pts = _landmarks(hand)
                gesture, _ = detect_gesture(pts)
                label = gesture
                now = time.time()

                if gesture == "point":
                    # frame was mirrored above, so x maps directly
                    nx, ny = pts[8][0], pts[8][1]
                    tx = map_range(nx, 0.1, 0.9) * screen_w
                    ty = map_range(ny, 0.1, 0.9) * screen_h
                    cur_x += (tx - cur_x) * SMOOTHING
                    cur_y += (ty - cur_y) * SMOOTHING
                    pyautogui.moveTo(cur_x, cur_y)
                elif gesture == "pinch":
                    if now - last_click > CLICK_COOLDOWN:
                        last_click = now
                        do_action("click")
                        label = "pinch CLICK"
                elif gesture == "fist":
                    if now - last_action > ACTION_COOLDOWN:
                        last_action = now
                        do_action("play")
                        label = "fist PLAY/PAUSE"
                elif gesture == "vol_up":
                    if now - last_action > ACTION_COOLDOWN:
                        last_action = now
                        do_action("vol_up")
                        label = "VOL +"
                elif gesture == "vol_down":
                    if now - last_action > ACTION_COOLDOWN:
                        last_action = now
                        do_action("vol_down")
                        label = "VOL -"
                elif gesture == "palm":
                    if now - last_action > ACTION_COOLDOWN:
                        last_action = now
                        do_action("mute")
                        label = "palm MUTE"

            cv2.putText(frame, f"CYBER AI: {label}", (12, 32),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 65), 2)
            cv2.putText(frame, "Q = quit", (12, 64),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (120, 120, 120), 1)
            cv2.imshow("CYBER AI - Gesture Control", frame)
            if frame_count % 3 == 0:
                _publish_frame(frame)
            frame_count += 1
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[CYBER AI gesture control OFF]")
    return True


if __name__ == "__main__":
    run()
