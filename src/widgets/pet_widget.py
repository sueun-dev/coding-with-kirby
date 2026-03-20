import random
import math
from enum import Enum, auto
from PyQt5.QtWidgets import QLabel, QWidget, QApplication
from PyQt5.QtGui import QMovie, QCursor
from PyQt5.QtCore import Qt, QTimer, QPointF, QPoint
from utils.utils import resource_path
from utils.macos_window import pin_window_above_mission_control


class State(Enum):
    WANDERING = auto()
    IDLE = auto()
    CHASING = auto()
    RESTING = auto()
    THROWN = auto()


class PetWidget(QWidget):
    """
    Kirby with state-machine movement: wander, pause, rest, chase food.
    Uses velocity with acceleration for smooth, natural motion.
    """

    FPS = 60
    MAX_SPEED = 2.2
    CHASE_MAX_SPEED = 4.0
    ACCELERATION = 0.08
    FRICTION = 0.96
    TURN_SMOOTHING = 0.06
    THROW_FRICTION = 0.985
    THROW_GRAVITY = 0.15

    def __init__(self, controller, is_baby=False):
        super().__init__()
        self.controller = controller
        self.is_baby = is_baby
        self.scale_factor = 0.5 if is_baby else 1.0
        self._dragging = False
        self._drag_offset = None
        self._drag_positions = []  # for throw velocity calculation

        # Physics
        self.pos_f = QPointF(0, 0)
        self.vel = QPointF(0, 0)
        self.target_dir = QPointF(1, 0)
        self.is_facing_right = True
        self._throw_bounces = 0

        # State machine
        self.state = State.WANDERING
        self._state_timer = 0  # frames remaining in current state

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

        # Babies are faster and more energetic
        if self.is_baby:
            self.MAX_SPEED = 3.0
            self.CHASE_MAX_SPEED = 5.0
            self.ACCELERATION = 0.12

        init_x = random.randint(100, self.screen_width - self.width() - 100)
        init_y = random.randint(100, self.screen_height - self.height() - 100)
        self.move(init_x, init_y)
        self.pos_f = QPointF(init_x, init_y)

        self._pick_wander_direction()
        self._state_timer = random.randint(120, 360)  # 2-6 sec
        self.show()
        pin_window_above_mission_control(self)

        if self.is_baby:
            self.apply_scale()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000 // self.FPS)

    def _tick(self):
        if self._dragging:
            return

        # Thrown state (flung by user)
        if self.state == State.THROWN:
            self._do_thrown()
            self._apply_velocity()
            self.controller.check_collision()
            return

        if self.controller.mood == "sleeping":
            # Slow to a stop
            self.vel *= 0.92
            self._apply_velocity()
            return

        self._state_timer -= 1

        # State transitions
        has_food = bool(self.controller.snacks)
        should_chase = (self.controller.mood == "hungry" and has_food) if not self.is_baby else has_food
        if should_chase:
            self.state = State.CHASING
        elif self.state == State.CHASING and not should_chase:
            self._enter_wandering()
        elif self._state_timer <= 0:
            self._next_state()

        # State behavior
        if self.state == State.WANDERING:
            self._do_wander()
        elif self.state == State.IDLE:
            self._do_idle()
        elif self.state == State.RESTING:
            self._do_rest()
        elif self.state == State.CHASING:
            self._do_chase()

        self._apply_velocity()
        self.controller.check_collision()

    def _next_state(self):
        if self.state == State.WANDERING:
            # After wandering, either pause briefly or rest
            roll = random.random()
            if roll < 0.5:
                self._enter_idle()
            elif roll < 0.75:
                self._enter_resting()
            else:
                # Pick new wander direction
                self._enter_wandering()
        elif self.state in (State.IDLE, State.RESTING):
            self._enter_wandering()

    def _enter_wandering(self):
        self.state = State.WANDERING
        self._pick_wander_direction()
        self._state_timer = random.randint(150, 420)  # 2.5-7 sec

    def _enter_idle(self):
        self.state = State.IDLE
        self._state_timer = random.randint(30, 120)  # 0.5-2 sec pause

    def _enter_resting(self):
        self.state = State.RESTING
        self._state_timer = random.randint(90, 240)  # 1.5-4 sec

    def _pick_wander_direction(self):
        angle = random.uniform(0, 2 * math.pi)
        self.target_dir = QPointF(math.cos(angle), math.sin(angle))

    # --- State behaviors ---

    def _do_wander(self):
        # Occasionally nudge direction slightly for organic feel
        if random.random() < 0.02:
            nudge = random.gauss(0, 0.3)
            cos_a, sin_a = math.cos(nudge), math.sin(nudge)
            dx = self.target_dir.x() * cos_a - self.target_dir.y() * sin_a
            dy = self.target_dir.x() * sin_a + self.target_dir.y() * cos_a
            self.target_dir = QPointF(dx, dy)
            self._normalize_target()

        # Accelerate toward target direction
        ax = self.target_dir.x() * self.ACCELERATION
        ay = self.target_dir.y() * self.ACCELERATION
        self.vel = QPointF(self.vel.x() + ax, self.vel.y() + ay)
        self._clamp_speed(self.MAX_SPEED)
        self._update_facing()

    def _do_idle(self):
        # Decelerate to a stop
        self.vel *= self.FRICTION

    def _do_rest(self):
        # Almost stopped, gentle breathing-like micro-sway
        self.vel *= 0.94
        if random.random() < 0.03:
            self.vel = QPointF(
                self.vel.x() + random.gauss(0, 0.05),
                self.vel.y() + random.gauss(0, 0.05),
            )

    def _do_chase(self):
        target = self._nearest_snack_center()
        if not target:
            return
        center = self.frameGeometry().center()
        dx = target.x() - center.x()
        dy = target.y() - center.y()
        dist = math.hypot(dx, dy)
        if dist < 1:
            return

        # Smooth steering toward food
        desired = QPointF(dx / dist, dy / dist)
        self.target_dir = QPointF(
            self.target_dir.x() + (desired.x() - self.target_dir.x()) * 0.12,
            self.target_dir.y() + (desired.y() - self.target_dir.y()) * 0.12,
        )
        self._normalize_target()

        # Faster acceleration when chasing
        chase_accel = self.ACCELERATION * 1.8
        self.vel = QPointF(
            self.vel.x() + self.target_dir.x() * chase_accel,
            self.vel.y() + self.target_dir.y() * chase_accel,
        )
        self._clamp_speed(self.CHASE_MAX_SPEED)
        self._update_facing()

    def _do_thrown(self):
        """Kirby was flung — apply gravity and high friction until stopped."""
        self.vel = QPointF(
            self.vel.x() * self.THROW_FRICTION,
            self.vel.y() * self.THROW_FRICTION + self.THROW_GRAVITY,
        )
        self._update_facing()
        speed = math.hypot(self.vel.x(), self.vel.y())
        if speed < 0.5:
            self._throw_bounces = 0
            self._enter_wandering()
            self.controller.bubble.show_text(
                random.choice(["Whoa!", "Dizzy...", "Poyo~?!", "Again!!"]), 2000
            )

    # --- Physics helpers ---

    def _apply_velocity(self):
        # Apply friction
        self.vel = QPointF(self.vel.x() * self.FRICTION, self.vel.y() * self.FRICTION)

        new_pos = QPointF(self.pos_f.x() + self.vel.x(), self.pos_f.y() + self.vel.y())
        new_pos = self._bounce(new_pos)
        self.pos_f = new_pos
        self.move(int(new_pos.x()), int(new_pos.y()))

    def _clamp_speed(self, max_spd):
        speed = math.hypot(self.vel.x(), self.vel.y())
        if speed > max_spd:
            ratio = max_spd / speed
            self.vel = QPointF(self.vel.x() * ratio, self.vel.y() * ratio)

    def _normalize_target(self):
        mag = math.hypot(self.target_dir.x(), self.target_dir.y())
        if mag > 0:
            self.target_dir = QPointF(self.target_dir.x() / mag, self.target_dir.y() / mag)

    def _update_facing(self):
        # Only flip when velocity is clearly horizontal
        speed = math.hypot(self.vel.x(), self.vel.y())
        if speed < 0.3:
            return
        facing_right = self.vel.x() >= 0
        if facing_right != self.is_facing_right:
            self.is_facing_right = facing_right
            new_movie = self.right_movie if facing_right else self.left_movie
            self.current_movie.stop()
            self.current_movie = new_movie
            self.label.setMovie(self.current_movie)
            self.current_movie.start()

    def _bounce(self, pos):
        max_x = self.screen_width - self.width()
        max_y = self.screen_height - self.height()
        bounce_factor = 0.6 if self.state == State.THROWN else 0.5
        bounced = False
        if pos.x() < 0:
            pos.setX(0)
            self.vel.setX(abs(self.vel.x()) * bounce_factor)
            self.target_dir.setX(abs(self.target_dir.x()))
            bounced = True
        elif pos.x() > max_x:
            pos.setX(max_x)
            self.vel.setX(-abs(self.vel.x()) * bounce_factor)
            self.target_dir.setX(-abs(self.target_dir.x()))
            bounced = True
        if pos.y() < 0:
            pos.setY(0)
            self.vel.setY(abs(self.vel.y()) * bounce_factor)
            self.target_dir.setY(abs(self.target_dir.y()))
            bounced = True
        elif pos.y() > max_y:
            pos.setY(max_y)
            self.vel.setY(-abs(self.vel.y()) * bounce_factor)
            self.target_dir.setY(-abs(self.target_dir.y()))
            bounced = True
        if bounced and self.state == State.THROWN:
            self._throw_bounces += 1
            if self._throw_bounces <= 3:
                center = self.frameGeometry().center()
                self.controller.particles.emit_eat(center.x(), center.y())
        return pos

    def _nearest_snack_center(self):
        if not self.controller.snacks:
            return None
        center = self.frameGeometry().center()
        nearest = min(
            self.controller.snacks,
            key=lambda s: (center - s.frameGeometry().center()).manhattanLength(),
        )
        return nearest.frameGeometry().center()

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
            self._drag_positions = [(event.globalPos(), event.timestamp())]

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_offset is not None:
            new_pos = event.globalPos() - self._drag_offset
            self.move(new_pos)
            self.pos_f = QPointF(new_pos.x(), new_pos.y())
            # Track last few positions for throw velocity
            self._drag_positions.append((event.globalPos(), event.timestamp()))
            if len(self._drag_positions) > 6:
                self._drag_positions.pop(0)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._dragging and self._drag_offset is not None:
                delta = (event.globalPos() - self.pos()) - self._drag_offset
                if delta.manhattanLength() < 5:
                    self.controller.pet_kirby()
                elif len(self._drag_positions) >= 2:
                    # Calculate throw velocity from recent drag
                    p1, t1 = self._drag_positions[0]
                    p2, t2 = self._drag_positions[-1]
                    dt = max(1, t2 - t1)
                    vx = (p2.x() - p1.x()) / dt * 16.0
                    vy = (p2.y() - p1.y()) / dt * 16.0
                    speed = math.hypot(vx, vy)
                    if speed > 2.0:
                        # Cap throw speed
                        max_throw = 18.0
                        if speed > max_throw:
                            ratio = max_throw / speed
                            vx *= ratio
                            vy *= ratio
                        self.vel = QPointF(vx, vy)
                        self.state = State.THROWN
                        self._throw_bounces = 0
                        self.controller.bubble.show_text(
                            random.choice(["Wheee!", "Poyooo~!", "Waaaah!"]), 1500
                        )
            self._dragging = False
            self._drag_offset = None
            self._drag_positions = []
