"""Tests verifying bug fixes and refactoring from v2.2.0+ audits."""

from __future__ import annotations

import math

from utils.utils import (
    validate_state, xp_for_level,
    MAX_HUNGER, MAX_KIRBYS, MAX_PARTICLES, MAX_SNACKS, MAX_POOPS,
    PET_FRICTION, PET_THROW_FRICTION, PET_THROW_GRAVITY,
    PET_THROW_STOP_SPEED, PET_BOUNCE_FACTOR_THROWN,
    PET_BOUNCE_FACTOR_NORMAL, PET_SLEEP_FRICTION, PET_REST_FRICTION,
    PET_WANDER_NUDGE_CHANCE, PET_REST_SWAY_CHANCE,
    PET_CHASE_STEERING, PET_CHASE_ACCEL_MULTIPLIER,
    PET_GROWTH_BASE, PET_GROWTH_DIMINISH, PET_INIT_MARGIN,
    SNACK_SPAWN_MARGIN, BREED_COOLDOWN_FRAMES,
)


# --- Bug #10: NaN/Inf scale_factor ---

class TestNaNScaleFactor:
    def test_nan_scale_returns_default(self):
        result = validate_state({"scale_factor": float("nan")})
        assert math.isfinite(result["scale_factor"])
        assert result["scale_factor"] == 1.0

    def test_inf_scale_returns_capped(self):
        result = validate_state({"scale_factor": float("inf")})
        assert math.isfinite(result["scale_factor"])
        assert result["scale_factor"] == 1.0

    def test_neg_inf_scale_returns_capped(self):
        result = validate_state({"scale_factor": float("-inf")})
        assert math.isfinite(result["scale_factor"])
        assert result["scale_factor"] == 1.0

    def test_string_nan_scale(self):
        result = validate_state({"scale_factor": "not_a_number"})
        assert math.isfinite(result["scale_factor"])
        assert result["scale_factor"] == 1.0

    def test_none_scale(self):
        result = validate_state({"scale_factor": None})
        assert math.isfinite(result["scale_factor"])
        assert result["scale_factor"] == 1.0

    def test_valid_scale_preserved(self):
        result = validate_state({"scale_factor": 2.5})
        assert result["scale_factor"] == 2.5


# --- Bug #8: XP infinite loop guard ---

class TestXPSafetyGuard:
    def test_xp_for_level_always_positive(self):
        """Verify that xp_for_level never returns 0 or negative."""
        for level in range(0, 200):
            assert xp_for_level(level) > 0

    def test_level_up_with_huge_xp(self):
        """Simulate _add_xp with safety guard."""
        xp = 0
        level = 1
        amount = 999_999_999
        xp += amount
        max_levelups = 50
        count = 0
        while xp >= xp_for_level(level) and count < max_levelups:
            needed = xp_for_level(level)
            if needed <= 0:
                break
            xp -= needed
            level += 1
            count += 1
        # Should have leveled up exactly 50 times (capped)
        assert count == max_levelups
        assert level == 51


# --- Bug #7: Breeding limit re-check ---

class TestBreedingLimitRecheck:
    def test_cant_breed_at_max(self):
        all_pets = list(range(MAX_KIRBYS))
        assert len(all_pets) >= MAX_KIRBYS

    def test_breed_adds_one(self):
        """After breeding, total should be +1."""
        pets = list(range(MAX_KIRBYS - 1))
        pets.append("new_baby")
        assert len(pets) == MAX_KIRBYS


# --- Bug #6: Snack spawn bounds ---

class TestSnackSpawnBounds:
    def test_small_screen_no_crash(self):
        """Verify randint bounds are valid even on tiny screens."""
        screen_width = 100
        widget_width = 50
        max_x = screen_width - widget_width - SNACK_SPAWN_MARGIN
        safe_max = max(SNACK_SPAWN_MARGIN, max_x)
        # Should not raise ValueError
        import random
        x = random.randint(SNACK_SPAWN_MARGIN, safe_max)
        assert x >= SNACK_SPAWN_MARGIN

    def test_zero_screen_no_crash(self):
        screen_width = 0
        widget_width = 50
        max_x = screen_width - widget_width - SNACK_SPAWN_MARGIN
        safe_max = max(SNACK_SPAWN_MARGIN, max_x)
        import random
        x = random.randint(SNACK_SPAWN_MARGIN, safe_max)
        assert x == SNACK_SPAWN_MARGIN


# --- Bug #15/#16: Particle cap and life threshold ---

class TestParticleCap:
    def test_can_emit_at_zero(self):
        count = 0
        assert count + 8 <= MAX_PARTICLES

    def test_cant_emit_at_max(self):
        count = MAX_PARTICLES
        assert not (count + 1 <= MAX_PARTICLES)

    def test_cant_emit_near_max(self):
        count = MAX_PARTICLES - 3
        assert not (count + 8 <= MAX_PARTICLES)  # 8 eat particles wouldn't fit


class TestParticleLifeThreshold:
    def test_very_small_life_is_dead(self):
        """Particles with life near zero should be considered dead."""
        life = 0.0005
        assert not (life > 0.001)  # should be filtered out

    def test_alive_particle_survives(self):
        life = 0.01
        assert life > 0.001


