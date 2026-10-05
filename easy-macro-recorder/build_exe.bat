@echo off
REM Builds dist\EasyMacroRecorder.exe (single file, no console window).
REM The .spec disables UPX and embeds version metadata to reduce antivirus
REM false positives. For a build that is NOT flagged at all, sign it with a
REM code-signing certificate afterwards (see README).
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --clean EasyMacroRecorder.spec
echo.
echo Done: dist\EasyMacroRecorder.exe
