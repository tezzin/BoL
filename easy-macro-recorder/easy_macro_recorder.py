"""Easy Macro Recorder: record mouse + keyboard input and play it back.

Run:  python easy_macro_recorder.py
Hotkeys (work even when the window is not focused):
    F9   start / stop recording
    F10  start / stop playback
"""

import os
import queue
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from macro_engine import Macro, Player, Recorder, key_label

APP_NAME = "Easy Macro Recorder"
RECORD_HOTKEY = "f9"
PLAY_HOTKEY = "f10"

# Palette
BG = "#f5f6f8"
CARD = "#ffffff"
TEXT = "#1f2328"
MUTED = "#6b7280"
RED = "#e5484d"
GREEN = "#30a46c"
BLUE = "#3b82f6"
GRAY = "#9ca3af"


def enable_dpi_awareness():
    """Make recorded coordinates match real pixels on scaled Windows displays."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.macro = Macro()
        self.recorder = None
        self.player = None
        self.ui_queue = queue.Queue()  # work posted from listener threads
        self.file_path = None

        root.title(APP_NAME)
        root.configure(bg=BG)
        root.resizable(False, False)
        root.attributes("-topmost", True)

        self._build_styles()
        self._build_ui()
        self._start_hotkeys()
        self._refresh()
        root.after(50, self._drain_queue)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------- layout

    def _build_styles(self):
        s = ttk.Style()
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        base = ("Segoe UI", 10)
        s.configure(".", background=BG, foreground=TEXT, font=base)
        s.configure("Card.TFrame", background=CARD)
        s.configure("Card.TLabel", background=CARD, foreground=TEXT)
        s.configure("Muted.TLabel", background=CARD, foreground=MUTED, font=("Segoe UI", 9))
        s.configure("Hint.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))
        s.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Segoe UI Semibold", 15))
        s.configure("Card.TRadiobutton", background=CARD, foreground=TEXT)
        s.configure("Card.TCheckbutton", background=CARD, foreground=TEXT)
        s.map("Card.TRadiobutton", background=[("active", CARD)])
        s.map("Card.TCheckbutton", background=[("active", CARD)])
        s.configure("TSpinbox", arrowsize=12, padding=3)

        for name, color in (("Record", RED), ("Play", GREEN), ("Stop", TEXT)):
            s.configure(f"{name}.TButton", background=color, foreground="white",
                        font=("Segoe UI Semibold", 11), padding=(14, 10),
                        borderwidth=0, focuscolor=color)
            s.map(f"{name}.TButton",
                  background=[("disabled", "#d1d5db"), ("active", color)],
                  foreground=[("disabled", "#f3f4f6")])
        s.configure("Small.TButton", padding=(10, 5), background="#e5e7eb", borderwidth=0)
        s.map("Small.TButton", background=[("active", "#d1d5db")])

    def _card(self, parent, title):
        outer = ttk.Frame(parent, style="Card.TFrame", padding=14)
        outer.pack(fill="x", pady=(0, 10))
        ttk.Label(outer, text=title.upper(), style="Muted.TLabel").pack(anchor="w", pady=(0, 6))
        return outer

    def _build_ui(self):
        wrap = ttk.Frame(self.root, padding=16)
        wrap.pack(fill="both", expand=True)

        ttk.Label(wrap, text=APP_NAME, style="Title.TLabel").pack(anchor="w", pady=(0, 10))

        # Status + main controls
        card = self._card(wrap, "Status")
        status_row = ttk.Frame(card, style="Card.TFrame")
        status_row.pack(fill="x")
        self.dot = tk.Canvas(status_row, width=14, height=14, bg=CARD, highlightthickness=0)
        self.dot.pack(side="left", padx=(0, 8))
        self.dot_id = self.dot.create_oval(2, 2, 12, 12, fill=GRAY, outline="")
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_row, textvariable=self.status_var, style="Card.TLabel",
                  font=("Segoe UI Semibold", 12)).pack(side="left")
        self.info_var = tk.StringVar()
        ttk.Label(card, textvariable=self.info_var, style="Muted.TLabel").pack(anchor="w", pady=(4, 12))

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.pack(fill="x")
        self.rec_btn = ttk.Button(btns, text="●  Record", style="Record.TButton",
                                  command=self.toggle_record)
        self.play_btn = ttk.Button(btns, text="▶  Play", style="Play.TButton",
                                   command=self.toggle_play)
        self.stop_btn = ttk.Button(btns, text="■  Stop", style="Stop.TButton",
                                   command=self.stop_from_button)
        for i, b in enumerate((self.rec_btn, self.play_btn, self.stop_btn)):
            b.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 6, 0))
            btns.columnconfigure(i, weight=1)

        # Repeat settings
        card = self._card(wrap, "Playback")
        self.mode_var = tk.StringVar(value="times")
        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill="x", pady=2)
        ttk.Radiobutton(row, text="Repeat", value="times", variable=self.mode_var,
                        style="Card.TRadiobutton", command=self._refresh).pack(side="left")
        self.times_var = tk.IntVar(value=1)
        self.times_spin = ttk.Spinbox(row, from_=1, to=1_000_000, width=7,
                                      textvariable=self.times_var)
        self.times_spin.pack(side="left", padx=6)
        ttk.Label(row, text="times", style="Card.TLabel").pack(side="left")

        ttk.Radiobutton(card, text="Repeat continuously (until you press Stop / F10)",
                        value="loop", variable=self.mode_var, style="Card.TRadiobutton",
                        command=self._refresh).pack(anchor="w", pady=2)

        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill="x", pady=(8, 0))
        ttk.Label(row, text="Speed", style="Card.TLabel").pack(side="left")
        self.speed_var = tk.StringVar(value="1.0")
        ttk.Spinbox(row, values=("0.25", "0.5", "0.75", "1.0", "1.5", "2.0", "3.0", "5.0"),
                    width=5, textvariable=self.speed_var).pack(side="left", padx=(6, 2))
        ttk.Label(row, text="x", style="Card.TLabel").pack(side="left")
        ttk.Label(row, text="Pause between repeats", style="Card.TLabel").pack(side="left", padx=(16, 0))
        self.delay_var = tk.StringVar(value="0")
        ttk.Spinbox(row, from_=0, to=3600, increment=0.5, width=5,
                    textvariable=self.delay_var).pack(side="left", padx=(6, 2))
        ttk.Label(row, text="s", style="Card.TLabel").pack(side="left")

        # Recording options
        card = self._card(wrap, "Recording")
        self.moves_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, text="Record mouse movement (not just clicks)",
                        variable=self.moves_var, style="Card.TCheckbutton").pack(anchor="w")
        self.hide_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card, text="Minimize this window while recording / playing",
                        variable=self.hide_var, style="Card.TCheckbutton").pack(anchor="w", pady=(2, 0))

        files = ttk.Frame(card, style="Card.TFrame")
        files.pack(fill="x", pady=(10, 0))
        ttk.Button(files, text="Open…", style="Small.TButton", command=self.open_macro).pack(side="left")
        ttk.Button(files, text="Save…", style="Small.TButton", command=self.save_macro).pack(side="left", padx=6)
        ttk.Button(files, text="Clear", style="Small.TButton", command=self.clear_macro).pack(side="left")

        ttk.Label(wrap, text=f"Hotkeys:  {RECORD_HOTKEY.upper()} record / stop     "
                             f"{PLAY_HOTKEY.upper()} play / stop",
                  style="Hint.TLabel").pack(anchor="w")

    # ------------------------------------------------------------ hotkeys

    def _start_hotkeys(self):
        from pynput import keyboard

        def on_press(key):
            if key is None:
                return
            label = key_label(key).lower()
            if label == RECORD_HOTKEY:
                self.ui_queue.put(self.toggle_record)
            elif label == PLAY_HOTKEY:
                self.ui_queue.put(self.toggle_play)

        self.hotkeys = keyboard.Listener(on_press=on_press)
        self.hotkeys.daemon = True
        self.hotkeys.start()

    def _drain_queue(self):
        try:
            while True:
                self.ui_queue.get_nowait()()
        except queue.Empty:
            pass
        self.root.after(50, self._drain_queue)

    # ------------------------------------------------------------ actions

    def toggle_record(self):
        if self.recorder:
            self.stop_recording(trim_click=False)
        elif not self.player:
            self.start_recording()

    def start_recording(self):
        self.recorder = Recorder(record_moves=self.moves_var.get(),
                                 ignore_keys={RECORD_HOTKEY, PLAY_HOTKEY})
        self.recorder.start()
        if self.hide_var.get():
            self.root.iconify()
        self._refresh()

    def stop_recording(self, trim_click):
        macro = self.recorder.stop()
        self.recorder = None
        if trim_click:
            macro.trim_trailing_click()
        self.macro = macro
        self.file_path = None
        self.root.deiconify()
        self._refresh()

    def toggle_play(self):
        if self.player:
            self.player.stop()
        elif not self.recorder:
            self.start_playback()

    def start_playback(self):
        if not self.macro.events:
            messagebox.showinfo(APP_NAME, "Nothing recorded yet. Press Record first.")
            return
        try:
            repeat = 0 if self.mode_var.get() == "loop" else max(1, int(self.times_var.get()))
            speed = float(self.speed_var.get())
            delay = float(self.delay_var.get())
        except (ValueError, tk.TclError):
            messagebox.showerror(APP_NAME, "Repeat, speed and pause must be numbers.")
            return

        def on_loop(n):
            total = "∞" if repeat == 0 else str(repeat)
            self.ui_queue.put(lambda: self._set_status(f"Playing  ·  loop {n} of {total}", GREEN))

        def on_done(_stopped):
            self.ui_queue.put(self._playback_finished)

        self.player = Player(self.macro, repeat=repeat, speed=speed, loop_delay=delay,
                             on_loop=on_loop, on_done=on_done)
        self._refresh()
        if self.hide_var.get():
            self.root.iconify()
        # Small head start so the click on Play has finished before replay begins.
        self.root.after(300, self.player.start)

    def _playback_finished(self):
        self.player = None
        self.root.deiconify()
        self._refresh()

    def stop_from_button(self):
        if self.recorder:
            self.stop_recording(trim_click=True)
        elif self.player:
            self.player.stop()

    def open_macro(self):
        if self.recorder or self.player:
            return
        path = filedialog.askopenfilename(filetypes=[("Macro files", "*.macro.json *.json"),
                                                     ("All files", "*.*")])
        if not path:
            return
        try:
            self.macro = Macro.load(path)
            self.file_path = path
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"Could not open macro:\n{exc}")
        self._refresh()

    def save_macro(self):
        if not self.macro.events:
            messagebox.showinfo(APP_NAME, "Nothing to save yet.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".macro.json",
                                            filetypes=[("Macro files", "*.macro.json")])
        if path:
            self.macro.save(path)
            self.file_path = path
            self._refresh()

    def clear_macro(self):
        if self.recorder or self.player:
            return
        self.macro = Macro()
        self.file_path = None
        self._refresh()

    # -------------------------------------------------------------- state

    def _set_status(self, text, color):
        self.status_var.set(text)
        self.dot.itemconfigure(self.dot_id, fill=color)

    def _refresh(self):
        busy = bool(self.recorder or self.player)
        if self.recorder:
            self._set_status("Recording…  press Stop or F9 to finish", RED)
        elif self.player:
            self._set_status("Playing…", GREEN)
        elif self.macro.events:
            self._set_status("Ready to play", BLUE)
        else:
            self._set_status("Ready", GRAY)

        n = len(self.macro.events)
        info = f"{n} events  ·  {self.macro.duration:.1f} s" if n else "No macro recorded yet"
        if self.file_path:
            info += f"  ·  {os.path.basename(self.file_path)}"
        self.info_var.set(info)

        self.rec_btn.state(["disabled"] if busy else ["!disabled"])
        self.play_btn.state(["disabled"] if busy or not n else ["!disabled"])
        self.stop_btn.state(["!disabled"] if busy else ["disabled"])
        self.times_spin.state(["disabled"] if self.mode_var.get() == "loop" else ["!disabled"])

    def _on_close(self):
        if self.player:
            self.player.stop()
        if self.recorder:
            self.recorder.stop()
        self.root.destroy()


def main():
    enable_dpi_awareness()
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
