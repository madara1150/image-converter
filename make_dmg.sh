#!/bin/bash
# สร้างไฟล์ .dmg จาก dist/ImageConverter.app
# ./make_dmg.sh [ชื่อไฟล์.dmg]
set -e
cd "$(dirname "$0")"
OUT="${1:-dist/ImageConverter.dmg}"
STAGE="$(mktemp -d)"
cp -R dist/ImageConverter.app "$STAGE/"
ln -s /Applications "$STAGE/Applications"
rm -f "$OUT"
hdiutil create -volname "Image Converter" -srcfolder "$STAGE" -ov -format UDZO "$OUT" >/dev/null
rm -rf "$STAGE"
echo "สร้างแล้ว: $OUT"