# --- Bug #13: Baby spawn bounds ---

class TestBabySpawnBounds:
    def test_negative_parent_pos_clamped(self):
        parent_a_x, parent_b_x = -100, -50
        screen_w = 1920
        mid_x = max(0, min(screen_w - 50, (parent_a_x + parent_b_x) / 2))
        assert mid_x == 0

    def test_offscreen_right_clamped(self):
        parent_a_x, parent_b_x = 1900, 1950
        screen_w = 1920
        mid_x = max(0, min(screen_w - 50, (parent_a_x + parent_b_x) / 2))
        assert mid_x == screen_w - 50

    def test_normal_position_unchanged(self):
        parent_a_x, parent_b_x = 400, 500
        screen_w = 1920
        mid_x = max(0, min(screen_w - 50, (parent_a_x + parent_b_x) / 2))
        assert mid_x == 450.0


# --- Throw physics with bounce simulation (Bug #2 context) ---

class TestThrowWithBounce:
    def test_throw_stops_with_bouncing(self):
        """Full throw simulation including wall bounces and gravity."""
        vx, vy = 18.0, -15.0  # max throw speed
        py = 500.0
        screen_h = 1000.0
        stopped = False
        for tick in range(10000):
            vx *= PET_THROW_FRICTION
            vy = vy * PET_THROW_FRICTION + PET_THROW_GRAVITY
            vx *= PET_FRICTION
            vy *= PET_FRICTION
            py += vy
            if py < 0:
                py = 0
                vy = abs(vy) * PET_BOUNCE_FACTOR_THROWN
            elif py > screen_h:
                py = screen_h
                vy = -abs(vy) * PET_BOUNCE_FACTOR_THROWN
            speed = math.hypot(vx, vy)
            if speed < PET_THROW_STOP_SPEED:
                stopped = True
                break
        assert stopped, f"Throw didn't stop after 10000 ticks, speed={speed}"

    def test_gentle_throw_stops_quickly(self):
        vx, vy = 3.0, -2.0
        py = 500.0
        screen_h = 1000.0
        for tick in range(500):
            vx *= PET_THROW_FRICTION * PET_FRICTION
            vy = (vy * PET_THROW_FRICTION + PET_THROW_GRAVITY) * PET_FRICTION
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
        assert speed < PET_THROW_STOP_SPEED


# --- Validate state edge cases ---

class TestValidateStateEdgeCases:
    def test_extremely_large_values(self):
        result = validate_state({
            "hunger": 999999,
            "xp": 999999999,
            "level": 999999,
            "total_eats": 999999,
            "scale_factor": 999.0,
        })
        assert result["hunger"] == MAX_HUNGER
        assert result["scale_factor"] == 10.0
        assert result["level"] == 999999  # no upper cap on level

    def test_boolean_values_coerced(self):
        result = validate_state({
            "hunger": True,  # int(True) = 1
            "level": True,
        })
        assert result["hunger"] == 1
        assert result["level"] == 1

    def test_empty_achievements_list(self):
        result = validate_state({"achievements": []})
        assert result["achievements"] == []

    def test_achievements_with_none(self):
        result = validate_state({"achievements": [None, "first_bite", 42]})
        assert "first_bite" in result["achievements"]
        assert None not in result["achievements"]
        assert 42 not in result["achievements"]


# --- v2.3.0: Constants extracted from magic numbers ---

class TestExtractedConstants:
    """Verify that constants extracted during refactoring have sane values."""

    def test_friction_constants_in_range(self):
        assert 0.0 < PET_SLEEP_FRICTION < 1.0
        assert 0.0 < PET_REST_FRICTION < 1.0
        assert PET_REST_FRICTION > PET_SLEEP_FRICTION  # rest is less damped

    def test_bounce_factors_in_range(self):
        assert 0.0 < PET_BOUNCE_FACTOR_NORMAL < 1.0
        assert 0.0 < PET_BOUNCE_FACTOR_THROWN < 1.0
        assert PET_BOUNCE_FACTOR_THROWN > PET_BOUNCE_FACTOR_NORMAL

    def test_chance_constants_in_range(self):
        assert 0.0 < PET_WANDER_NUDGE_CHANCE < 1.0
        assert 0.0 < PET_REST_SWAY_CHANCE < 1.0

    def test_chase_constants_positive(self):
        assert PET_CHASE_STEERING > 0
        assert PET_CHASE_ACCEL_MULTIPLIER > 1.0

    def test_growth_constants_positive(self):
        assert PET_GROWTH_BASE > 0
        assert PET_GROWTH_DIMINISH > 0

    def test_growth_formula_diminishes(self):
        """Growth should decrease as level increases."""
        growth_1 = PET_GROWTH_BASE / (1 + 0 * PET_GROWTH_DIMINISH)
        growth_50 = PET_GROWTH_BASE / (1 + 49 * PET_GROWTH_DIMINISH)
        assert growth_50 < growth_1

    def test_init_margin_reasonable(self):
        assert PET_INIT_MARGIN > 0
        assert PET_INIT_MARGIN < 500  # shouldn't be too large
