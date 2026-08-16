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
    print("Building for Windows: cliplay.exe")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--console",
            "--name",
            "cliplay",
            "--icon",
            "NONE",
            "CliPlayer.py",
        ],
        check=True,
    )
    print("Output: dist/cliplay.exe")


def build_linux():
    print("Building for Linux: cliplay.bin")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--console",
            "--name",
            "cliplay",
            "CliPlayer.py",
        ],
        check=True,
    )
    # Rename to .bin
    src = os.path.join("dist", "cliplay")
    dst = os.path.join("dist", "cliplay.bin")
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"Output: {dst}")
    elif os.path.exists(dst + ".exe"):
        pass


def build_macos():
    print("Building for macOS: cliplay.app")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--console",
            "--name",
            "cliplay",
            "CliPlayer.py",
        ],
        check=True,
    )
    # Rename executable to .bin inside app or standalone
    src = os.path.join("dist", "cliplay")
    dst = os.path.join("dist", "cliplay.bin")
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"Output: {dst}")

    # Create DMG
    app_path = os.path.join("dist", "cliplay.app")
    dmg_path = os.path.join("dist", "cliplay.dmg")
    if os.path.exists(app_path):
        print("Creating DMG...")
        subprocess.run(
            [
                "hdiutil",
                "create",
                "-volname",
                "CliPlayer",
                "-srcfolder",
                app_path,
                "-ov",
                "-format",
                "UDZO",
                dmg_path,
            ],
            check=True,
        )
        print(f"Output: {dmg_path}")


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
