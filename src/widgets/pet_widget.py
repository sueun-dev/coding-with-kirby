import random
import math
from PyQt5.QtWidgets import QLabel, QWidget, QApplication
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt, QTimer, QPointF
from utils.utils import resource_path

class PetWidget(QWidget):
    """
    Kirby widget that moves using QMovie animation.
    Uses floating-point positions for smooth movement and handles level-up (growth).
    """
    def __init__(self, controller):
        super().__init__()
        self.controller = controller  # Reference to MainController.
        self.scale_factor = 1.0       # Current growth factor.
        self.initUI()

    def initUI(self):
        try:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setMouseTracking(True)

            self.label = QLabel(self)
            self.right_movie = QMovie(resource_path("images/y3il.gif"))
            self.left_movie = QMovie(resource_path("images/y3il-reverse.gif"))
            self.current_movie = self.right_movie
            self.label.setMovie(self.current_movie)
            self.current_movie.start()
            self.label.setScaledContents(True)
            self.label.resize(self.current_movie.frameRect().size())

            screen_geom = QApplication.primaryScreen().geometry()
            self.screen_width = screen_geom.width()
            self.screen_height = screen_geom.height()

            self.resize(self.current_movie.frameRect().width(), self.current_movie.frameRect().height())
            self.original_size = self.current_movie.frameRect().size()
            init_x = random.randint(0, self.screen_width - self.width())
            init_y = random.randint(0, self.screen_height - self.height())
            self.move(init_x, init_y)
            self.pos_f = QPointF(init_x, init_y)
            self.direction_f = QPointF(1.0, 0.0)
            self.is_facing_right = True
            self.show()

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.moveStep)
            self.timer.start(16)  # ~60 FPS.
        except Exception as e:
            print("Error in PetWidget.initUI:", e)

    def moveStep(self):
        try:
            step_size = 3.0
            if self.controller.hunger >= 80:
                if self.controller.snacks:
                    kirby_center = self.frameGeometry().center()
                    nearest_snack = min(
                        self.controller.snacks,
                        key=lambda snack: (kirby_center - snack.frameGeometry().center()).manhattanLength()
                    )
                    snack_center = nearest_snack.frameGeometry().center()
                    dx = snack_center.x() - kirby_center.x()
                    dy = snack_center.y() - kirby_center.y()
                    mag = math.hypot(dx, dy)
                    if mag != 0:
                        self.direction_f = QPointF(dx / mag, dy / mag)
                        self.flipDirection()
                else:
                    self.controller.spawn_snack()
            else:
                if random.random() < 0.05:
                    delta_x = random.uniform(-0.2, 0.2)
                    delta_y = random.uniform(-0.2, 0.2)
                    new_dx = self.direction_f.x() + delta_x
                    new_dy = self.direction_f.y() + delta_y
                    norm = math.hypot(new_dx, new_dy)
                    if norm != 0:
                        self.direction_f = QPointF(new_dx / norm, new_dy / norm)
                        self.flipDirection()

            new_pos = self.pos_f + self.direction_f * step_size

            if new_pos.x() < 0:
                new_pos.setX(0)
                self.direction_f.setX(-self.direction_f.x())
                self.flipDirection()
            elif new_pos.x() > self.screen_width - self.width():
                new_pos.setX(self.screen_width - self.width())
                self.direction_f.setX(-self.direction_f.x())
                self.flipDirection()
            if new_pos.y() < 0:
                new_pos.setY(0)
                self.direction_f.setY(-self.direction_f.y())
            elif new_pos.y() > self.screen_height - self.height():
                new_pos.setY(self.screen_height - self.height())
                self.direction_f.setY(-self.direction_f.y())

            self.pos_f = new_pos
            self.move(int(new_pos.x()), int(new_pos.y()))
            self.controller.check_collision()
        except Exception as e:
            print("Error in PetWidget.moveStep:", e)

    def flipDirection(self):
        try:
            self.is_facing_right = (self.direction_f.x() >= 0)
            new_movie = self.right_movie if self.is_facing_right else self.left_movie
            if new_movie != self.current_movie:
                self.current_movie.stop()
                self.current_movie = new_movie
                self.label.setMovie(self.current_movie)
                self.current_movie.start()
        except Exception as e:
            print("Error in PetWidget.flipDirection:", e)

    def level_up(self):
        """
        Increase Kirby's scale factor by a diminishing increment.
        Increment = 0.001 / current scale_factor.
        """
        try:
            increment = 0.001 / self.scale_factor
            self.scale_factor += increment
            new_width = int(self.original_size.width() * self.scale_factor)
            new_height = int(self.original_size.height() * self.scale_factor)
            self.resize(new_width, new_height)
            self.label.resize(new_width, new_height)
        except Exception as e:
            print("Error in PetWidget.level_up:", e)
