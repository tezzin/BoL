"""Recording and playback engine for Easy Macro Recorder.

This module has no GUI code. pynput is imported lazily so the data model
and timing logic can be used (and tested) on machines without a display.
"""

import json
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Callable, List, Optional

# Events produced by the recorder. `t` is seconds since recording started.
MOVE = "move"
CLICK = "click"
SCROLL = "scroll"
KEY_DOWN = "key_down"
KEY_UP = "key_up"

FILE_VERSION = 1


@dataclass
class Event:
    kind: str
    t: float
    x: int = 0
    y: int = 0
    button: str = ""      # mouse button name, e.g. "left"
    pressed: bool = False  # for CLICK: True = down, False = up
    dx: int = 0
    dy: int = 0
    key: str = ""          # serialized key, see _key_to_str


@dataclass
class Macro:
    events: List[Event] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return self.events[-1].t if self.events else 0.0

    def to_json(self) -> str:
        return json.dumps(
            {"version": FILE_VERSION, "events": [asdict(e) for e in self.events]},
            indent=1,
        )

    @classmethod
    def from_json(cls, text: str) -> "Macro":
        data = json.loads(text)
        return cls([Event(**e) for e in data.get("events", [])])

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: str) -> "Macro":
        with open(path, encoding="utf-8") as f:
            return cls.from_json(f.read())

    def trim_trailing_click(self) -> None:
        """Drop the final mouse click, i.e. the click on the app's Stop button."""
        for i in range(len(self.events) - 1, -1, -1):
            e = self.events[i]
            if e.kind == CLICK and e.pressed:
                # Remove that press, its release and anything after it.
                del self.events[i:]
                # Also drop the mouse travel towards the Stop button.
                while self.events and self.events[-1].kind == MOVE:
                    self.events.pop()
                return
            if e.kind in (KEY_DOWN, KEY_UP, SCROLL):
                return  # last action wasn't a click; nothing to trim


# ---------------------------------------------------------------- key helpers

def _key_to_str(key) -> str:
    """Serialize a pynput key to a string: 'Key.shift' or 'char:a' or 'vk:65'."""
    from pynput import keyboard

    if isinstance(key, keyboard.Key):
        return "Key." + key.name
    if getattr(key, "char", None):
        return "char:" + key.char
    if getattr(key, "vk", None) is not None:
        return "vk:" + str(key.vk)
    return "char:" + str(key)


def _str_to_key(s: str):
    from pynput import keyboard

    if s.startswith("Key."):
        return getattr(keyboard.Key, s[4:])
    if s.startswith("vk:"):
        return keyboard.KeyCode.from_vk(int(s[3:]))
    return keyboard.KeyCode.from_char(s[5:] if s.startswith("char:") else s)


def key_label(key) -> str:
    """Human friendly name for a pynput key, used for hotkey matching."""
    s = _key_to_str(key)
    return s[4:] if s.startswith("Key.") else s.split(":", 1)[1]


# -------------------------------------------------------------- recording

class Recorder:
    """Captures mouse and keyboard input into a Macro."""

    def __init__(self, record_moves: bool = True, ignore_keys=(),
                 move_interval: float = 0.01):
        self.record_moves = record_moves
        self.ignore_keys = set(ignore_keys)  # labels like "f9", never recorded
        self.move_interval = move_interval   # throttle mouse-move events
        self.macro = Macro()
        self._start = 0.0
        self._last_move = -1.0
        self._lock = threading.Lock()
        self._mouse = None
        self._kb = None
        self.running = False

    def _now(self) -> float:
        return time.perf_counter() - self._start

    def _add(self, ev: Event) -> None:
        with self._lock:
            if self.running:
                self.macro.events.append(ev)

    def start(self) -> None:
        from pynput import keyboard, mouse

        self.macro = Macro()
        self._start = time.perf_counter()
        self._last_move = -1.0
        self.running = True

        def on_move(x, y):
            if not self.record_moves:
                return
            t = self._now()
            if t - self._last_move < self.move_interval:
                return
            self._last_move = t
            self._add(Event(MOVE, t, x=int(x), y=int(y)))

        def on_click(x, y, button, pressed):
            self._add(Event(CLICK, self._now(), x=int(x), y=int(y),
                            button=button.name, pressed=pressed))

        def on_scroll(x, y, dx, dy):
            self._add(Event(SCROLL, self._now(), x=int(x), y=int(y),
                            dx=int(dx), dy=int(dy)))

        def on_press(key):
            if key is None or key_label(key).lower() in self.ignore_keys:
                return
            self._add(Event(KEY_DOWN, self._now(), key=_key_to_str(key)))

        def on_release(key):
            if key is None or key_label(key).lower() in self.ignore_keys:
                return
            self._add(Event(KEY_UP, self._now(), key=_key_to_str(key)))

        self._mouse = mouse.Listener(on_move=on_move, on_click=on_click,
                                     on_scroll=on_scroll)
        self._kb = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._mouse.start()
        self._kb.start()

    def stop(self) -> Macro:
        with self._lock:
            self.running = False
        for listener in (self._mouse, self._kb):
            if listener is not None:
                listener.stop()
        self._mouse = self._kb = None
        return self.macro


