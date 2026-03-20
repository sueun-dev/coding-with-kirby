import random
import math
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QTimer, QPointF
from utils.macos_window import pin_window_above_mission_control


class Particle:
    def __init__(self, x, y, char, color, size=14):
        self.pos = QPointF(x, y)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 4.0)
        self.vel = QPointF(math.cos(angle) * speed, math.sin(angle) * speed - 2.0)
        self.char = char
        self.color = color
        self.size = size
        self.life = 1.0
        self.decay = random.uniform(0.015, 0.035)

    def update(self):
        self.pos += self.vel
        self.vel.setY(self.vel.y() + 0.08)  # gravity
        self.life -= self.decay
        return self.life > 0


class ParticleOverlay(QWidget):
    """Full-screen transparent overlay that renders particles."""

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
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.particles = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)
        self.show()
        pin_window_above_mission_control(self)

    def emit_eat(self, x, y):
        chars = ["★", "✦", "✧", "⭐", "+XP"]
        colors = [
            QColor(255, 215, 0),
            QColor(255, 165, 0),
            QColor(255, 255, 100),
            QColor(255, 200, 50),
        ]
        for _ in range(8):
            c = random.choice(chars)
            col = random.choice(colors)
            self.particles.append(Particle(x, y, c, col, random.randint(12, 20)))

    def emit_heart(self, x, y):
        for _ in range(5):
            col = QColor(
                random.randint(200, 255),
                random.randint(50, 120),
                random.randint(100, 180),
            )
            self.particles.append(Particle(x, y, "♥", col, random.randint(14, 22)))

    def emit_sleep(self, x, y):
        col = QColor(150, 180, 255, 200)
        p = Particle(x, y, "Z", col, random.randint(16, 24))
        p.vel = QPointF(random.uniform(-0.5, 0.5), -1.5)
        p.decay = 0.01
        self.particles.append(p)

    def emit_achievement(self, x, y):
        chars = ["🏆", "⭐", "✨", "🎉"]
        for _ in range(12):
            c = random.choice(chars)
            col = QColor(255, 215, 0)
            self.particles.append(Particle(x, y, c, col, random.randint(16, 26)))

    def emit_level_up(self, x, y):
        chars = ["▲", "UP!", "★", "LV"]
        colors = [QColor(0, 255, 100), QColor(100, 255, 200), QColor(255, 255, 0)]
        for _ in range(10):
            c = random.choice(chars)
            col = random.choice(colors)
            self.particles.append(Particle(x, y, c, col, random.randint(14, 22)))

    def _tick(self):
        self.particles = [p for p in self.particles if p.update()]
        if self.particles:
            self.update()

    def paintEvent(self, event):
        if not self.particles:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for p in self.particles:
            color = QColor(p.color)
            color.setAlphaF(max(0.0, p.life))
            painter.setPen(color)
            font = QFont("Arial", p.size)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(int(p.pos.x()), int(p.pos.y()), p.char)
