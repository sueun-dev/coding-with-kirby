"""
Tests for pet physics — velocity, bouncing, clamping, throw mechanics.
"""
import math
import pytest

from utils.utils import (
    PET_MAX_SPEED, PET_CHASE_MAX_SPEED, PET_FRICTION,
    PET_THROW_FRICTION, PET_THROW_GRAVITY,
    PET_THROW_STOP_SPEED, PET_MAX_THROW_SPEED, PET_MIN_THROW_SPEED,
    PET_BOUNCE_FACTOR_NORMAL, PET_BOUNCE_FACTOR_THROWN,
    PET_FLIP_SPEED_THRESHOLD,
    BABY_MAX_SPEED, BABY_CHASE_MAX_SPEED, BABY_ACCELERATION,
    PET_ACCELERATION,
)


class TestSpeedClamping:
    """Test that speed is properly clamped to max values."""

    def clamp_speed(self, vx, vy, max_spd):
        speed = math.hypot(vx, vy)
        if speed > max_spd:
            ratio = max_spd / speed
            vx *= ratio
            vy *= ratio
        return vx, vy, math.hypot(vx, vy)

    def test_under_max_unchanged(self):
        vx, vy, speed = self.clamp_speed(1.0, 1.0, PET_MAX_SPEED)
        assert speed <= PET_MAX_SPEED + 0.001

    def test_over_max_clamped(self):
        vx, vy, speed = self.clamp_speed(10.0, 10.0, PET_MAX_SPEED)
        assert abs(speed - PET_MAX_SPEED) < 0.001

    def test_zero_velocity_stays_zero(self):
        vx, vy, speed = self.clamp_speed(0.0, 0.0, PET_MAX_SPEED)
        assert speed == 0.0

    def test_chase_speed_higher_than_walk(self):
        assert PET_CHASE_MAX_SPEED > PET_MAX_SPEED

    def test_baby_faster_than_adult(self):
        assert BABY_MAX_SPEED > PET_MAX_SPEED
        assert BABY_CHASE_MAX_SPEED > PET_CHASE_MAX_SPEED

    def test_baby_more_agile(self):
        assert BABY_ACCELERATION > PET_ACCELERATION


class TestBouncing:
    """Test wall bounce physics."""

    def bounce_axis(self, pos, vel, min_val, max_val, bounce_factor):
        bounced = False
        if pos < min_val:
            pos = min_val
            vel = abs(vel) * bounce_factor
            bounced = True
        elif pos > max_val:
            pos = max_val
            vel = -abs(vel) * bounce_factor
            bounced = True
        return pos, vel, bounced

    def test_bounce_left_wall(self):
        pos, vel, bounced = self.bounce_axis(-5, -3.0, 0, 1000, PET_BOUNCE_FACTOR_NORMAL)
        assert pos == 0
        assert vel > 0
        assert bounced is True

    def test_bounce_right_wall(self):
        pos, vel, bounced = self.bounce_axis(1005, 3.0, 0, 1000, PET_BOUNCE_FACTOR_NORMAL)
        assert pos == 1000
        assert vel < 0
        assert bounced is True

    def test_no_bounce_in_bounds(self):
        pos, vel, bounced = self.bounce_axis(500, 2.0, 0, 1000, PET_BOUNCE_FACTOR_NORMAL)
        assert pos == 500
        assert vel == 2.0
        assert bounced is False

    def test_thrown_bounce_stronger(self):
        assert PET_BOUNCE_FACTOR_THROWN > PET_BOUNCE_FACTOR_NORMAL

    def test_bounce_reduces_speed(self):
        _, vel_normal, _ = self.bounce_axis(-5, -10.0, 0, 1000, PET_BOUNCE_FACTOR_NORMAL)
        assert abs(vel_normal) < 10.0

    def test_bounce_at_exactly_boundary(self):
        pos, vel, bounced = self.bounce_axis(0, -1.0, 0, 1000, PET_BOUNCE_FACTOR_NORMAL)
        # At boundary with negative vel — should bounce
        # Actually 0 is not < 0, so no bounce
        assert bounced is False


class TestThrowPhysics:
    """Test throw mechanics."""

    def test_throw_friction_slows_down(self):
        vx = 10.0
        for _ in range(500):
            vx *= PET_THROW_FRICTION
        assert vx < 1.0

    def test_throw_gravity_pulls_down(self):
        vy = 0.0
        for _ in range(10):
            vy = vy * PET_THROW_FRICTION + PET_THROW_GRAVITY
        assert vy > 0  # positive = downward

    def test_throw_eventually_stops(self):
        """In real gameplay, bouncing + friction stops the throw.
        Simulate with wall bounces at y=0 and y=1000."""
        vx, vy = 15.0, -10.0
        py = 500.0
        screen_h = 1000.0
        for _ in range(5000):
            # Throw physics
            vx *= PET_THROW_FRICTION
            vy = vy * PET_THROW_FRICTION + PET_THROW_GRAVITY
            # Normal friction
            vx *= PET_FRICTION
            vy *= PET_FRICTION
            # Bounce at floor/ceiling
            py += vy
            if py < 0:
                py = 0
                vy = abs(vy) * PET_BOUNCE_FACTOR_THROWN
            elif py > screen_h:
                py = screen_h
                vy = -abs(vy) * PET_BOUNCE_FACTOR_THROWN
            speed = math.hypot(vx, vy)
            if speed < PET_THROW_STOP_SPEED:
                break
        else:
            pytest.fail("Throw never stopped after 5000 ticks with bouncing")

    def test_max_throw_speed_caps(self):
        vx, vy = 50.0, 50.0
        speed = math.hypot(vx, vy)
        if speed > PET_MAX_THROW_SPEED:
            ratio = PET_MAX_THROW_SPEED / speed
            vx *= ratio
            vy *= ratio
        new_speed = math.hypot(vx, vy)
        assert abs(new_speed - PET_MAX_THROW_SPEED) < 0.001

    def test_slow_drag_not_thrown(self):
        speed = 1.0
        assert speed < PET_MIN_THROW_SPEED


class TestFriction:
    """Test friction decay behavior."""

    def test_friction_reduces_speed(self):
        vx = 5.0
        vx *= PET_FRICTION
        assert vx < 5.0

    def test_friction_never_reverses(self):
        vx = 5.0
        for _ in range(1000):
            vx *= PET_FRICTION
        assert vx >= 0

    def test_friction_approaches_zero(self):
        vx = 10.0
        for _ in range(1000):
            vx *= PET_FRICTION
        assert vx < 0.001


class TestFacingDirection:
    """Test sprite flip logic."""

    def should_flip(self, vx, vy, current_facing_right):
        speed = math.hypot(vx, vy)
        if speed < PET_FLIP_SPEED_THRESHOLD:
            return current_facing_right  # no change
        return vx >= 0

    def test_moving_right_faces_right(self):
        assert self.should_flip(2.0, 0.0, False) is True

    def test_moving_left_faces_left(self):
        assert self.should_flip(-2.0, 0.0, True) is False

    def test_slow_speed_no_flip(self):
        # Below threshold, should keep current direction
        assert self.should_flip(0.1, 0.1, True) is True
        assert self.should_flip(0.1, 0.1, False) is False

    def test_vertical_movement_no_flip(self):
        # Zero horizontal but fast vertical — vx=0 means >=0 so faces right
        result = self.should_flip(0.0, 5.0, False)
        assert result is True  # vx >= 0
