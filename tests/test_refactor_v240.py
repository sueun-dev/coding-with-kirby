"""Regression tests for the v2.4.0 hardening & refactor pass.

Covers the robustness fixes (safe int coercion, malformed save/ranking
files, non-serializable save data) and the newly extracted constants.
All tests here are Qt-free so the suite stays fast and display-independent.
"""

from __future__ import annotations

import os
import tempfile

from utils.utils import (
    _coerce_int,
    validate_state,
    save_json_safe,
    load_json_safe,
    # newly extracted constants
    MAX_LEVELUPS_PER_TICK,
    PARTICLE_SPEED_RANGE, PARTICLE_UPWARD_BOOST, PARTICLE_MIN_LIFE,
    PET_WANDER_NUDGE_SIGMA, PET_REST_SWAY_SIGMA,
    PET_THROW_VELOCITY_SCALE, PET_CLICK_THRESHOLD_PX, PET_DRAG_HISTORY_LEN,
    ADULT_SCALE, BABY_SCALE, BABY_SPAWN_MARGIN, BABY_SPAWN_VX_RANGE, BABY_SPAWN_VY,
    TRAY_ICON_SIZE, TRAY_ICON_RETINA_SCALE, TRAY_ICON_FONT_SIZE,
    EVENT_TRIP_HOP, EVENT_DANCE_HSPEED, EVENT_DANCE_HOP,
    EVENT_SNEEZE_PUSH, EVENT_SNEEZE_HOP, EVENT_HICCUP_HOP,
)


# --- _coerce_int ---

class TestCoerceInt:
    def test_numeric_string(self):
        assert _coerce_int("50") == 50

    def test_plain_int(self):
        assert _coerce_int(7) == 7

    def test_float_truncates(self):
        assert _coerce_int(3.9) == 3

    def test_bool_is_int(self):
        assert _coerce_int(True) == 1
        assert _coerce_int(False) == 0

    def test_garbage_string_uses_default(self):
        assert _coerce_int("abc") == 0
        assert _coerce_int("abc", default=5) == 5

    def test_none_uses_default(self):
        assert _coerce_int(None) == 0
        assert _coerce_int(None, default=1) == 1

    def test_list_uses_default(self):
        assert _coerce_int([1, 2, 3]) == 0


# --- validate_state robustness (regression for the startup-crash bug) ---

class TestValidateStateRobustness:
    def test_non_numeric_hunger_does_not_crash(self):
        result = validate_state({"hunger": "abc"})
        assert result["hunger"] == 0

    def test_non_numeric_level_falls_back_to_one(self):
        result = validate_state({"level": "not_a_number"})
        assert result["level"] == 1

    def test_non_numeric_fields_default_safely(self):
        result = validate_state({
            "hunger": "x", "xp": "y", "level": "z",
            "total_eats": [], "total_pets": None, "star_eats": {},
        })
        assert result["hunger"] == 0
        assert result["xp"] == 0
        assert result["level"] == 1
        assert result["total_eats"] == 0
        assert result["total_pets"] == 0
        assert result["star_eats"] == 0

    def test_achievements_int_does_not_crash(self):
        # Previously raised TypeError: 'int' object is not iterable.
        result = validate_state({"achievements": 5})
        assert result["achievements"] == []

    def test_achievements_string_does_not_crash(self):
        result = validate_state({"achievements": "first_bite"})
        assert result["achievements"] == []

    def test_achievements_list_of_dicts_does_not_crash(self):
        # Previously raised TypeError: unhashable type: 'dict'.
        result = validate_state({"achievements": [{"id": "first_bite"}, "level5"]})
        assert result["achievements"] == ["level5"]

    def test_achievements_keeps_only_valid_string_ids(self):
        result = validate_state({"achievements": ["first_bite", None, 42, "FAKE", "level5"]})
        assert result["achievements"] == ["first_bite", "level5"]


# --- save_json_safe with non-serializable data ---

class TestSaveJsonNonSerializable:
    def test_non_serializable_does_not_raise(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        os.unlink(path)
        try:
            # A set is not JSON-serializable; must log + clean up, not raise.
            save_json_safe(path, {"bad": {1, 2, 3}})
            assert not os.path.exists(path + ".tmp")  # temp cleaned up
        finally:
            for p in (path, path + ".tmp"):
                if os.path.exists(p):
                    os.unlink(p)

    def test_good_data_still_round_trips(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_json_safe(path, {"level": 3, "items": [1, 2]})
            assert load_json_safe(path) == {"level": 3, "items": [1, 2]}
        finally:
            os.unlink(path)


# --- Newly extracted constants ---

class TestNewConstants:
    def test_levelup_guard_positive(self):
        assert MAX_LEVELUPS_PER_TICK > 0

    def test_particle_constants(self):
        lo, hi = PARTICLE_SPEED_RANGE
        assert 0 < lo < hi
        assert PARTICLE_UPWARD_BOOST > 0
        assert 0 < PARTICLE_MIN_LIFE < 1

    def test_pet_motion_constants(self):
        assert PET_WANDER_NUDGE_SIGMA > 0
        assert PET_REST_SWAY_SIGMA > 0
        assert PET_THROW_VELOCITY_SCALE > 0
        assert PET_CLICK_THRESHOLD_PX > 0
        assert PET_DRAG_HISTORY_LEN >= 2  # need at least 2 samples for velocity

    def test_scale_constants(self):
        assert ADULT_SCALE == 1.0
        assert 0 < BABY_SCALE < ADULT_SCALE
        assert BABY_SPAWN_MARGIN > 0

    def test_baby_spawn_velocity(self):
        lo, hi = BABY_SPAWN_VX_RANGE
        assert lo < hi
        assert BABY_SPAWN_VY < 0  # newborns launch upward

    def test_tray_constants(self):
        assert TRAY_ICON_SIZE > 0
        assert TRAY_ICON_RETINA_SCALE >= 1
        assert TRAY_ICON_FONT_SIZE > 0

    def test_event_impulses_sign(self):
        # Hops are upward (negative y); pushes are non-zero.
        assert EVENT_TRIP_HOP < 0
        assert EVENT_DANCE_HOP < 0
        assert EVENT_HICCUP_HOP < 0
        assert EVENT_SNEEZE_HOP < 0
        assert EVENT_DANCE_HSPEED > 0
        assert EVENT_SNEEZE_PUSH > 0
