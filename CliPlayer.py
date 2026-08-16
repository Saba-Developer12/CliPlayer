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


def get_duration(path: str):
    try:
        probe = ffmpeg.probe(path)
        return float(probe["format"]["duration"])
    except Exception:
        return None


def start_ffplay_audio(path: str, start_sec: float):
    if not shutil.which("ffplay"):
        return None
    cmd = [
        "ffplay",
        "-vn",
        "-nodisp",
        "-autoexit",
        "-loglevel",
        "quiet",
        "-ss",
        str(start_sec),
        path,
    ]
    kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        return subprocess.Popen(cmd, **kwargs)
    except Exception:
        return None


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
    p.add_argument("--matrix", action="store_true", default=True, help="Matrix Green ASCII რეჟიმი")
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

    def audio_start(sec):
        nonlocal audio_proc
        if args.no_audio: return
        if audio_proc:
            try: audio_proc.kill()
            except Exception: pass
        audio_proc = start_ffplay_audio(path, sec)

    def audio_stop():
        nonlocal audio_proc
        if audio_proc:
            try: audio_proc.kill()
            except Exception: pass
            audio_proc = None

    if not args.no_audio:
        audio_start(args.start)

    paused = False
    speed = max(0.01, args.speed)

    # ეკრანის გასუფთავება სტარტზე
    print("\x1b[2J", end="")

    try:
        while True:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    if args.loop:
                        cap.set(cv2.CAP_PROP_POS_MSEC, args.start * 1000.0)
                        if not args.no_audio: audio_start(args.start)
                        continue
                    else:
                        break

                term_size = shutil.get_terminal_size((80, 24))
                ascii_frame = frame_to_matrix_ascii(frame, term_size.columns, term_size.lines)

                pos = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                dur_str = f"{duration:.1f}s" if duration else "N/A"
                status = f"\033[1;32m[MATRIX PLAYER]\033[0m {path} | {pos:.1f}s / {dur_str} | Speed: {speed:.2f}x"

                # \x1b[H აბრუნებს კურსორს დასაწყისში ეკრანის ციმციმის გარეშე
                print(f"\x1b[H{ascii_frame}\n{status}")

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
                        audio_start(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0)
                elif key in ('+', '='):
                    speed *= 1.1
                elif key == '-':
                    speed = max(0.01, speed / 1.1)

    finally:
        cap.release()
        audio_stop()
        print("\033[0m\x1b[2J")  # გასუფთავება გამოსვლისას


if __name__ == "__main__":
    main()