"""ถ่ายรูปหน้าจอโปรแกรมสำหรับ README (ใช้ใน GitHub Actions บน macOS)

python tools/screenshot.py docs/screenshot-light.png light
python tools/screenshot.py docs/screenshot-dark.png dark
"""

import random
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import customtkinter as ctk  # noqa: E402
from PIL import Image  # noqa: E402

import gui  # noqa: E402

out, mode = Path(sys.argv[1]).resolve(), sys.argv[2]
lang = sys.argv[3] if len(sys.argv) > 3 else "en"

# สร้างไฟล์ตัวอย่างที่มีขนาดต่างๆ กัน
tmp = Path(tempfile.mkdtemp())
random.seed(1)
for name, size in [("holiday_beach.png", 900), ("family_dinner.png", 700), ("logo_transparent.png", 300),
                   ("product_photo.webp", 800), ("scanned_receipt.tiff", 600), ("IMG_2048.heic", 500)]:
    img = Image.effect_noise((size, size), random.randint(20, 90)).convert("RGB")
    fmt = {".heic": "PNG"}.get(Path(name).suffix)
    img.save(tmp / name, fmt) if fmt else img.save(tmp / name)

app = gui.App()
ctk.set_appearance_mode(mode)
app.lang = lang
app.build()
app.add_paths(sorted(tmp.iterdir(), key=lambda p: p.name))
app.geometry("780x680+40+0")


def shot():
    app.update()
    x, y = app.winfo_rootx(), app.winfo_rooty()
    w, h = app.winfo_width(), app.winfo_height()
    title = 28
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["screencapture", "-x", f"-R{x},{y - title},{w},{h + title}", str(out)], check=True)
    print("saved", out)
    app.destroy()


app.lift()
app.attributes("-topmost", True)
app.after(2500, shot)
app.mainloop()
