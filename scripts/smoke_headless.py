"""Headless end-to-end smoke test for Coding with Kirby.

Runs the real MainController + widgets under Qt's offscreen platform,
exercises the core game systems, and asserts no exceptions. This is the
"run it" harness used during refactoring — not a unit test.

Usage:  QT_QPA_PLATFORM=offscreen python scripts/smoke_headless.py
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PyQt5.QtWidgets import QApplication, QInputDialog
from PyQt5.QtCore import QPointF

# The macOS Cocoa window-pinning path operates on a native NSView handle.
# Under the offscreen Qt platform that handle is not an NSView, so stub it
# out before any widget module binds the name. (We exercise game logic here,
# not Cocoa integration.)
import utils.macos_window as _macos_window

_macos_window.pin_window_above_mission_control = lambda *a, **k: None


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Avoid the blocking username prompt.
    QInputDialog.getText = staticmethod(lambda *a, **k: ("SmokeTester", True))

    from core.main_controller import MainController

    ctrl = MainController(app)
    checks: list[str] = []

    def ok(label: str, cond: bool) -> None:
        checks.append(label)
        if not cond:
            raise AssertionError(f"FAILED: {label}")

    # --- Food + eating ---
    ctrl.spawn_snack()
    ok("snack spawned", len(ctrl.snacks) == 1)
    snack = ctrl.snacks[0]
    ctrl._eat(snack)
    ok("snack consumed", len(ctrl.snacks) == 0)
    ok("eat counted", ctrl.total_eats == 1)
    ok("first_bite achievement", "first_bite" in ctrl.unlocked_achievements)

    # --- XP / leveling ---
    lvl_before = ctrl.level
    ctrl._add_xp(100_000)
    ok("leveled up", ctrl.level > lvl_before)
    ok("scale grew", ctrl.pet.scale_factor > 0)

    # --- Petting ---
    ctrl.pet_kirby()
    ok("pet counted", ctrl.total_pets == 1)

    # --- Mood / hunger ticks ---
    for _ in range(5):
        ctrl._hunger_tick()
    ctrl._mood_tick()
    ok("mood is a known value", ctrl.mood in ("happy", "hungry", "sleeping", "excited"))

    # --- Poop ---
    ctrl._spawn_poop()
    ok("poop spawned", len(ctrl.poops) == 1)
    ctrl.clean_poop(ctrl.poops[0])
    ok("poop cleaned", len(ctrl.poops) == 0)

    # --- Random events (exercise each) ---
    ctrl._event_trip()
    ctrl._event_find_star()
    ctrl._event_dance()
    ctrl._event_sneeze()
    ctrl._event_hiccup()
    ok("events ran", True)

    # --- Pet physics tick ---
    ctrl.pet.vel = QPointF(5.0, -3.0)
    for _ in range(10):
        ctrl.pet._tick()
    ok("pet ticked without error", True)

    # --- Breeding ---
    # Place two pets close, force-breed.
    ctrl.pet.pos_f = QPointF(100, 100)
    ctrl.pet.move(100, 100)
    ctrl._breed(ctrl.pet, ctrl.pet)
    ok("baby spawned", len(ctrl.extra_pets) == 1)

    # --- CPU monitor ---
    ctrl._cpu_tick()
    ok("cpu tick ran", isinstance(ctrl._cpu_percent, float))

    # --- Persistence round-trip ---
    ctrl.save_state()
    ok("state file written", os.path.exists("kirby_state.json"))
    saved_level = ctrl.level
    ctrl.level = 1
    ctrl._load_state()
    ok("state reloaded", ctrl.level == saved_level)

    # --- Robustness: corrupted state file must not crash loading ---
    import json
    with open("kirby_state.json", "w", encoding="utf-8") as fh:
        json.dump(
            {"hunger": "abc", "level": "x", "achievements": {"first_bite": True}}, fh
        )
    ctrl._load_state()  # must not raise
    ok("load tolerates corrupted state", True)

    # --- Robustness: malformed ranking.json must not crash the board ---
    from dialogs.ranking_board import RankingBoard
    with open("ranking.json", "w", encoding="utf-8") as fh:
        json.dump(
            ["garbage", {"username": "x", "level": None}, {"username": "y", "level": 3}],
            fh,
        )
    board = RankingBoard()
    board._refresh()  # must not raise on non-dict rows / null level
    board._timer.stop()
    board.close()
    ok("ranking board tolerates malformed data", True)

    # --- Clean shutdown ---
    ctrl.stop_all_timers()
    for s in ctrl.snacks:
        s.close()
    for p in ctrl.poops:
        p.close()
    ok("shutdown clean", True)

    print(f"SMOKE OK — {len(checks)} checks passed:")
    for c in checks:
        print(f"  - {c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
