"""Image Converter - แปลงนามสกุลไฟล์รูปภาพ (PNG, JPG, WEBP, BMP, TIFF, GIF, ICO)

ใช้งานแบบ GUI:  python image_converter.py
ใช้งานแบบ CLI:  python image_converter.py a.png b.png --to jpg --quality 90 --out ./output
"""

import argparse
import sys
from pathlib import Path

from PIL import Image

try:  # รองรับ HEIC (รูปจาก iPhone) ถ้าติดตั้ง pillow-heif ไว้
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass

APP_NAME = "Image Converter"
APP_VERSION = "1.0.0"

# ชื่อที่แสดง -> (Pillow format, นามสกุลไฟล์)
FORMATS = {
    "JPG": ("JPEG", ".jpg"),
    "PNG": ("PNG", ".png"),
    "WEBP": ("WEBP", ".webp"),
    "BMP": ("BMP", ".bmp"),
    "TIFF": ("TIFF", ".tiff"),
    "GIF": ("GIF", ".gif"),
    "ICO": ("ICO", ".ico"),
}

INPUT_EXTS = {
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff",
    ".gif", ".ico", ".heic", ".heif",
}

# ฟอร์แมตที่ไม่รองรับพื้นหลังโปร่งใส
NO_ALPHA = {"JPEG", "BMP"}


def convert_image(src, out_dir, target, quality=90, bg_color=(255, 255, 255), overwrite=False):
    """แปลงไฟล์เดียว คืนค่า path ของไฟล์ผลลัพธ์"""
    pil_format, ext = FORMATS[target]
    src = Path(src)
    out_dir = Path(out_dir) if out_dir else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    dst = out_dir / (src.stem + ext)
    if dst.resolve() == src.resolve() or (dst.exists() and not overwrite):
        n = 1
        while True:
            candidate = out_dir / f"{src.stem}_{n}{ext}"
            if not candidate.exists():
                dst = candidate
                break
            n += 1

    with Image.open(src) as img:
        img.load()
        exif = img.info.get("exif")
        icc = img.info.get("icc_profile")

        if pil_format in NO_ALPHA:
            img = _flatten(img, bg_color)
        elif img.mode not in ("RGB", "RGBA", "L", "LA", "P"):
            img = img.convert("RGBA" if _has_alpha(img) else "RGB")

        kwargs = {}
        if pil_format == "JPEG":
            kwargs.update(quality=quality, optimize=True, progressive=True)
        elif pil_format == "WEBP":
            kwargs.update(quality=quality, method=4)
        elif pil_format == "PNG":
            kwargs.update(optimize=True)
        elif pil_format == "TIFF":
            kwargs.update(compression="tiff_lzw")
        elif pil_format == "ICO":
            # ไอคอนต้องเป็นสี่เหลี่ยมจัตุรัส: เติมพื้นโปร่งใสรอบรูป
            side = max(img.size)
            square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
            rgba = img.convert("RGBA")
            square.paste(rgba, ((side - img.width) // 2, (side - img.height) // 2))
            img = square
            kwargs.update(sizes=[(s, s) for s in (16, 32, 48, 64, 128, 256)
                                 if s <= side] or [img.size])

        if exif and pil_format in ("JPEG", "WEBP", "PNG", "TIFF"):
            kwargs["exif"] = exif
        if icc and pil_format in ("JPEG", "WEBP", "PNG", "TIFF"):
            kwargs["icc_profile"] = icc

        img.save(dst, pil_format, **kwargs)
    return dst


def _has_alpha(img):
    return img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info)


def _flatten(img, bg_color):
    """วางรูปโปร่งใสบนพื้นหลังสีทึบ (สำหรับ JPG/BMP)"""
    if _has_alpha(img):
        rgba = img.convert("RGBA")
        bg = Image.new("RGB", rgba.size, bg_color)
        bg.paste(rgba, mask=rgba.split()[-1])
        return bg
    return img.convert("RGB")


def collect_files(paths):
    files = []
    for p in map(Path, paths):
        if p.is_dir():
            files += sorted(f for f in p.rglob("*") if f.suffix.lower() in INPUT_EXTS)
        elif p.suffix.lower() in INPUT_EXTS:
            files.append(p)
    return files


# ---------------------------------------------------------------- CLI

def run_cli(argv):
    parser = argparse.ArgumentParser(description=f"{APP_NAME} {APP_VERSION}")
    parser.add_argument("inputs", nargs="+", help="ไฟล์หรือโฟลเดอร์รูปภาพ")
    parser.add_argument("--to", required=True, choices=[k.lower() for k in FORMATS],
                        help="นามสกุลปลายทาง")
    parser.add_argument("--quality", type=int, default=90, help="คุณภาพ 1-100 (JPG/WEBP)")
    parser.add_argument("--out", help="โฟลเดอร์ผลลัพธ์ (ค่าเริ่มต้น: โฟลเดอร์เดียวกับไฟล์ต้นฉบับ)")
    parser.add_argument("--overwrite", action="store_true", help="เขียนทับไฟล์ที่มีชื่อซ้ำ")
    args = parser.parse_args(argv)

    files = collect_files(args.inputs)
    if not files:
        print("ไม่พบไฟล์รูปภาพ")
        return 1
    failed = 0
    for f in files:
        try:
            dst = convert_image(f, args.out, args.to.upper(), args.quality, overwrite=args.overwrite)
            print(f"✓ {f} -> {dst}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"✗ {f}: {e}")
    print(f"เสร็จสิ้น: สำเร็จ {len(files) - failed}, ล้มเหลว {failed}")
    return 1 if failed else 0


# ---------------------------------------------------------------- GUI

def run_gui():
    import gui

    gui.run()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(run_cli(sys.argv[1:]))
    run_gui()
