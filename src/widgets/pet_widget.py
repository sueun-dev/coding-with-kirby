import random
import math
from PyQt5.QtWidgets import QLabel, QWidget, QApplication
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt, QTimer, QPointF
from utils.utils import resource_path


class PetWidget(QWidget):
    """
    Kirby widget with smooth floating-point movement, mood-aware behavior,
    drag-and-drop support, and petting interaction.
    """

    MOVE_FPS = 60
    BASE_SPEED = 3.0
    HUNGRY_SPEED = 4.5
    WANDER_TURN_CHANCE = 0.04
    IDLE_PAUSE_CHANCE = 0.005
    IDLE_RESUME_CHANCE = 0.03

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.scale_factor = 1.0
        self._dragging = False
        self._drag_offset = None
        self._idle = False
        self._init_ui()

    def _init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self.label = QLabel(self)
        self.right_movie = QMovie(resource_path("images/Y3il.gif"))
        self.left_movie = QMovie(resource_path("images/Y3il-reverse.gif"))
        self.current_movie = self.right_movie
        self.label.setMovie(self.current_movie)
        self.current_movie.start()
        self.label.setScaledContents(True)
        self.label.resize(self.current_movie.frameRect().size())

        screen = QApplication.primaryScreen().geometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()

        self.resize(self.current_movie.frameRect().size())
        self.original_size = self.current_movie.frameRect().size()

        init_x = random.randint(100, self.screen_width - self.width() - 100)
        init_y = random.randint(100, self.screen_height - self.height() - 100)
        self.move(init_x, init_y)
        self.pos_f = QPointF(init_x, init_y)

        angle = random.uniform(0, 2 * math.pi)
        self.direction_f = QPointF(math.cos(angle), math.sin(angle))
        self.is_facing_right = self.direction_f.x() >= 0
        self.show()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._move_step)
        self.timer.start(1000 // self.MOVE_FPS)

    def _move_step(self):
        if self._dragging:
            return

        mood = self.controller.mood
        speed = self.BASE_SPEED

        # Sleeping: no movement
        if mood == "sleeping":
            return

        # Hungry: chase food fast
        if mood == "hungry" and self.controller.snacks:
            speed = self.HUNGRY_SPEED
            target = self._nearest_snack_center()
            if target:
                self._steer_toward(target)
        else:
            # Random idle pausing
            if not self._idle and random.random() < self.IDLE_PAUSE_CHANCE:
                self._idle = True
                return
            if self._idle:
                if random.random() < self.IDLE_RESUME_CHANCE:
                    self._idle = False
                return

            # Gentle wandering
            if random.random() < self.WANDER_TURN_CHANCE:
                delta_angle = random.gauss(0, 0.4)
                cos_a = math.cos(delta_angle)
                sin_a = math.sin(delta_angle)
                dx = self.direction_f.x() * cos_a - self.direction_f.y() * sin_a
                dy = self.direction_f.x() * sin_a + self.direction_f.y() * cos_a
                norm = math.hypot(dx, dy)
                if norm > 0:
                    self.direction_f = QPointF(dx / norm, dy / norm)
                    self._flip_direction()

        new_pos = self.pos_f + self.direction_f * speed
        new_pos = self._bounce(new_pos)
        self.pos_f = new_pos
        self.move(int(new_pos.x()), int(new_pos.y()))
        self.controller.check_collision()

    def _nearest_snack_center(self):
        if not self.controller.snacks:
            return None
        center = self.frameGeometry().center()
        nearest = min(
            self.controller.snacks,
            key=lambda s: (center - s.frameGeometry().center()).manhattanLength(),
        )
        return nearest.frameGeometry().center()

    def _steer_toward(self, target):
        center = self.frameGeometry().center()
        dx = target.x() - center.x()
        dy = target.y() - center.y()
        mag = math.hypot(dx, dy)
        if mag > 0:
            self.direction_f = QPointF(dx / mag, dy / mag)
            self._flip_direction()

    def _bounce(self, pos):
        max_x = self.screen_width - self.width()
        max_y = self.screen_height - self.height()
        if pos.x() < 0:
            pos.setX(0)
            self.direction_f.setX(abs(self.direction_f.x()))
            self._flip_direction()
        elif pos.x() > max_x:
            pos.setX(max_x)
            self.direction_f.setX(-abs(self.direction_f.x()))
            self._flip_direction()
        if pos.y() < 0:
            pos.setY(0)
            self.direction_f.setY(abs(self.direction_f.y()))
        elif pos.y() > max_y:
            pos.setY(max_y)
            self.direction_f.setY(-abs(self.direction_f.y()))
        return pos

    def _flip_direction(self):
        facing_right = self.direction_f.x() >= 0
        if facing_right == self.is_facing_right:
            return
        self.is_facing_right = facing_right
        new_movie = self.right_movie if facing_right else self.left_movie
        self.current_movie.stop()
        self.current_movie = new_movie
        self.label.setMovie(self.current_movie)
        self.current_movie.start()

    def apply_scale(self):
        w = int(self.original_size.width() * self.scale_factor)
        h = int(self.original_size.height() * self.scale_factor)
        self.resize(w, h)
        self.label.resize(w, h)

    # --- Mouse interactions ---

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_offset = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_offset is not None:
            new_pos = event.globalPos() - self._drag_offset
            self.move(new_pos)
            self.pos_f = QPointF(new_pos.x(), new_pos.y())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._dragging and self._drag_offset is not None:
                delta = (event.globalPos() - self.pos()) - self._drag_offset
                if delta.manhattanLength() < 5:
                    # It was a click, not a drag -> pet Kirby
                    self.controller.pet_kirby()
            self._dragging = False
            self._drag_offset = None
