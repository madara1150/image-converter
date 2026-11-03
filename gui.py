"""หน้าจอ GUI ของ Image Converter (customtkinter + drag & drop)"""

import os
import queue
import subprocess
import sys
import threading
from pathlib import Path

import customtkinter as ctk

from image_converter import APP_NAME, APP_VERSION, FORMATS, INPUT_EXTS, collect_files, convert_image

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:  # ใช้งานได้แม้ไม่มี drag & drop
    TkinterDnD = None

ACCENT = ("#2563EB", "#3B82F6")
ACCENT_HOVER = ("#1D4ED8", "#2563EB")
CARD = ("#FFFFFF", "#1F2329")
BG = ("#F3F5F9", "#15181D")
BORDER = ("#E3E7EE", "#2C313A")
MUTED = ("#6B7280", "#9CA3AF")
ROW_HOVER = ("#F1F5FB", "#262B33")
LOSSY = {"JPG", "WEBP"}
MAX_ROWS = 200

TEXT = {
    "th": {
        "subtitle": "แปลงนามสกุลไฟล์รูปภาพ ง่าย เร็ว และไม่ต้องใช้อินเทอร์เน็ต",
        "drop": "ลากไฟล์หรือโฟลเดอร์รูปภาพมาวางที่นี่",
        "drop_hint": "รองรับ PNG, JPG, WEBP, BMP, TIFF, GIF, ICO, HEIC",
        "or": "หรือ",
        "pick_files": "เลือกไฟล์",
        "pick_folder": "เลือกโฟลเดอร์",
        "add": "+ เพิ่ม",
        "clear": "ล้างทั้งหมด",
        "n_files": "{n} ไฟล์ · {size}",
        "more": "และอีก {n} ไฟล์…",
        "to": "แปลงเป็น",
        "quality": "คุณภาพ",
        "quality_na": "ไม่มีผลกับ {fmt}",
        "save_to": "บันทึกไปที่",
        "same_folder": "โฟลเดอร์เดียวกับไฟล์ต้นฉบับ",
        "browse": "เลือก…",
        "convert": "แปลง {n} ไฟล์เป็น {fmt}",
        "convert_empty": "เพิ่มไฟล์เพื่อเริ่มแปลง",
        "working": "กำลังแปลง {i}/{n}…",
        "done": "✓ แปลงสำเร็จ {ok} ไฟล์",
        "done_err": "แปลงสำเร็จ {ok} ไฟล์ · ไม่สำเร็จ {err} ไฟล์",
        "open_folder": "เปิดโฟลเดอร์",
        "errors_title": "บางไฟล์แปลงไม่สำเร็จ",
    },
    "en": {
        "subtitle": "Convert image formats: simple, fast and fully offline",
        "drop": "Drag & drop images or folders here",
        "drop_hint": "Supports PNG, JPG, WEBP, BMP, TIFF, GIF, ICO, HEIC",
        "or": "or",
        "pick_files": "Choose files",
        "pick_folder": "Choose folder",
        "add": "+ Add",
        "clear": "Clear all",
        "n_files": "{n} files · {size}",
        "more": "and {n} more…",
        "to": "Convert to",
        "quality": "Quality",
        "quality_na": "Not used by {fmt}",
        "save_to": "Save to",
        "same_folder": "Same folder as the original",
        "browse": "Browse…",
        "convert": "Convert {n} files to {fmt}",
        "convert_empty": "Add files to start",
        "working": "Converting {i}/{n}…",
        "done": "✓ Converted {ok} files",
        "done_err": "Converted {ok} · Failed {err}",
        "open_folder": "Open folder",
        "errors_title": "Some files could not be converted",
    },
}


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def open_path(path):
    if sys.platform == "win32":
        os.startfile(path)  # noqa: S606
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


_Base = ctk.CTk
if TkinterDnD is not None:
    class _Base(ctk.CTk, TkinterDnD.DnDWrapper):  # noqa: F811
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            try:
                self.TkdndVersion = TkinterDnD._require(self)
            except Exception:  # noqa: BLE001
                self.TkdndVersion = None


