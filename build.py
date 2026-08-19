#!/usr/bin/env python3
"""
Build script for CliPlayer
Generates Windows executable using PyInstaller.
"""
import os
import platform
import shutil
import subprocess
import sys


def build_windows():
    print("Building CliPlayer 0.0.5 Beta for Windows...")
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


def main():
    system = platform.system().lower()
    if system != "windows":
        print(f"Error: This build script only supports Windows. Detected: {system}")
        sys.exit(1)

    os.makedirs("dist", exist_ok=True)
    build_windows()
    print("Build complete.")


if __name__ == "__main__":
    main()
