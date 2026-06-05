"""Poop widget left behind by Kirby after eating."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QLabel, QWidget
from PyQt5.QtGui import QFont, QMouseEvent
from PyQt5.QtCore import Qt

from utils.macos_window import pin_window_above_mission_control

if TYPE_CHECKING:
    from core.main_controller import MainController


class PoopWidget(QWidget):
    """Clickable poop left behind by Kirby. Click to clean for XP."""

    def __init__(self, x: float, y: float, controller: "MainController") -> None:
        super().__init__()
        self.controller = controller
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.label = QLabel("💩", self)
        self.label.setFont(QFont("Apple Color Emoji", 18))
        self.label.setAlignment(Qt.AlignCenter)
        self.label.adjustSize()
        self.resize(self.label.size())
        self.move(int(x), int(y))
        self.show()
        pin_window_above_mission_control(self)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self.controller.clean_poop(self)