class App(_Base):
    def __init__(self):
        ctk.set_appearance_mode("system")
        super().__init__(fg_color=BG)
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry("780x680")
        self.minsize(640, 600)
        self._set_icon()

        self.files = []
        self.lang = "en" if os.environ.get("LANG", "").startswith("en") and sys.platform != "win32" else "th"
        self.target = ctk.StringVar(value="JPG")
        self.quality = ctk.IntVar(value=90)
        self.out_dir = ctk.StringVar(value="")
        self.last_out = None
        self.busy = False
        self.events = queue.Queue()

        self.font_title = ctk.CTkFont(size=26, weight="bold")
        self.font_h = ctk.CTkFont(size=14, weight="bold")
        self.font_body = ctk.CTkFont(size=13)
        self.font_small = ctk.CTkFont(size=12)
        self.font_big = ctk.CTkFont(size=16, weight="bold")

        self.root_frame = None
        self.build()
        self.after(100, self.poll_events)

    def t(self, key, **kw):
        return TEXT[self.lang][key].format(**kw)

    def _set_icon(self):
        self.logo = None
        icon = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "assets" / "icon.png"
        if icon.exists():
            from PIL import Image, ImageTk
            img = Image.open(icon)
            self.logo = ctk.CTkImage(img, size=(40, 40))
            self._icon = ImageTk.PhotoImage(img.resize((128, 128)))
            self.iconphoto(True, self._icon)

    # ------------------------------------------------------------ layout

    def build(self):
        if self.root_frame is not None:
            self.out_dir.set(self.out_entry.get())
            self.root_frame.destroy()
        root = self.root_frame = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=24, pady=20)

        # header
        header = ctk.CTkFrame(root, fg_color="transparent")
        header.pack(fill="x")
        titles = ctk.CTkFrame(header, fg_color="transparent")
        titles.pack(side="left")
        ctk.CTkLabel(titles, text=f"  {APP_NAME}", font=self.font_title, image=self.logo,
                     compound="left").pack(anchor="w")
        ctk.CTkLabel(titles, text=self.t("subtitle"), font=self.font_body,
                     text_color=MUTED).pack(anchor="w")
        lang = ctk.CTkSegmentedButton(header, values=["TH", "EN"], width=90,
                                      command=self.switch_lang,
                                      selected_color=ACCENT, selected_hover_color=ACCENT_HOVER)
        lang.set(self.lang.upper())
        lang.pack(side="right", anchor="n")

        # file card
        self.file_card = ctk.CTkFrame(root, fg_color=CARD, corner_radius=14,
                                      border_width=1, border_color=BORDER)
        self.file_card.pack(fill="both", expand=True, pady=(18, 12))
        self.render_files()

        # settings card
        card = ctk.CTkFrame(root, fg_color=CARD, corner_radius=14, border_width=1, border_color=BORDER)
        card.pack(fill="x")
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text=self.t("to"), font=self.font_h).grid(
            row=0, column=0, sticky="w", padx=(18, 12), pady=(16, 8))
        fmt = ctk.CTkSegmentedButton(card, values=list(FORMATS), variable=self.target,
                                     command=lambda _: self.refresh_controls(), height=34,
                                     selected_color=ACCENT, selected_hover_color=ACCENT_HOVER,
                                     font=self.font_body)
        fmt.grid(row=0, column=1, sticky="we", padx=(0, 18), pady=(16, 8))

        ctk.CTkLabel(card, text=self.t("quality"), font=self.font_h).grid(
            row=1, column=0, sticky="w", padx=(18, 12), pady=8)
        qrow = ctk.CTkFrame(card, fg_color="transparent")
        qrow.grid(row=1, column=1, sticky="we", padx=(0, 18), pady=8)
        self.q_slider = ctk.CTkSlider(qrow, from_=10, to=100, number_of_steps=90,
                                      variable=self.quality, button_color=ACCENT,
                                      button_hover_color=ACCENT_HOVER, progress_color=ACCENT,
                                      command=lambda _: self.refresh_controls())
        self.q_slider.pack(side="left", fill="x", expand=True)
        self.q_label = ctk.CTkLabel(qrow, text="", width=130, anchor="e", font=self.font_body)
        self.q_label.pack(side="left")

        ctk.CTkLabel(card, text=self.t("save_to"), font=self.font_h).grid(
            row=2, column=0, sticky="w", padx=(18, 12), pady=(8, 16))
        orow = ctk.CTkFrame(card, fg_color="transparent")
        orow.grid(row=2, column=1, sticky="we", padx=(0, 18), pady=(8, 16))
        # ไม่ใช้ textvariable เพราะจะทำให้ placeholder ไม่แสดง
        self.out_entry = ctk.CTkEntry(orow, placeholder_text=self.t("same_folder"),
                                      height=34, font=self.font_body)
        if self.out_dir.get():
            self.out_entry.insert(0, self.out_dir.get())
        self.out_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(orow, text=self.t("browse"), width=90, height=34, command=self.pick_out,
                      fg_color="transparent", border_width=1, border_color=BORDER,
                      text_color=("gray15", "gray90"), hover_color=ROW_HOVER).pack(side="left", padx=(8, 0))

        # bottom: progress + convert
        bottom = ctk.CTkFrame(root, fg_color="transparent")
        bottom.pack(fill="x", pady=(16, 0))
        self.progress = ctk.CTkProgressBar(bottom, height=6, progress_color=ACCENT)
        self.progress.set(0)
        status_row = self.status_row = ctk.CTkFrame(bottom, fg_color="transparent", height=28)
        status_row.pack(fill="x", pady=(0, 10))
        self.status = ctk.CTkLabel(status_row, text="", font=self.font_body, text_color=MUTED)
        self.status.pack(side="left")
        self.open_btn = ctk.CTkButton(status_row, text=self.t("open_folder"), width=110, height=28,
                                      fg_color="transparent", text_color=ACCENT, hover_color=ROW_HOVER,
                                      command=lambda: self.last_out and open_path(self.last_out))
        self.convert_btn = ctk.CTkButton(bottom, text="", height=48, corner_radius=12,
                                         font=self.font_big, fg_color=ACCENT,
                                         hover_color=ACCENT_HOVER, command=self.start)
        self.convert_btn.pack(fill="x")

        if TkinterDnD is not None and getattr(self, "TkdndVersion", None):
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self.on_drop)

        self.refresh_controls()

    def render_files(self):
        for w in self.file_card.winfo_children():
            w.destroy()

        if not self.files:
            box = ctk.CTkFrame(self.file_card, fg_color="transparent")
            box.place(relx=0.5, rely=0.5, anchor="center")
            ctk.CTkLabel(box, text="⬇", font=ctk.CTkFont(size=44), text_color=ACCENT).pack()
            ctk.CTkLabel(box, text=self.t("drop"), font=self.font_big).pack(pady=(4, 2))
            ctk.CTkLabel(box, text=self.t("drop_hint"), font=self.font_small,
                         text_color=MUTED).pack()
            ctk.CTkLabel(box, text=self.t("or"), font=self.font_small,
                         text_color=MUTED).pack(pady=8)
            btns = ctk.CTkFrame(box, fg_color="transparent")
            btns.pack()
            ctk.CTkButton(btns, text=self.t("pick_files"), width=130, height=36, fg_color=ACCENT,
                          hover_color=ACCENT_HOVER, command=self.add_files).pack(side="left", padx=5)
            ctk.CTkButton(btns, text=self.t("pick_folder"), width=130, height=36,
                          fg_color="transparent", border_width=1, border_color=BORDER,
                          text_color=("gray15", "gray90"), hover_color=ROW_HOVER,
                          command=self.add_folder).pack(side="left", padx=5)
            return

        top = ctk.CTkFrame(self.file_card, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 4))
        total = sum(self._size(f) for f in self.files)
        ctk.CTkLabel(top, text=self.t("n_files", n=len(self.files), size=human_size(total)),
                     font=self.font_h).pack(side="left")
        ctk.CTkButton(top, text=self.t("clear"), width=90, height=28, fg_color="transparent",
                      text_color=MUTED, hover_color=ROW_HOVER,
                      command=self.clear).pack(side="right")
        ctk.CTkButton(top, text=self.t("add"), width=80, height=28, fg_color="transparent",
                      text_color=ACCENT, hover_color=ROW_HOVER,
                      command=self.add_files).pack(side="right", padx=4)

        lst = ctk.CTkScrollableFrame(self.file_card, fg_color="transparent")
        lst.pack(fill="both", expand=True, padx=8, pady=(0, 10))
        for f in self.files[:MAX_ROWS]:
            self._file_row(lst, f)
        if len(self.files) > MAX_ROWS:
            ctk.CTkLabel(lst, text=self.t("more", n=len(self.files) - MAX_ROWS),
                         text_color=MUTED, font=self.font_small).pack(pady=6)

    def _file_row(self, parent, f):
        row = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=8, height=40)
        row.pack(fill="x", pady=1)
        ext = f.suffix.lstrip(".").upper()[:4]
        ctk.CTkLabel(row, text=ext, width=48, height=24, corner_radius=6,
                     fg_color=("#E8EEFC", "#24324D"), text_color=ACCENT,
                     font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(8, 10), pady=6)
        ctk.CTkLabel(row, text=f.name, font=self.font_body, anchor="w").pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row, text="✕", width=28, height=28, fg_color="transparent", text_color=MUTED,
                      hover_color=ROW_HOVER, command=lambda: self.remove(f)).pack(side="right", padx=4)
        ctk.CTkLabel(row, text=human_size(self._size(f)), font=self.font_small,
                     text_color=MUTED).pack(side="right", padx=8)
        for w in (row, *row.winfo_children()[:2]):
            w.bind("<Enter>", lambda _e: row.configure(fg_color=ROW_HOVER))
            w.bind("<Leave>", lambda _e: row.configure(fg_color="transparent"))

    @staticmethod
    def _size(f):
        try:
            return f.stat().st_size
        except OSError:
            return 0

    def refresh_controls(self):
        fmt = self.target.get()
        if fmt in LOSSY:
            self.q_slider.configure(state="normal", button_color=ACCENT, progress_color=ACCENT)
            self.q_label.configure(text=f"{self.quality.get()}%", text_color=("gray10", "gray90"))
        else:
            self.q_slider.configure(state="disabled", button_color=BORDER, progress_color=BORDER)
            self.q_label.configure(text=self.t("quality_na", fmt=fmt), text_color=MUTED)
        if self.busy:
            return
        if self.files:
            self.convert_btn.configure(text=self.t("convert", n=len(self.files), fmt=fmt), state="normal")
        else:
            self.convert_btn.configure(text=self.t("convert_empty"), state="disabled")

    # ------------------------------------------------------------ actions

    def switch_lang(self, value):
        self.lang = value.lower()
        self.build()

    def add_paths(self, paths):
        known = set(self.files)
        for p in collect_files(paths):
            if p not in known:
                self.files.append(p)
                known.add(p)
        self.after_change()

    def add_files(self):
        types = [("Images", " ".join(f"*{e}" for e in sorted(INPUT_EXTS))), ("All files", "*.*")]
        self.add_paths(ctk.filedialog.askopenfilenames(filetypes=types))

    def add_folder(self):
        d = ctk.filedialog.askdirectory()
        if d:
            self.add_paths([d])

    def on_drop(self, event):
        self.add_paths(self.tk.splitlist(event.data))

    def remove(self, f):
        self.files.remove(f)
        self.after_change()

    def clear(self):
        self.files.clear()
        self.after_change()

    def after_change(self):
        self.render_files()
        self.status.configure(text="", text_color=MUTED)
        self.open_btn.pack_forget()
        self.progress.set(0)
        self.progress.pack_forget()
        self.refresh_controls()

    def pick_out(self):
        d = ctk.filedialog.askdirectory()
        if d:
            self.out_dir.set(d)
            self.out_entry.delete(0, "end")
            self.out_entry.insert(0, d)

    def start(self):
        if not self.files or self.busy:
            return
        self.busy = True
        self.convert_btn.configure(state="disabled")
        self.open_btn.pack_forget()
        self.progress.set(0)
        self.progress.pack(fill="x", before=self.status_row, pady=(0, 8))
        items = list(self.files)
        out = self.out_entry.get().strip() or None
        self.last_out = Path(out) if out else items[0].parent
        args = (items, self.target.get(), self.quality.get(), out)
        threading.Thread(target=self.worker, args=args, daemon=True).start()

    def worker(self, items, target, quality, out):
        errors = []
        for i, f in enumerate(items, 1):
            try:
                convert_image(f, out, target, quality)
            except Exception as e:  # noqa: BLE001
                errors.append(f"{f.name}: {e}")
            self.events.put(("progress", i, len(items)))
        self.events.put(("done", len(items), errors))

    def poll_events(self):
        try:
            while True:
                ev = self.events.get_nowait()
                if ev[0] == "progress":
                    _, i, n = ev
                    self.progress.set(i / n)
                    self.status.configure(text=self.t("working", i=i, n=n), text_color=MUTED)
                else:
                    self.finish(ev[1], ev[2])
        except queue.Empty:
            pass
        self.after(80, self.poll_events)

    def finish(self, total, errors):
        self.busy = False
        ok = total - len(errors)
        if errors:
            self.status.configure(text=self.t("done_err", ok=ok, err=len(errors)), text_color="#DC2626")
            from tkinter import messagebox
            messagebox.showwarning(self.t("errors_title"), "\n".join(errors[:15]))
        else:
            self.status.configure(text=self.t("done", ok=ok), text_color=("#16A34A", "#4ADE80"))
        if ok:
            self.open_btn.pack(side="right")
        self.refresh_controls()


def run():
    App().mainloop()
