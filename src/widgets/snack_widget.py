import random
from PyQt5.QtWidgets import QLabel, QWidget, QApplication
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from utils.utils import resource_path, FOODS
from utils.macos_window import pin_window_above_mission_control


class SnackWidget(QWidget):
    """Food widget that spawns at a random screen position."""

    def __init__(self, food_def=None):
        super().__init__()
        if food_def is None:
            food_def = random.choice(FOODS)
        self.food_index, self.food_name, self.hunger_restore, self.xp_reward = food_def
        self._init_ui()

    def _init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        pixmap = QPixmap(resource_path(f"images/food_{self.food_index}.png"))
        if pixmap.isNull():
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.red)
        pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.label = QLabel(self)
        self.label.setPixmap(pixmap)
        self.resize(pixmap.size())

        screen = QApplication.primaryScreen().geometry()
        margin = 60
        x = random.randint(margin, screen.width() - self.width() - margin)
        y = random.randint(margin, screen.height() - self.height() - margin)
        self.move(x, y)
        self.show()
        pin_window_above_mission_control(self)
