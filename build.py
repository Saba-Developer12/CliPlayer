#!/usr/bin/env python3
"""
Build script for CliPlayer
Generates platform-specific executables using PyInstaller.
"""
import os
import platform
import shutil
import subprocess
import sys


def build_windows():
    print("Building Cli Player 0.0.1 Alpha for Windows...")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--console",
            "--name",
            "CliPlayer",
            "--version-file",
            "version.txt",
            "CliPlayer.py",
        ],
        check=True,
    )
    print("Output: dist/CliPlayer.exe")


def build_linux():
    print("Building Cli Player 0.0.1 Alpha for Linux...")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--console",
            "--name",
            "cliplayer",
            "CliPlayer.py",
        ],
        check=True,
    )
    src = os.path.join("dist", "cliplayer")
    dst = os.path.join("dist", "cliplayer.bin")
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"Output: {dst}")


def build_macos():
    print("Building Cli Player 0.0.1 Alpha for macOS...")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--console",
            "--name",
            "cliplayer",
            "CliPlayer.py",
        ],
        check=True,
    )
    src = os.path.join("dist", "cliplayer")
    dst = os.path.join("dist", "cliplayer.bin")
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"Output: {dst}")


def main():
    system = platform.system().lower()
    os.makedirs("dist", exist_ok=True)

    if system == "windows":
        build_windows()
    elif system == "linux":
        build_linux()
    elif system == "darwin":
        build_macos()
    else:
        print(f"Unsupported platform: {system}")
        sys.exit(1)

    print("Build complete.")


if __name__ == "__main__":
    main()
