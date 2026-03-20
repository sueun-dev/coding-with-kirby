"""
Full-screen transparent particle overlay for visual effects.
"""
import math
import random

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QTimer, QPointF

from utils.macos_window import pin_window_above_mission_control
from utils.utils import PARTICLE_GRAVITY, PARTICLE_DECAY_RANGE, PARTICLE_TICK_MS


class Particle:
    """A single animated character that floats, falls, and fades."""

    __slots__ = ("pos", "vel", "char", "color", "size", "life", "decay")

    def __init__(self, x, y, char, color, size=14):
        self.pos = QPointF(x, y)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 4.0)
        self.vel = QPointF(math.cos(angle) * speed, math.sin(angle) * speed - 2.0)
        self.char = char
        self.color = color
        self.size = size
        self.life = 1.0
        self.decay = random.uniform(*PARTICLE_DECAY_RANGE)

    def update(self):
        self.pos += self.vel
        self.vel.setY(self.vel.y() + PARTICLE_GRAVITY)
        self.life -= self.decay
        return self.life > 0


class ParticleOverlay(QWidget):
    """Full-screen transparent overlay that renders particles."""

    # Preset definitions: (chars, colors, count, size_range)
    _PRESETS = {
        "eat": {
            "chars": ["★", "✦", "✧", "⭐", "+XP"],
            "colors": [
                QColor(255, 215, 0),
                QColor(255, 165, 0),
                QColor(255, 255, 100),
                QColor(255, 200, 50),
            ],
            "count": 8,
            "size_range": (12, 20),
        },
        "heart": {
            "chars": ["♥"],
            "colors": None,  # generated randomly
            "count": 5,
            "size_range": (14, 22),
        },
        "achievement": {
            "chars": ["🏆", "⭐", "✨", "🎉"],
            "colors": [QColor(255, 215, 0)],
            "count": 12,
            "size_range": (16, 26),
        },
        "level_up": {
            "chars": ["▲", "UP!", "★", "LV"],
            "colors": [QColor(0, 255, 100), QColor(100, 255, 200), QColor(255, 255, 0)],
            "count": 10,
            "size_range": (14, 22),
        },
    }

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self._particles: list[Particle] = []

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(PARTICLE_TICK_MS)
        self.show()
        pin_window_above_mission_control(self)

    # --- Public emitters ---

    def emit_preset(self, name, x, y):
        """Emit particles from a named preset."""
        preset = self._PRESETS[name]
        for _ in range(preset["count"]):
            char = random.choice(preset["chars"])
            if preset["colors"] is None:
                color = QColor(
                    random.randint(200, 255),
                    random.randint(50, 120),
                    random.randint(100, 180),
                )
            else:
                color = random.choice(preset["colors"])
            size = random.randint(*preset["size_range"])
            self._particles.append(Particle(x, y, char, color, size))

    def emit_eat(self, x, y):
        self.emit_preset("eat", x, y)

    def emit_heart(self, x, y):
        self.emit_preset("heart", x, y)

    def emit_achievement(self, x, y):
        self.emit_preset("achievement", x, y)

    def emit_level_up(self, x, y):
        self.emit_preset("level_up", x, y)

    def emit_sleep(self, x, y):
        color = QColor(150, 180, 255, 200)
        p = Particle(x, y, "Z", color, random.randint(16, 24))
        p.vel = QPointF(random.uniform(-0.5, 0.5), -1.5)
        p.decay = 0.01
        self._particles.append(p)

    def emit_sweat(self, x, y):
        sweat_offset = 10
        for _ in range(3):
            color = QColor(100, 180, 255, 220)
            p = Particle(
                x + random.randint(-sweat_offset, sweat_offset),
                y - sweat_offset,
                "💧", color, random.randint(10, 16),
            )
            p.vel = QPointF(random.uniform(-0.5, 0.5), random.uniform(1.0, 2.5))
            p.decay = 0.02
            self._particles.append(p)

    def emit_poop(self, x, y):
        color = QColor(139, 90, 43)
        p = Particle(x, y, "💩", color, 18)
        p.vel = QPointF(0, -1.5)
        p.decay = 0.015
        self._particles.append(p)

    # --- Internal ---

    def _tick(self):
        self._particles = [p for p in self._particles if p.update()]
        if self._particles:
            self.update()

    def paintEvent(self, event):
        if not self._particles:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for p in self._particles:
            color = QColor(p.color)
            color.setAlphaF(max(0.0, p.life))
            painter.setPen(color)
            font = QFont("Arial", p.size)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(int(p.pos.x()), int(p.pos.y()), p.char)
