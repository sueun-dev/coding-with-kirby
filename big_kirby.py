import sys
import random
import os
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt, QTimer, QPoint

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class PetWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)  # 마우스 추적 활성화

        self.label = QLabel(self)
        self.right_movie = QMovie(resource_path("y3il.gif"))  # 오른쪽 이동 시 애니메이션 GIF
        self.left_movie = QMovie(resource_path("y3il-reverse.gif"))  # 왼쪽 이동 시 애니메이션 GIF
        self.current_movie = self.right_movie
        self.label.setMovie(self.current_movie)
        self.current_movie.start()

        self.label.resize(self.current_movie.frameRect().size())

        screen = QApplication.primaryScreen().geometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()

        self.resize(self.current_movie.frameRect().width(), self.current_movie.frameRect().height())
        self.direction = QPoint(1, 0)  # 초기 방향
        self.is_facing_right = True
        self.move(random.randint(0, self.screen_width - self.width()),
                  random.randint(0, self.screen_height - self.height()))

        self.show()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.moveStep)
        self.timer.start(50)  # 50ms 마다 움직임

    def moveStep(self):
        new_pos = self.pos() + self.direction * 10  # 현재 위치에서 방향으로 10픽셀 이동

        # 화면 가장자리 도달 시 방향 전환
        if not (0 <= new_pos.x() <= self.screen_width - self.width()):
            self.direction.setX(-self.direction.x())
            self.flipDirection()

        if not (0 <= new_pos.y() <= self.screen_height - self.height()):
            self.direction.setY(-self.direction.y())

        self.move(new_pos)

        # 방향 무작위 변경
        if random.random() < 0.01:  # 1% 확률로 방향 변경
            self.direction = QPoint(random.choice([-1, 0, 1]), random.choice([-1, 0, 1]))
            while self.direction == QPoint(0, 0):  # 정지하지 않도록 함
                self.direction = QPoint(random.choice([-1, 0, 1]), random.choice([-1, 0, 1]))
            self.flipDirection()

    def flipDirection(self):
        self.is_facing_right = self.direction.x() >= 0
        new_movie = self.right_movie if self.is_facing_right else self.left_movie
        if new_movie != self.current_movie:
            self.current_movie.stop()
            self.current_movie = new_movie
            self.label.setMovie(self.current_movie)
            self.current_movie.start()

def main():
    app = QApplication(sys.argv)
    ex = PetWidget()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
