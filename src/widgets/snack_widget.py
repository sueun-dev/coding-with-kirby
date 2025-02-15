import random
from PyQt5.QtWidgets import QLabel, QWidget, QApplication
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from utils.utils import resource_path

class SnackWidget(QWidget):
    """
    Food widget represented by an image.
    Loads one of the food images from the images folder and scales it to 16x16 pixels.
    """
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        try:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            
            food_index = random.randint(1, 7)
            food_image_path = resource_path(f"images/food_{food_index}.png")
            pixmap = QPixmap(food_image_path)
            if pixmap.isNull():
                raise FileNotFoundError(f"Food image not found: {food_image_path}")
            pixmap = pixmap.scaled(16, 16, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            
            self.label = QLabel(self)
            self.label.setPixmap(pixmap)
            self.resize(pixmap.size())
            
            screen = QApplication.primaryScreen().geometry()
            x = random.randint(0, screen.width() - self.width())
            y = random.randint(0, screen.height() - self.height())
            self.move(x, y)
            self.show()
        except Exception as e:
            print("Error in SnackWidget.initUI:", e)
