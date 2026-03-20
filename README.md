<div align="center">

# Coding with Kirby

### Your Desktop Companion for Late-Night Coding Sessions

![Kirby](images/Y3il.gif)

**v2.3.0**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-41CD52?style=flat-square)](https://pypi.org/project/PyQt5/)
[![macOS](https://img.shields.io/badge/macOS-Supported-000000?style=flat-square&logo=apple&logoColor=white)](https://www.apple.com/macos/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

---

A physics-driven desktop pet that lives on your screen while you code.
Feed him, throw him, watch him breed — Kirby does his thing while you do yours.

</div>

---

## What is this?

A virtual Kirby that roams your macOS desktop as a transparent overlay. He walks around, gets hungry, eats food, levels up, poops, reacts to your CPU load, and breeds when two Kirbys meet. Everything runs from the macOS menu bar.

---

## Features

### Core
- **Physics-based movement** — Velocity, acceleration, friction, wall bouncing
- **State machine AI** — Wander, idle, rest, chase food, get thrown
- **Hunger & mood system** — Happy, hungry, sleeping, excited
- **XP & leveling** — Quadratic scaling, Kirby grows as he levels
- **9 achievements** — First Bite, Glutton, Star Hunter, Pet Lover, etc.
- **Persistent state** — Auto-saves every 30s, survives restarts
- **Local ranking board** — Compete with friends on the same machine

### Fun Stuff
- **Drag & throw** — Fling Kirby across the screen with momentum physics. He bounces off walls with particle effects
- **Breeding** — When two Kirbys get close, a baby Kirby is born (max 6). Babies are smaller, faster, and chase food independently
- **Poop system** — Kirby poops after eating. Click to clean (+5 XP)
- **Random events** — Trips, finds hidden stars, dances, sneezes, hiccups
- **CPU monitor** — Kirby sweats and complains when CPU > 80%
- **Time-aware greetings** — Different messages for morning, afternoon, evening, late night
- **Colorful emoji food** — Apple, cake, burger, pizza, sushi, ice cream, star candy

### Technical
- **Mission Control compatible** — Kirby stays visible during F3 (uses NSWindow level 25 + Cocoa collection behaviors)
- **Menu bar tray icon** — All controls live in the macOS menu bar
- **Particle system** — Full-screen transparent overlay with eat, heart, sleep, level-up, sweat, and achievement effects
- **Thought bubbles** — Kirby tells you what he's thinking

---

## Quick Start

```bash
git clone https://github.com/sueun-dev/coding-with-kirby.git
cd coding-with-kirby
pip install -r requirements.txt
python3 src/main.py
```

### Dependencies

```
PyQt5
pyobjc-framework-Cocoa
psutil
```

---

## How It Works

| Action | What happens |
|--------|-------------|
| **Left-click tray icon** | Spawn food |
| **Right-click tray icon** | Open menu (stats, feed, pet, ranking, quit) |
| **Click Kirby** | Pet him (+hearts) |
| **Drag & release Kirby** | Throw him (physics momentum) |
| **Click poop** | Clean it (+5 XP) |
| **Two Kirbys meet** | Baby Kirby spawns |
| **Do nothing for 60s** | Kirby falls asleep |
| **Hunger hits 90%** | Food auto-spawns |

---

## Architecture

```
src/
├── main.py                          # Entry point
├── core/
│   └── main_controller.py           # Central game controller
├── widgets/
│   ├── pet_widget.py                # Kirby with state machine + physics
│   ├── snack_widget.py              # Emoji food items
│   ├── poop_widget.py               # Clickable poop
│   ├── thought_bubble.py            # Floating text bubble
│   └── transparent_snackbar.py      # Legacy status bar
├── dialogs/
│   ├── stats_dialog.py              # Achievements dialog
│   └── ranking_board.py             # Leaderboard
└── utils/
    ├── utils.py                     # Constants, food defs, achievements
    ├── particles.py                 # Full-screen particle overlay
    └── macos_window.py              # Cocoa window pinning
```

---

## Build macOS App

```bash
pip install pyinstaller
pyinstaller --windowed --onefile --add-data "images:images" src/main.py
```

The `.app` will be in `dist/`. If macOS blocks it: **System Settings > Privacy & Security > Allow**.

---

## Changelog

### v2.0.0 (2026-03)
- Complete rewrite with physics engine and state machine AI
- Menu bar tray icon (removed floating status bar)
- Drag & throw with momentum
- Breeding system (baby Kirbys)
- Poop system
- Random events (trip, dance, sneeze, hiccup, find star)
- CPU monitor with sweat particles
- Time-based greetings
- Emoji food (replaced black silhouette PNGs)
- Mission Control compatibility
- Achievement system (9 achievements)
- Particle effects (eat, heart, sleep, level-up, sweat, achievement)

### v1.0.0 (2025)
- Initial release with basic movement and food system

---

## Author

**sueun-dev** — [GitHub](https://github.com/sueun-dev) · sueun.dev@gmail.com

---

## License

MIT
