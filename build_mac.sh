#!/bin/bash
# สร้างโปรแกรมสำหรับ macOS -> dist/ImageConverter.app
set -e
cd "$(dirname "$0")"
# Python ของ Xcode (/usr/bin/python3) ใช้ Tk 8.5 ซึ่งทำให้หน้าต่างดำบน macOS รุ่นใหม่
# จึงเลือก Python จาก Homebrew หรือ python.org ก่อน (ตั้ง PYTHON=... เองได้)
PYTHON="${PYTHON:-$(ls /opt/homebrew/bin/python3 /usr/local/bin/python3 2>/dev/null | head -1)}"
PYTHON="${PYTHON:-python3}"
if ! "$PYTHON" -c "import tkinter, sys; sys.exit(tkinter.TkVersion < 8.6)" 2>/dev/null; then
  echo "ต้องใช้ Python ที่มี Tk 8.6 ขึ้นไป: brew install python python-tk"
  exit 1
fi
"$PYTHON" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-build.txt

pyinstaller --noconfirm --clean --windowed --onedir --noupx \
  --icon assets/icon.png --add-data assets:assets \
  --collect-data customtkinter --collect-all tkinterdnd2 \
  --name ImageConverter \
  --osx-bundle-identifier com.imageconverter.app \
  image_converter.py

# ad-hoc sign (ฟรี) ถ้ามี Developer ID ให้ตั้งค่า SIGN_ID แล้วรันใหม่
codesign --force --deep --sign "${SIGN_ID:--}" dist/ImageConverter.app
echo "เสร็จแล้ว: dist/ImageConverter.app"
./make_dmg.sh
