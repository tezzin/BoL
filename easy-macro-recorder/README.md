# Easy Macro Recorder

Record your mouse and keyboard, then play it back once, a set number of times, or continuously until you stop it.

![Easy Macro Recorder](docs/screenshot.png)

## Features

- Records mouse movement, clicks, scrolling and every key press, with the original timing.
- One-click **Record**, **Play** and **Stop**, plus global hotkeys that work while the window is in the background:
  - **F9** start / stop recording
  - **F10** start / stop playback
- **Repeat N times** or **Repeat continuously** until you press Stop / F10.
- Playback **speed** (0.25x to 5x) and an optional **pause between repeats**.
- Save and open macros as `.macro.json` files.
- Keys and mouse buttons are always released when playback stops, so nothing gets stuck down.
- The click on the Stop button itself is left out of the recording.

## Run it (Windows)

1. Install Python 3.9 or newer from python.org (tick "Add Python to PATH").
2. In this folder:

   ```
   pip install -r requirements.txt
   python easy_macro_recorder.py
   ```

## Make an .exe

Double-click `build_exe.bat`, or run:

```
pip install pyinstaller
pyinstaller --onefile --windowed --name EasyMacroRecorder easy_macro_recorder.py
```

The program ends up in `dist\EasyMacroRecorder.exe` and runs without Python installed.

## Tips

- To replay into a program running as administrator, run Easy Macro Recorder as administrator too (Windows blocks input from a lower-privilege app).
- Turn off "Record mouse movement" to record only clicks; playback then jumps straight to each click position.
- Some games ignore simulated input or block it with anti-cheat; check a game's rules before automating it.

## Development

`macro_engine.py` holds recording and playback with no GUI code; `easy_macro_recorder.py` is the tkinter window. Run the tests with:

```
pip install pytest
python -m pytest tests
```
