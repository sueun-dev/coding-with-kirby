from PyQt5.QtWidgets import QLabel, QWidget
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from utils.macos_window import pin_window_above_mission_control


class PoopWidget(QWidget):
    """Poop left behind by Kirby. Click to clean."""

    def __init__(self, x, y, controller):
        super().__init__()
        self.controller = controller
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.label = QLabel("\U0001F4A9", self)
        self.label.setFont(QFont("Apple Color Emoji", 18))
        self.label.setAlignment(Qt.AlignCenter)
        self.label.adjustSize()
        self.resize(self.label.size())
        self.move(int(x), int(y))
        self.show()
        pin_window_above_mission_control(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.controller.clean_poop(self)
