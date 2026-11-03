@echo off
REM Build for Windows -> dist\ImageConverter\ImageConverter.exe
cd /d "%~dp0"
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements-build.txt

REM --onedir       : no self-extracting to temp at runtime (onefile is often flagged)
REM --noupx        : no UPX packing (the main cause of false positives)
REM --version-file : embed publisher/version metadata in the .exe
pyinstaller --noconfirm --clean --windowed --onedir --noupx ^
  --icon assets\icon.ico --add-data assets:assets ^
  --collect-data customtkinter --collect-all tkinterdnd2 ^
  --name ImageConverter ^
  --version-file version_info.txt ^
  image_converter.py

echo.
echo Done: dist\ImageConverter\ImageConverter.exe
echo If you have a code signing certificate, sign it with signtool (see README).
pause