# --------------------------------------------------------------- playback

class Player:
    """Replays a Macro a fixed number of times, or forever (repeat=0)."""

    def __init__(self, macro: Macro, repeat: int = 1, speed: float = 1.0,
                 loop_delay: float = 0.0,
                 on_loop: Optional[Callable[[int], None]] = None,
                 on_done: Optional[Callable[[bool], None]] = None,
                 backend=None):
        self.macro = macro
        self.repeat = max(0, int(repeat))
        self.speed = max(0.05, float(speed))
        self.loop_delay = max(0.0, float(loop_delay))
        self.on_loop = on_loop   # called with the 1-based loop number
        self.on_done = on_done   # called with True if stopped by the user
        self._backend = backend
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._held_keys = set()
        self._held_buttons = set()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self._backend is None:
            self._backend = PynputBackend()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def join(self, timeout=None) -> None:
        if self._thread:
            self._thread.join(timeout)

    def _wait(self, seconds: float) -> bool:
        """Sleep, returning True if a stop was requested meanwhile."""
        return self._stop.wait(seconds) if seconds > 0 else self._stop.is_set()

    def _run(self) -> None:
        loop = 0
        try:
            while not self._stop.is_set() and (self.repeat == 0 or loop < self.repeat):
                loop += 1
                if self.on_loop:
                    self.on_loop(loop)
                self._play_once()
                if self._stop.is_set():
                    break
                if self.repeat == 0 or loop < self.repeat:
                    if self._wait(self.loop_delay):
                        break
        finally:
            self._release_held()
            if self.on_done:
                self.on_done(self._stop.is_set())

    def _play_once(self) -> None:
        start = time.perf_counter()
        for ev in self.macro.events:
            target = start + ev.t / self.speed
            if self._wait(target - time.perf_counter()):
                return
            self._dispatch(ev)

    def _dispatch(self, ev: Event) -> None:
        b = self._backend
        if ev.kind == MOVE:
            b.move(ev.x, ev.y)
        elif ev.kind == CLICK:
            b.move(ev.x, ev.y)
            if ev.pressed:
                b.mouse_down(ev.button)
                self._held_buttons.add(ev.button)
            else:
                b.mouse_up(ev.button)
                self._held_buttons.discard(ev.button)
        elif ev.kind == SCROLL:
            b.move(ev.x, ev.y)
            b.scroll(ev.dx, ev.dy)
        elif ev.kind == KEY_DOWN:
            b.key_down(ev.key)
            self._held_keys.add(ev.key)
        elif ev.kind == KEY_UP:
            b.key_up(ev.key)
            self._held_keys.discard(ev.key)

    def _release_held(self) -> None:
        """Never leave a key or button stuck down when playback stops."""
        for k in list(self._held_keys):
            try:
                self._backend.key_up(k)
            except Exception:
                pass
        for btn in list(self._held_buttons):
            try:
                self._backend.mouse_up(btn)
            except Exception:
                pass
        self._held_keys.clear()
        self._held_buttons.clear()


class PynputBackend:
    """Sends real input through pynput."""

    def __init__(self):
        from pynput import keyboard, mouse

        self._mouse_mod = mouse
        self.mouse = mouse.Controller()
        self.keyboard = keyboard.Controller()

    def move(self, x, y):
        self.mouse.position = (x, y)

    def mouse_down(self, button):
        self.mouse.press(getattr(self._mouse_mod.Button, button))

    def mouse_up(self, button):
        self.mouse.release(getattr(self._mouse_mod.Button, button))

    def scroll(self, dx, dy):
        self.mouse.scroll(dx, dy)

    def key_down(self, key):
        self.keyboard.press(_str_to_key(key))

    def key_up(self, key):
        self.keyboard.release(_str_to_key(key))
