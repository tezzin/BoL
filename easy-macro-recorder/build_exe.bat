@echo off
REM Builds dist\EasyMacroRecorder.exe (single file, no console window).
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --onefile --windowed --name EasyMacroRecorder easy_macro_recorder.py
echo.
echo Done: dist\EasyMacroRecorder.exe
