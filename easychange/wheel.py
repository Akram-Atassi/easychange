"""The pop-up wheel (and the small message bar used when there's nothing to show)."""
from __future__ import annotations

import logging
import math
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path

from . import converters, winutil

KEY = "#010203"  # painted wherever the window should be see-through (Windows only)
VISIBLE_SLOTS = 8

C = {
    "ring": "#1e2230", "ring_edge": "#2f3546", "seg": "#262b3a", "seg_hover": "#3b82f6",
    "seg_busy": "#22c55e", "text": "#e6e8ee", "muted": "#8b93a7", "center": "#141824",
    "ok": "#16a34a", "err": "#dc2626", "info": "#1e2230",
}

if sys.platform == "win32":
    FONT, FONT_BOLD = ("Segoe UI", 10), ("Segoe UI Semibold", 11)
else:
    FONT, FONT_BOLD = ("DejaVu Sans", 9), ("DejaVu Sans", 10, "bold")


class Popup:
    def __init__(self, at: tuple[int, int] | None = None):
        winutil.enable_dpi_awareness()
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.transparent = winutil.set_transparent_color(self.root, KEY)
        self.s = self.root.winfo_fpixels("1i") / 96  # DPI scale factor
        self.at = at or self.root.winfo_pointerxy()
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bd=0,
                                bg=KEY if self.transparent else C["center"])
        self.canvas.pack(fill="both", expand=True)
        self.font = tkfont.Font(family=FONT[0], size=FONT[1])
        self.font_bold = tkfont.Font(family=FONT_BOLD[0], size=FONT_BOLD[1],
                                     weight="bold" if "bold" in FONT_BOLD else "normal")
        self.root.bind("<Escape>", lambda e: self.close())
        self._closing = False

    def px(self, v: float) -> int:
        return round(v * self.s)

    def place(self, w: int, h: int) -> None:
        """Center a w x h window on the anchor point, kept inside the monitor."""
        left, top, right, bottom = winutil.work_area(self.at, self.root)
        x = min(max(self.at[0] - w // 2, left), right - w)
        y = min(max(self.at[1] - h // 2, top), bottom - h)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.canvas.config(width=w, height=h)

    def show(self) -> None:
        self.root.deiconify()
        self.root.lift()
        winutil.force_foreground(self.root)
        self.root.focus_force()
        self._fade(0.0)

    def _fade(self, a: float) -> None:
        a = min(a + 0.2, 0.97)
        try:
            self.root.attributes("-alpha", a)
        except tk.TclError:
            return
        if a < 0.97:
            self.root.after(16, self._fade, a)

    def close(self) -> None:
        if not self._closing:
            self._closing = True
            self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()

    # ---- message bar -------------------------------------------------- #

    def bar(self, text: str, kind: str = "info", timeout_ms: int = 2400,
            on_click=None) -> None:
        cv = self.canvas
        cv.delete("all")
        for ev in ("<Motion>", "<Button-1>", "<MouseWheel>", "<Button-4>", "<Button-5>",
                   "<FocusOut>"):
            cv.unbind(ev)
            self.root.unbind(ev)
        pad_x, h = self.px(18), self.px(38)
        icon = {"ok": "✓  ", "err": "✕  "}.get(kind, "")
        w = self.font.measure(icon + text) + 2 * pad_x
        self.place(w, h)
        bg = C[kind]
        rounded_rect(cv, 0, 0, w - 1, h - 1, h // 2, fill=bg, outline=C["ring_edge"])
        cv.create_text(w // 2, h // 2, text=icon + text, fill=C["text"], font=self.font)
        cv.config(cursor="hand2" if on_click else "")
        cv.bind("<Button-1>", lambda e: (on_click and on_click(), self.close()))
        self.root.after(timeout_ms, self.close)
        if self.root.state() == "withdrawn":
            self.show()


class Wheel(Popup):
    R_OUT, R_IN = 118, 44

    def __init__(self, files: list[Path], targets: list[str], at=None):
        super().__init__(at)
        self.files, self.targets = files, targets
        self.progress: tuple[int, int] | None = None  # (done, total) for batches
        self.sel: int | None = None  # index into targets
        self.offset = 0              # first target shown when there are > 8
        self.busy = False
        self.spin = 0
        self.grow = 0.55             # opening animation, 0.55 -> 1.0
        self.results: queue.Queue = queue.Queue()

        size = self.px(2 * self.R_OUT + 8)
        self.place(size, size)
        self.cx = self.cy = size / 2

        cv = self.canvas
        cv.bind("<Motion>", self.on_motion)
        cv.bind("<Leave>", lambda e: self.hover(None))
        cv.bind("<Button-1>", self.on_click)
        cv.bind("<Button-3>", lambda e: self.close())
        self.root.bind("<MouseWheel>", lambda e: self.step(-1 if e.delta > 0 else 1))
        self.root.bind("<Button-4>", lambda e: self.step(-1))
        self.root.bind("<Button-5>", lambda e: self.step(1))
        for k in ("<Left>", "<Up>", "<Shift-Tab>"):
            self.root.bind(k, lambda e: self.step(-1))
        for k in ("<Right>", "<Down>", "<Tab>"):
            self.root.bind(k, lambda e: self.step(1))
        self.root.bind("<Return>", lambda e: self.choose(self.sel))
        self.root.bind("<space>", lambda e: self.choose(self.sel))
        for i in range(1, VISIBLE_SLOTS + 1):
            self.root.bind(str(i), lambda e, i=i: self.choose(self.offset + i - 1))
        # Clicking anywhere else (window loses focus) dismisses the wheel.
        self.root.bind("<FocusOut>", lambda e: self.busy or self.root.after(80, self._maybe_close))

        self.draw()
        self.show()
        self._animate_open()

    # ---- geometry -------------------------------------------------------- #

    @property
    def slots(self) -> int:
        return min(len(self.targets), VISIBLE_SLOTS)

    def visible(self) -> list[int]:
        return [(self.offset + i) % len(self.targets) for i in range(self.slots)]

    def slot_angle(self, slot: int) -> float:
        """Center angle of a slot in Tk degrees (0 = 3 o'clock, counter-clockwise).
        Slot 0 sits at 12 o'clock and the rest follow clockwise."""
        return 90 - slot * 360 / self.slots

    def slot_at(self, x: float, y: float) -> int | None | str:
        dx, dy = x - self.cx, self.cy - y
        d = math.hypot(dx, dy)
        if d < self.px(self.R_IN):
            return "center"
        if d > self.px(self.R_OUT):
            return None
        ang = math.degrees(math.atan2(dy, dx))
        step = 360 / self.slots
        return round(((90 - ang) % 360) / step) % self.slots

    # ---- drawing ---------------------------------------------------------- #

    def draw(self) -> None:
        cv, k = self.canvas, self.grow
        cv.delete("all")
        cx, cy = self.cx, self.cy
        ro, ri = self.px(self.R_OUT) * k, self.px(self.R_IN) * k
        step = 360 / self.slots
        gap = self.px(3)

        cv.create_oval(cx - ro, cy - ro, cx + ro, cy + ro, fill=C["ring"],
                       outline=C["ring_edge"], width=self.px(1.5))
        ro_seg = ro - self.px(5) * k
        for slot, idx in enumerate(self.visible()):
            mid = self.slot_angle(slot)
            active = idx == self.sel
            fill = (C["seg_busy"] if self.busy else C["seg_hover"]) if active else C["seg"]
            if self.slots == 1:
                cv.create_oval(cx - ro_seg, cy - ro_seg, cx + ro_seg, cy + ro_seg,
                               fill=fill, outline=C["ring"], width=gap)
            else:
                cv.create_arc(cx - ro_seg, cy - ro_seg, cx + ro_seg, cy + ro_seg,
                              start=mid - step / 2, extent=step, style="pieslice",
                              fill=fill, outline=C["ring"], width=gap)
            lr = (ro_seg + ri) / 2
            lx = cx + lr * math.cos(math.radians(mid))
            ly = cy - lr * math.sin(math.radians(mid))
            if self.slots == 1:
                lx, ly = cx, cy - lr
            dim = self.busy and not active
            cv.create_text(lx, ly, text=converters.label(self.targets[idx]),
                           fill=C["muted"] if dim else C["text"],
                           font=self.font_bold if active else self.font)

        # Center hub: source type on top, chosen target below.
        cv.create_oval(cx - ri, cy - ri, cx + ri, cy + ri, fill=C["center"],
                       outline=C["ring_edge"], width=self.px(1.5))
        if self.busy:
            a = self.spin
            rr = ri - self.px(5)
            cv.create_arc(cx - rr, cy - rr, cx + rr, cy + rr, start=a, extent=100,
                          style="arc", outline=C["seg_busy"], width=self.px(3))
            text = "%d/%d" % self.progress if self.progress else "…"
            cv.create_text(cx, cy, text=text, fill=C["text"], font=self.font_bold)
            return
        if k < 0.95:
            return
        cv.create_text(cx, cy - self.px(10), text=self.source_label(), fill=C["muted"],
                       font=self.font)
        if self.sel is not None:
            label = "→ " + converters.label(self.targets[self.sel])
        else:
            label = "Esc"
        cv.create_text(cx, cy + self.px(9), text=label,
                       fill=C["text"] if self.sel is not None else C["muted"],
                       font=self.font_bold if self.sel is not None else self.font)
        if len(self.targets) > VISIBLE_SLOTS:
            # Page hint: "3/12" under the hub so people know scrolling reveals more.
            pos = (self.sel if self.sel is not None else self.offset) + 1
            cv.create_text(cx, cy + self.px(27), text=f"{pos}/{len(self.targets)}",
                           fill=C["muted"], font=(FONT[0], max(FONT[1] - 3, 6)))

    def source_label(self) -> str:
        """'DOCX' for one file, '3 PNG' for three PNGs, '5 FILES' for a mix."""
        exts = {converters.norm_ext(f).upper() or "FILE" for f in self.files}
        if len(self.files) == 1:
            return exts.pop()
        return f"{len(self.files)} {exts.pop() if len(exts) == 1 else 'FILES'}"

    def _animate_open(self) -> None:
        if self.grow < 1:
            self.grow = min(1.0, self.grow + 0.09)
            self.draw()
            self.root.after(12, self._animate_open)

    # ---- interaction ----------------------------------------------------- #

    def hover(self, idx: int | None) -> None:
        if not self.busy and idx != self.sel:
            self.sel = idx
            self.draw()

    def on_motion(self, e) -> None:
        slot = self.slot_at(e.x, e.y)
        self.hover(self.visible()[slot] if isinstance(slot, int) else None)

    def on_click(self, e) -> None:
        slot = self.slot_at(e.x, e.y)
        if slot is None or slot == "center":
            if not self.busy:
                self.close()
            return
        self.choose(self.visible()[slot])

    def step(self, d: int) -> None:
        """Scroll / arrow keys: move the highlight; past the edge the wheel turns."""
        if self.busy:
            return
        n = len(self.targets)
        self.sel = (self.offset if d > 0 else self.offset + self.slots - 1) \
            if self.sel is None else (self.sel + d) % n
        if n > VISIBLE_SLOTS:
            rel = (self.sel - self.offset) % n
            if rel >= self.slots:
                self.offset = (self.sel - (self.slots - 1 if d > 0 else 0)) % n
        self.draw()

    def _maybe_close(self) -> None:
        if not self.busy and not self._closing and self.root.focus_get() is None:
            self.close()

    # ---- converting ------------------------------------------------------- #

    def choose(self, idx: int | None) -> None:
        if self.busy or idx is None or not (0 <= idx < len(self.targets)):
            return
        self.sel, self.busy = idx, True
        target = self.targets[idx]
        self.draw()

        def work():
            try:
                done = converters.convert_many(
                    self.files, target,
                    progress=lambda d, t: t > 1 and self.results.put(("progress", (d, t))))
                for path, msg in done[1]:
                    logging.error("Converting %s to %s failed: %s", path, target, msg)
                self.results.put(("done", done))
            except Exception as e:
                logging.exception("Converting %s to %s failed", self.files, target)
                self.results.put(("err", e))

        threading.Thread(target=work, daemon=True).start()
        self._poll()

    def _poll(self) -> None:
        while True:
            try:
                kind, value = self.results.get_nowait()
            except queue.Empty:
                self.spin = (self.spin - 12) % 360
                self.draw()
                self.root.after(30, self._poll)
                return
            if kind != "progress":
                break
            self.progress = value
        if kind == "err":
            self.bar(shorten(str(value) or type(value).__name__, 90), "err", 6000)
            return
        outputs, failures = value
        reveal = (lambda: reveal_in_explorer(outputs[0])) if outputs else None
        first_err = shorten(f"{failures[0][0].name}: {failures[0][1]}", 60) if failures else ""
        if not failures:
            text = f"Saved {outputs[0].name}" if len(outputs) == 1 else f"Saved {len(outputs)} files"
            self.bar(text, "ok", 3500, on_click=reveal)
        elif outputs:
            self.bar(f"Saved {len(outputs)}, {len(failures)} failed: {first_err}", "err", 7000,
                     on_click=reveal)
        elif len(failures) == 1:
            msg = failures[0][1] if len(self.files) == 1 else f"{failures[0][0].name}: {failures[0][1]}"
            self.bar(shorten(msg, 90), "err", 6000)
        else:
            self.bar(f"All {len(failures)} failed: {first_err}", "err", 7000)


def shorten(s: str, n: int) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def reveal_in_explorer(path: Path) -> None:
    if sys.platform == "win32":
        subprocess.Popen(["explorer", "/select,", str(path)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path.parent)])


def rounded_rect(cv: tk.Canvas, x1, y1, x2, y2, r, **kw):
    r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return cv.create_polygon(pts, smooth=True, **kw)


def open_for(paths: list[str | os.PathLike], at=None) -> None:
    """Entry point: show the wheel for the selected file(s), or the
    'nothing available' bar."""
    files = [Path(p) for p in paths if Path(p).is_file()]
    if not files:
        message("Select a file (not a folder) to change its type", at=at)
        return
    targets = converters.shared_targets(files)
    if not targets:
        text = ("No available file types to change to" if len(files) == 1
                else "No file type all of these can change to")
        message(text, at=at)
        return
    Wheel(files, targets, at).run()


def message(text: str, kind: str = "info", at=None) -> None:
    p = Popup(at)
    p.bar(text, kind)
    p.run()
