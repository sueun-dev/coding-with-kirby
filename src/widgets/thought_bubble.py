"""Floating thought bubble that follows Kirby and shows text."""

from __future__ import annotations

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QFont, QPainterPath
from PyQt5.QtCore import Qt, QTimer, QRectF

from utils.macos_window import pin_window_above_mission_control
from utils.utils import FADE_TICK_MS

_OPACITY_THRESHOLD = 0.01
_FADE_RATE = 0.15


class ThoughtBubble(QWidget):
    """A floating thought bubble that follows Kirby and shows his mood."""

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
        self.resize(160, 60)
        self._text = ""
        self._opacity = 0.0
        self._target_opacity = 0.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._fade_tick)
        self._timer.start(FADE_TICK_MS)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.fade_out)

        self._screen = QApplication.primaryScreen().geometry()
        self.show()
        pin_window_above_mission_control(self)

    def stop(self):
        """Stop all timers for clean shutdown."""
        self._timer.stop()
        self._hide_timer.stop()

    def show_text(self, text, duration_ms=3000):
        self._text = text
        self._target_opacity = 1.0
        self._hide_timer.stop()
        self._hide_timer.start(duration_ms)
        self.update()

    def fade_out(self):
        self._target_opacity = 0.0

    def follow(self, x, y):
        """Follow Kirby, clamped to screen bounds."""
        bx = max(0, min(x - 20, self._screen.width() - self.width()))
        by = max(0, min(y - 65, self._screen.height() - self.height()))
        self.move(int(bx), int(by))

    def _fade_tick(self):
        diff = self._target_opacity - self._opacity
        if abs(diff) > _OPACITY_THRESHOLD:
            self._opacity += diff * _FADE_RATE
            self.update()
        elif diff != 0:
            self._opacity = self._target_opacity
            self.update()

    def paintEvent(self, event):
        if self._opacity < _OPACITY_THRESHOLD:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(self._opacity)

        # Bubble body
        path = QPainterPath()
        bubble_rect = QRectF(5, 5, self.width() - 10, self.height() - 20)
        path.addRoundedRect(bubble_rect, 12, 12)
        painter.fillPath(path, QColor(255, 255, 255, 220))
        painter.setPen(QColor(180, 180, 180))
        painter.drawPath(path)

        # Small circles for tail
        painter.setBrush(QColor(255, 255, 255, 220))
        painter.drawEllipse(25, self.height() - 18, 10, 10)
        painter.drawEllipse(20, self.height() - 8, 6, 6)

        # Text
        painter.setPen(QColor(60, 60, 60))
        font = QFont("Arial", 11)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(bubble_rect, Qt.AlignCenter, self._text)
