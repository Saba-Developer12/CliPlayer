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
import ffmpeg

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


def frame_to_matrix_ascii(frame, term_w, term_h, chars=" .:-=+*#%@"):
    """კადრის გარდაქმნა მწვანე Matrix ASCII გრადიენტად"""
    h, w = frame.shape[:2]
    new_w = min(max(20, term_w), 160)
    new_h = max(5, min(term_h - 3, int(h * (new_w / float(w)) * 0.48)))

    small = cv2.resize(frame, (new_w, new_h))
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

    lines = []
    for y in range(gray.shape[0]):
        row_chars = []
        for pixel in gray[y]:
            idx = int((pixel / 255.0) * (len(chars) - 1))
            ch = chars[idx]

            # Matrix RGB ფერების დინამიური შერჩევა სიკაშკაშის მიხედვით
            if pixel > 210:
                color = "\033[38;2;210;255;210m\033[1m"  # განათება (თითქმის თეთრი)
            elif pixel > 110:
                color = "\033[38;2;0;255;70m"  # მკვეთრი მწვანე
            elif pixel > 40:
                color = "\033[38;2;0;130;35m"  # მუქი მწვანე
            else:
                color = "\033[38;2;0;45;10m"  # ფონის ძალიან მუქი მწვანე

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

    paused = False
    speed = max(0.01, args.speed)
    last_ascii_frame = ""

    # ეკრანის გასუფთავება სტარტზე
    sys.stdout.write("\x1b[2J")
    sys.stdout.flush()

    try:
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

                last_ascii_frame = frame_to_matrix_ascii(frame, term_w, term_h)

            ascii_frame = last_ascii_frame

            pos = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            dur_str = f"{duration:.1f}s" if duration else "N/A"
            status = f"\033[1;32m[MATRIX PLAYER]\033[0m {path} | {pos:.1f}s / {dur_str} | Speed: {speed:.2f}x"

            sys.stdout.write(f"\x1b[2J\x1b[H{ascii_frame}\n{status}\n")
            sys.stdout.flush()

            time.sleep(max(0.001, (1.0 / fps) / speed))

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
        sys.stdout.write("\033[0m\x1b[2J")
        sys.stdout.flush()  # გასუფთავება გამოსვლისას


if __name__ == "__main__":
    main()