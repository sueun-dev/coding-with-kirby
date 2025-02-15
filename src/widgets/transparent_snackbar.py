from PyQt5.QtWidgets import QWidget, QPushButton
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt
from dialogs.ranking_board import RankingBoard

class TransparentSnackBar(QWidget):
    """
    A semi-transparent widget at the top-left of the screen.
    Spans 800 pixels in width and displays:
      - "Food" on the far left,
      - "I'm hungry: {hunger}%" in the center,
      - Kirby's size and level on the right.
    Also has "Ranking" and "Quit" buttons.
    Clicking the bar spawns a new food item.
    """
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.initUI()

    def initUI(self):
        try:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setGeometry(10, 10, 800, 30)
            
            self.ranking_button = QPushButton("Ranking", self)
            self.ranking_button.setGeometry(650, 5, 70, 20)
            self.ranking_button.setStyleSheet("background-color: transparent; color: white; border: none;")
            self.ranking_button.clicked.connect(self.show_ranking)
            
            self.quit_button = QPushButton("Quit", self)
            self.quit_button.setGeometry(730, 5, 60, 20)
            self.quit_button.setStyleSheet("background-color: transparent; color: white; border: none;")
            self.quit_button.clicked.connect(lambda: self.controller.app.quit())
            
            self.show()
        except Exception as e:
            print("Error in TransparentSnackBar.initUI:", e)

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            background_color = QColor(50, 50, 50, 150)
            painter.fillRect(self.rect(), background_color)
            painter.setPen(Qt.white)
            painter.drawText(5, 0, 150, 30, Qt.AlignLeft | Qt.AlignVCenter, "Food")
            painter.drawText(155, 0, 300, 30, Qt.AlignCenter, f"I'm hungry: {self.controller.hunger}%")
            size_percent = round(self.controller.pet.scale_factor * 100, 1)
            level = int((self.controller.pet.scale_factor - 1.0) * 1000)
            painter.drawText(455, 0, 180, 30, Qt.AlignCenter, f"Size: {size_percent}%  Level: {level}")
        except Exception as e:
            print("Error in TransparentSnackBar.paintEvent:", e)

    def mousePressEvent(self, event):
        try:
            self.controller.spawn_snack()
        except Exception as e:
            print("Error in TransparentSnackBar.mousePressEvent:", e)

    def show_ranking(self):
        try:
            ranking_board = RankingBoard(self)
            ranking_board.exec_()
        except Exception as e:
            print("Error in TransparentSnackBar.show_ranking:", e)
