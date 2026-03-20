<div align="center">

# Coding with Kirby

### Your Desktop Companion for Late-Night Coding Sessions

![Kirby](images/Y3il.gif)

**v2.3.0**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-41CD52?style=flat-square)](https://pypi.org/project/PyQt5/)
[![macOS](https://img.shields.io/badge/macOS-Supported-000000?style=flat-square&logo=apple&logoColor=white)](https://www.apple.com/macos/)
[![Tests](https://img.shields.io/badge/Tests-135%20passed-brightgreen?style=flat-square)](tests/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

---

A physics-driven desktop pet that lives on your screen while you code.
Feed him, throw him, watch him breed — Kirby does his thing while you do yours.

</div>

---

## What is this?

A virtual Kirby that roams your macOS desktop as a transparent overlay. He walks around, gets hungry, eats food, levels up, poops, reacts to your CPU load, and breeds when two Kirbys meet. Everything runs from the macOS menu bar.

No browser, no Electron, no web tech — just a lightweight PyQt5 widget floating on your screen.

---

## Getting Started

### With uv (recommended)

```bash
git clone https://github.com/sueun-dev/coding-with-kirby.git
cd coding-with-kirby

# Install dependencies
uv sync

# Run
uv run python src/main.py

# Run tests
uv run pytest
```

### With pip

```bash
git clone https://github.com/sueun-dev/coding-with-kirby.git
cd coding-with-kirby

# Install dependencies
pip install -r requirements.txt

# Run
python3 src/main.py

# Run tests
python3 -m pytest
```

> **Note:** macOS only. Requires Python 3.9+. Kirby uses Cocoa APIs to stay visible during Mission Control (F3).

---

## Features

### Core
- **Physics-based movement** — Velocity, acceleration, friction, wall bouncing
- **State machine AI** — Wander, idle, rest, chase food, get thrown
- **Hunger & mood system** — Happy, hungry, sleeping, excited
- **XP & leveling** — Exponential scaling, Kirby grows physically as he levels up
- **9 achievements** — First Bite, Glutton, Star Hunter, Pet Lover, and more
- **Persistent state** — Auto-saves every 30s with atomic writes, survives restarts
- **Local ranking board** — Compete with friends on the same machine

### Fun Stuff
- **Drag & throw** — Fling Kirby across the screen with real momentum physics. He bounces off walls with particle effects
- **Breeding** — When two Kirbys get close, a baby Kirby is born (max 6). Babies are smaller, faster, and chase food on their own
- **Poop system** — Kirby poops after eating. Click to clean for +5 XP
- **Random events** — Trips, finds hidden stars, dances, sneezes, hiccups
- **CPU monitor** — Kirby sweats and complains when your CPU goes above 80%
- **Time-aware greetings** — Different messages for morning, afternoon, evening, and late night
- **Colorful emoji food** — Apple, cake, burger, pizza, sushi, ice cream, star candy

### Technical
- **Mission Control compatible** — Kirby stays visible during F3, Spaces, and full-screen apps
- **Menu bar tray icon** — All controls live in the macOS menu bar. Left-click to feed, right-click for full menu
- **Particle system** — Full-screen transparent overlay with eat, heart, sleep, level-up, sweat, and achievement effects
- **Thought bubbles** — Kirby tells you what he's thinking with smooth fade-in/out
- **Zero magic numbers** — All tuning constants are named and centralized in `utils.py`

---

## How to Play

| Action | What happens |
|--------|-------------|
| **Left-click tray icon** | Spawn food |
| **Right-click tray icon** | Open menu (stats, feed, pet, ranking, quit) |
| **Click Kirby** | Pet him (hearts + XP toward Pet Lover achievement) |
| **Drag & release Kirby** | Throw him (momentum-based physics with wall bouncing) |
| **Click poop** | Clean it (+5 XP) |
| **Two Kirbys meet** | Baby Kirby spawns (+30 XP) |
| **Do nothing for 60s** | Kirby falls asleep (Zzz particles) |
| **Hunger hits 90%** | Food auto-spawns so Kirby doesn't starve |

---

## Project Structure

```
coding-with-kirby/
├── src/
│   ├── main.py                    # Entry point
│   ├── core/
│   │   └── main_controller.py     # Central game controller (state, tray, timers)
│   ├── widgets/
│   │   ├── pet_widget.py          # Kirby: state machine AI + physics engine
│   │   ├── snack_widget.py        # Emoji food items
│   │   ├── poop_widget.py         # Clickable poop
│   │   └── thought_bubble.py      # Floating text bubble with fade
│   ├── dialogs/
│   │   ├── stats_dialog.py        # Achievements dialog
│   │   └── ranking_board.py       # Leaderboard with auto-refresh
│   └── utils/
│       ├── utils.py               # All constants, validators, JSON I/O
│       ├── particles.py           # Full-screen particle overlay (6 presets)
│       └── macos_window.py        # Cocoa window pinning for Mission Control
├── tests/
│   ├── test_utils.py              # Constants, validators, JSON I/O (33 tests)
│   ├── test_game_logic.py         # XP, hunger, mood, achievements (40 tests)
│   ├── test_physics.py            # Velocity, bounce, throw, friction (29 tests)
│   └── test_bugfixes.py           # Regression tests for past bugs (33 tests)
├── images/
│   ├── Y3il.gif                   # Kirby walking right
│   └── Y3il-reverse.gif           # Kirby walking left
├── pyproject.toml                 # Project config (deps, pytest, pyright)
├── requirements.txt               # Pip-compatible dependency list
└── main.spec                      # PyInstaller build config
```

---

## Build macOS App

```bash
# With uv
uv run pyinstaller main.spec

# With pip
pip install pyinstaller
pyinstaller main.spec
```

The `.app` bundle will be in `dist/`. If macOS blocks it: **System Settings > Privacy & Security > Allow**.

---

## Running Tests

```bash
# 135 tests covering game logic, physics, utilities, and bug regressions
uv run pytest -v

# Or with pip
python3 -m pytest -v
```

---

## Changelog

### v2.3.0
- Full Google Python Style Guide compliance audit
- Type annotations on all public functions
- Replaced all magic numbers with named constants
- Fixed `_bounce()` using hardcoded values instead of constants
- Added `pyproject.toml` with proper project metadata
- 135 tests (7 new constant-validation tests)

### v2.2.0
- Fixed NaN/Inf `scale_factor` crash in state validation
- XP infinite loop safety guard (max 50 level-ups per tick)
- Breeding limit re-check before spawning baby
- Baby spawn position clamped to screen bounds
- Particle emission cap on all emitters
- `stop()` methods on all widgets for clean shutdown
- Snack spawn bounds safe on tiny screens
- 26 regression tests added

### v2.1.0
- Comprehensive test suite (102 tests)
- Code cleanup and import fixes
- Bug fixes from initial test run

### v2.0.0
- Complete rewrite with physics engine and state machine AI
- Menu bar tray icon (removed floating status bar)
- Drag & throw with momentum
- Breeding system (baby Kirbys)
- Poop system, random events, CPU monitor
- Mission Control compatibility via Cocoa APIs
- Achievement system, particle effects, thought bubbles
- Emoji food (replaced black silhouette PNGs)

### v1.0.0
- Initial release with basic movement and food system

---

## Author

**sueun-dev** — [GitHub](https://github.com/sueun-dev)

---

## License

MIT
