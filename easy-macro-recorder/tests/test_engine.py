import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from macro_engine import CLICK, KEY_DOWN, KEY_UP, MOVE, Event, Macro, Player


class FakeBackend:
    def __init__(self):
        self.calls = []

    def move(self, x, y):
        self.calls.append(("move", x, y))

    def mouse_down(self, b):
        self.calls.append(("down", b))

    def mouse_up(self, b):
        self.calls.append(("up", b))

    def scroll(self, dx, dy):
        self.calls.append(("scroll", dx, dy))

    def key_down(self, k):
        self.calls.append(("kd", k))

    def key_up(self, k):
        self.calls.append(("ku", k))


def sample():
    return Macro([
        Event(MOVE, 0.0, x=10, y=20),
        Event(CLICK, 0.01, x=10, y=20, button="left", pressed=True),
        Event(CLICK, 0.02, x=10, y=20, button="left", pressed=False),
        Event(KEY_DOWN, 0.03, key="char:a"),
        Event(KEY_UP, 0.04, key="char:a"),
    ])


def run(player):
    done = []
    player.on_done = done.append
    player.start()
    player.join(5)
    return done


def test_json_roundtrip():
    m = sample()
    m2 = Macro.from_json(m.to_json())
    assert m2.events == m.events
    assert m2.duration == 0.04


def test_repeat_n_times():
    be = FakeBackend()
    loops = []
    p = Player(sample(), repeat=3, speed=10, backend=be, on_loop=loops.append)
    assert run(p) == [False]
    assert loops == [1, 2, 3]
    assert be.calls.count(("kd", "char:a")) == 3
    assert be.calls.count(("down", "left")) == 3


def test_continuous_until_stopped():
    be = FakeBackend()
    loops = []
    p = Player(sample(), repeat=0, speed=10, backend=be, on_loop=loops.append)
    p.start()
    time.sleep(0.1)
    p.stop()
    p.join(5)
    assert len(loops) > 3
    assert not p.running


def test_timing_respects_speed():
    m = Macro([Event(KEY_DOWN, 0.0, key="char:x"), Event(KEY_UP, 0.2, key="char:x")])
    t = time.perf_counter()
    run(Player(m, repeat=1, speed=2, backend=FakeBackend()))
    assert 0.08 < time.perf_counter() - t < 0.3


def test_stop_releases_held_keys_and_buttons():
    m = Macro([
        Event(KEY_DOWN, 0.0, key="Key.shift"),
        Event(CLICK, 0.0, button="left", pressed=True),
        Event(KEY_UP, 5.0, key="Key.shift"),
    ])
    be = FakeBackend()
    p = Player(m, repeat=1, backend=be)
    p.start()
    time.sleep(0.05)
    p.stop()
    p.join(5)
    assert ("ku", "Key.shift") in be.calls
    assert ("up", "left") in be.calls


def test_stop_before_start_still_finishes():
    p = Player(sample(), repeat=1, backend=FakeBackend())
    p.stop()
    assert run(p) == [True]


def test_trim_trailing_click():
    m = sample()
    m.events += [Event(MOVE, 0.05, x=1, y=1),
                 Event(CLICK, 0.06, button="left", pressed=True),
                 Event(CLICK, 0.07, button="left", pressed=False)]
    m.trim_trailing_click()
    assert m.events == sample().events
    # Last action is a key, so nothing is trimmed.
    m2 = sample()
    m2.trim_trailing_click()
    assert m2.events == sample().events
