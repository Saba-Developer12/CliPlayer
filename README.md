# CliPlayer

**Matrix / ASCII CLI Video Player** — renders videos as real-time Matrix Green ASCII Art directly in your terminal!

![Python](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- 🎬 Real-time video-to-ASCII conversion using OpenCV
- 🟢 Matrix Green color palette with dynamic brightness levels
- 🔊 Audio playback via `ffplay`
- ⏯️ Playback controls: pause, speed up, slow down, seek
- 🔁 Loop mode for continuous playback
- ⌨️ Keyboard-driven controls
 - 🖥️ Windows

## Requirements

- Python 3.6+
- [OpenCV](https://pypi.org/project/opencv-python/) — Python library for reading video frames
- [ffmpeg-python](https://pypi.org/project/ffmpeg-python/) — Python wrapper for FFmpeg, used to read video metadata
- [FFmpeg](https://ffmpeg.org/) — external command-line tools for audio playback
  - `ffplay` — handles audio playback

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install FFmpeg

FFmpeg is an external program required only for audio playback:

## Usage

```bash
python CliPlayer.py <video_file> [options]
```

### Examples

```bash
python CliPlayer.py video.mp4
python CliPlayer.py video.mp4 --loop
python CliPlayer.py video.mp4 --start 10 --speed 1.5 --no-audio
python CliPlayer.py video.mp4 --fps 30
```

## Options

| Flag | Description |
|------|-------------|
| `file` | Path to the video file |
| `--matrix` | Matrix Green ASCII mode (default: on) |
| `--loop` | Loop the video indefinitely |
| `--start SECONDS` | Start playback at a specific time (seconds) |
| `--fps FPS` | Override the frame rate |
| `--speed SPEED` | Playback speed multiplier (default: 1.0) |
| `--no-audio` | Disable audio playback |

## Keyboard Controls

| Key | Action |
|-----|--------|
| `Space` | Pause / Resume |
| `+` / `=` | Increase playback speed |
| `-` | Decrease playback speed |
| `Q` / `Esc` | Quit |

## How It Works

1. Frames are read from the video using OpenCV
2. Each frame is resized to fit the terminal dimensions
3. Pixels are mapped to ASCII characters based on brightness
4. Brightness-dependent Matrix Green ANSI colors are applied
5. The ASCII frame is rendered in the terminal in real time

## Building

Build a standalone Windows executable using PyInstaller.

### Prerequisites

```bash
pip install pyinstaller
```

### Build Command

```bash
python build.py
# Output: dist/CliPlayer.exe
```

Or use the Windows shortcut script:

- **Windows**: `build.bat`

## License

MIT
