#!/usr/bin/env python3
"""
Matrix / ASCII CLI Video Player
Renders videos as real-time Matrix Green ASCII Art directly in your Terminal!
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

# Windows ტერმინალში ANSI ფერების ჩართვა
if os.name == "nt":
    os.system("")


def get_term_size():
    if os.name == "nt":
        try:
            import ctypes
            import msvcrt

            kernel32 = ctypes.windll.kernel32
            hConsole = msvcrt.get_osfhandle(sys.stdout.fileno())

            if not hConsole or hConsole == -1:
                raise ValueError("invalid stdout handle")

            class COORD(ctypes.Structure):
                _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

            class SMALL_RECT(ctypes.Structure):
                _fields_ = [
                    ("Left", ctypes.c_short),
                    ("Top", ctypes.c_short),
                    ("Right", ctypes.c_short),
                    ("Bottom", ctypes.c_short),
                ]

            class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
                _fields_ = [
                    ("dwSize", COORD),
                    ("dwCursorPosition", COORD),
                    ("wAttributes", ctypes.c_ushort),
                    ("srWindow", SMALL_RECT),
                    ("dwMaximumWindowSize", COORD),
                ]

            csbi = CONSOLE_SCREEN_BUFFER_INFO()
            if kernel32.GetConsoleScreenBufferInfo(hConsole, ctypes.byref(csbi)):
                width = csbi.srWindow.Right - csbi.srWindow.Left + 1
                height = csbi.srWindow.Bottom - csbi.srWindow.Top + 1
                if 10 <= width <= 400 and 5 <= height <= 200:
                    return width, height
        except Exception:
            pass

    size = shutil.get_terminal_size((80, 24))
    return size.columns, size.lines


def get_duration(path: str):
    cap = cv2.VideoCapture(path)
    if cap.isOpened():
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
        cap.release()
        if fps > 0 and frames > 0:
            return frames / fps
    return None


def build_audio_filter(speed: float) -> str:
    if speed <= 0:
        return "atempo=1.0"
    if 0.5 <= speed <= 2.0:
        return f"atempo={speed:.4f}"
    parts = []
    remaining = speed
    while remaining > 2.0:
        parts.append("atempo=2.0")
        remaining /= 2.0
    if remaining < 0.5:
        parts.append("atempo=0.5")
    else:
        parts.append(f"atempo={remaining:.4f}")
    return ",".join(parts)


def start_ffplay_audio(path: str, start_sec: float, speed: float):
    if not shutil.which("ffplay"):
        return None
    cmd = [
        "ffplay",
        "-ss", str(start_sec),
        "-i", path,
        "-vn",
        "-nodisp",
        "-autoexit",
        "-loglevel", "quiet",
        "-af", build_audio_filter(speed),
    ]
    kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        return subprocess.Popen(cmd, **kwargs)
    except Exception:
        return None


def stop_ffplay_audio(proc):
    if proc is None:
        return
    try:
        proc.kill()
    except Exception:
        pass


def get_theme_colors(theme: str):
    themes = {
        "matrix": {
            "bright": "\033[38;2;210;255;210m\033[1m",
            "high": "\033[38;2;0;255;70m",
            "mid": "\033[38;2;0;130;35m",
            "low": "\033[38;2;0;45;10m",
        },
        "amber": {
            "bright": "\033[38;2;255;240;200m\033[1m",
            "high": "\033[38;2;255;180;50m",
            "mid": "\033[38;2;180;100;20m",
            "low": "\033[38;2;60;30;10m",
        },
        "cyan": {
            "bright": "\033[38;2;200;255;255m\033[1m",
            "high": "\033[38;2;0;220;255m",
            "mid": "\033[38;2;0;130;160m",
            "low": "\033[38;2;0;40;60m",
        },
        "white": {
            "bright": "\033[38;2;240;240;240m\033[1m",
            "high": "\033[38;2;200;200;200m",
            "mid": "\033[38;2;120;120;120m",
            "low": "\033[38;2;40;40;40m",
        },
        "rainbow": {
            "bright": "\033[38;2;255;255;255m\033[1m",
            "high": "\033[38;2;255;0;128m",
            "mid": "\033[38;2;128;0;255m",
            "low": "\033[38;2;0;128;255m",
        },
    }
    return themes.get(theme, themes["matrix"])


def build_progress_bar(pos: float, duration: float, width: int = 30) -> str:
    if duration <= 0:
        return "[" + " " * width + "]"
    ratio = max(0.0, min(1.0, pos / duration))
    filled = int(ratio * width)
    return "[" + ("█" * filled) + ("░" * (width - filled)) + "]"


def apply_brightness_contrast(gray, brightness=0, contrast=0):
    if brightness == 0 and contrast == 0:
        return gray
    buf = gray.astype(np.float32)
    if contrast != 0:
        factor = (259.0 * (contrast + 255.0)) / (255.0 * (259.0 - contrast))
        buf = factor * (buf - 128.0) + 128.0
    buf = buf + brightness
    return np.clip(buf, 0, 255).astype(np.uint8)


def frame_to_matrix_ascii(frame, term_w, term_h, chars=" .:-=+*#%@", theme="matrix", brightness=0, contrast=0):
    h, w = frame.shape[:2]
    new_w = min(max(20, term_w), 160)
    new_h = max(5, min(term_h - 3, int(h * (new_w / float(w)) * 0.48)))

    small = cv2.resize(frame, (new_w, new_h))
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gray = apply_brightness_contrast(gray, brightness, contrast)

    colors = get_theme_colors(theme)
    char_arr = np.array(list(chars))
    indices = (gray / 255.0 * (len(chars) - 1)).astype(int)
    mapped_chars = char_arr[indices]

    lines = []
    for y in range(new_h):
        row_chars = []
        row_gray = gray[y]
        row_mapped = mapped_chars[y]
        for x in range(new_w):
            pixel = row_gray[x]
            ch = row_mapped[x]
            if pixel > 210:
                color = colors["bright"]
            elif pixel > 110:
                color = colors["high"]
            elif pixel > 40:
                color = colors["mid"]
            else:
                color = colors["low"]
            row_chars.append(f"{color}{ch}")
        lines.append("".join(row_chars) + "\033[0m")

    return "\n".join(lines)


def parse_args():
    p = argparse.ArgumentParser(description="Matrix ASCII Video Player")
    p.add_argument("file", help="ვიდეო ფაილის გზა")
    p.add_argument("--loop", action="store_true", help="ვიდეოს უსასრულო გაფორმება")
    p.add_argument("--start", type=float, default=0.0, help="დაწყების დრო (წამებში)")
    p.add_argument("--fps", type=float, default=None, help="FPS-ის ხელით მითითება")
    p.add_argument("--speed", type=float, default=1.0, help="სიჩქარე")
    p.add_argument("--theme", default="matrix", choices=["matrix", "amber", "cyan", "white", "rainbow"], help="ფერების თემა")
    p.add_argument("--chars", default=" .:-=+*#%@", help="ASCII კარაქთერების სიმბოლოები")
    p.add_argument("--brightness", type=int, default=0, help="ნაკაშკაშის კორექცია (-255 .. 255)")
    p.add_argument("--contrast", type=int, default=0, help="კონტრასტის კორექცია (-255 .. 255)")
    p.add_argument("--no-audio", action="store_true", help="ხმის გამორთვა")
    return p.parse_args()


def main():
    args = parse_args()
    path = args.file

    if not Path(path).exists():
        print(f"Warning: file '{path}' not found. Attempting to open anyway...")

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print("ERROR: Unable to open video source.")
        sys.exit(1)

    src_fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    fps = args.fps or (src_fps if src_fps > 0 else 25.0)
    duration = get_duration(path)

    if args.start > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, args.start * 1000.0)

    # Keyboard input setup
    try:
        import msvcrt
        def kb_hit(): return msvcrt.kbhit()
        def kb_get(): return msvcrt.getwch()
    except ImportError:
        import select
        def kb_hit(): return bool(select.select([sys.stdin], [], [], 0)[0])
        def kb_get(): return sys.stdin.read(1)

    audio_proc = None
    paused = False
    speed = max(0.01, args.speed)
    last_ascii_frame = ""
    fps_values = []
    last_frame_time = time.perf_counter()
    drift = 0.0

    def audio_start(sec, spd):
        nonlocal audio_proc
        if args.no_audio: return
        if audio_proc:
            stop_ffplay_audio(audio_proc)
            audio_proc = None
        audio_proc = start_ffplay_audio(path, sec, spd)

    def audio_stop():
        nonlocal audio_proc
        if audio_proc:
            stop_ffplay_audio(audio_proc)
            audio_proc = None

    if not args.no_audio:
        audio_start(args.start, speed)

    sys.stdout.write("\033[?25l\x1b[H")
    sys.stdout.flush()

    try:
        next_frame_time = time.perf_counter()
        while True:
            term_w, term_h = get_term_size()

            if not paused:
                ret, frame = cap.read()
                if not ret:
                    if args.loop:
                        cap.set(cv2.CAP_PROP_POS_MSEC, args.start * 1000.0)
                        if not args.no_audio:
                            audio_start(args.start, speed)
                        continue
                    else:
                        break

                last_ascii_frame = frame_to_matrix_ascii(frame, term_w, term_h, args.chars, args.theme, args.brightness, args.contrast)

            ascii_frame = last_ascii_frame

            pos = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            dur_str = f"{duration:.1f}s" if duration else "N/A"
            now = time.perf_counter()
            frame_dt = now - last_frame_time
            if frame_dt > 0:
                last_frame_time = now
                fps_values.append(1.0 / frame_dt)
                if len(fps_values) > 30:
                    fps_values.pop(0)
            avg_fps = sum(fps_values) / len(fps_values) if fps_values else 0.0
            progress = build_progress_bar(pos, duration)
            status = f"\033[1;32m[MATRIX PLAYER]\033[0m {path} | {pos:.1f}s / {dur_str} | Speed: {speed:.2f}x | FPS: {avg_fps:.1f} | {progress}"

            sys.stdout.write(f"\x1b[H{ascii_frame}\n{status}\033[K\n")
            sys.stdout.flush()

            next_frame_time += (1.0 / fps) / speed
            now = time.perf_counter()
            drift = next_frame_time - now
            if drift > 0:
                time.sleep(drift)
            else:
                if not paused:
                    cap.read()
                continue

            if kb_hit():
                key = kb_get()
                if key in ('q', 'Q', '\x1b'):
                    break
                elif key == ' ':
                    paused = not paused
                    if paused:
                        audio_stop()
                    else:
                        audio_start(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0, speed)
                elif key in ('+', '='):
                    speed *= 1.1
                    if not args.no_audio:
                        audio_start(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0, speed)
                elif key == '-':
                    speed = max(0.01, speed / 1.1)
                    if not args.no_audio:
                        audio_start(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0, speed)

    finally:
        cap.release()
        audio_stop()
        sys.stdout.write("\033[?25h\033[0m\x1b[H")
        sys.stdout.flush()


if __name__ == "__main__":
    main()