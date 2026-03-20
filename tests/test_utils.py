"""
Tests for utils.utils — constants, helpers, and persistence functions.
"""
import json
import os
import tempfile

import pytest

from utils.utils import (
    __version__,
    xp_for_level,
    is_achievement_met,
    validate_state,
    load_json_safe,
    save_json_safe,
    resource_path,
    ACHIEVEMENTS, FOODS, MOOD_EMOJIS,
    MAX_HUNGER, MAX_KIRBYS, EATS_UNTIL_POOP,
)


# --- Version ---

class TestVersion:
    def test_version_format(self):
        parts = __version__.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_version_major_is_2(self):
        assert __version__.startswith("2.")


# --- xp_for_level ---

class TestXpForLevel:
    def test_level_1_returns_positive(self):
        assert xp_for_level(1) > 0

    def test_monotonically_increasing(self):
        for i in range(1, 50):
            assert xp_for_level(i + 1) > xp_for_level(i)

    def test_level_0(self):
        assert xp_for_level(0) == 50  # 50 * 1.3^0 = 50

    def test_returns_int(self):
        for level in range(0, 30):
            assert isinstance(xp_for_level(level), int)

    def test_high_level_doesnt_overflow(self):
        # Level 100 should still be a sane number
        result = xp_for_level(100)
        assert isinstance(result, int)
        assert result > 0


# --- is_achievement_met ---

class TestIsAchievementMet:
    def test_first_bite_not_met(self):
        ach = {"id": "first_bite", "eats_req": 1}
        assert is_achievement_met(ach, total_eats=0) is False

    def test_first_bite_met(self):
        ach = {"id": "first_bite", "eats_req": 1}
        assert is_achievement_met(ach, total_eats=1) is True

    def test_first_bite_exceeded(self):
        ach = {"id": "first_bite", "eats_req": 1}
        assert is_achievement_met(ach, total_eats=100) is True

    def test_level_requirement(self):
        ach = {"id": "level5", "level_req": 5}
        assert is_achievement_met(ach, level=4) is False
        assert is_achievement_met(ach, level=5) is True
        assert is_achievement_met(ach, level=10) is True

    def test_pets_requirement(self):
        ach = {"id": "pet_lover", "pets_req": 20}
        assert is_achievement_met(ach, total_pets=19) is False
        assert is_achievement_met(ach, total_pets=20) is True

    def test_star_requirement(self):
        ach = {"id": "star_hunter", "star_req": 10}
        assert is_achievement_met(ach, star_eats=9) is False
        assert is_achievement_met(ach, star_eats=10) is True

    def test_no_requirements_always_met(self):
        ach = {"id": "empty"}
        assert is_achievement_met(ach) is True

    def test_all_real_achievements_have_valid_structure(self):
        for ach in ACHIEVEMENTS:
            assert "id" in ach
            assert "name" in ach
            assert "desc" in ach
            # Must have at least one requirement
            has_req = any(
                ach.get(k, 0) > 0
                for k in ("eats_req", "level_req", "pets_req", "star_req")
            )
            assert has_req, f"Achievement {ach['id']} has no requirements"


# --- validate_state ---

class TestValidateState:
    def test_empty_dict(self):
        result = validate_state({})
        assert result["hunger"] == 0
        assert result["level"] == 1
        assert result["xp"] == 0
        assert result["achievements"] == []

    def test_non_dict_returns_empty(self):
        assert validate_state("not a dict") == {}
        assert validate_state(None) == {}
        assert validate_state(42) == {}
        assert validate_state([]) == {}

    def test_clamps_hunger(self):
        assert validate_state({"hunger": -10})["hunger"] == 0
        assert validate_state({"hunger": 200})["hunger"] == MAX_HUNGER
        assert validate_state({"hunger": 50})["hunger"] == 50

    def test_clamps_level(self):
        assert validate_state({"level": 0})["level"] == 1
        assert validate_state({"level": -5})["level"] == 1
        assert validate_state({"level": 10})["level"] == 10

    def test_clamps_scale(self):
        assert validate_state({"scale_factor": 0.0})["scale_factor"] == 0.1
        assert validate_state({"scale_factor": 100.0})["scale_factor"] == 10.0
        assert validate_state({"scale_factor": 1.5})["scale_factor"] == 1.5

    def test_filters_invalid_achievements(self):
        result = validate_state({"achievements": ["first_bite", "FAKE", "level5"]})
        assert "first_bite" in result["achievements"]
        assert "level5" in result["achievements"]
        assert "FAKE" not in result["achievements"]

    def test_handles_type_coercion(self):
        result = validate_state({"hunger": "50", "level": "3"})
        assert result["hunger"] == 50
        assert result["level"] == 3

    def test_negative_values_clamped(self):
        result = validate_state({
            "xp": -100,
            "total_eats": -5,
            "total_pets": -1,
            "star_eats": -3,
        })
        assert result["xp"] == 0
        assert result["total_eats"] == 0
        assert result["total_pets"] == 0
        assert result["star_eats"] == 0


# --- load_json_safe / save_json_safe ---

class TestJsonIO:
    def test_load_nonexistent_returns_default(self):
        result = load_json_safe("/nonexistent/path.json", default={"x": 1})
        assert result == {"x": 1}

    def test_load_default_none_returns_dict(self):
        result = load_json_safe("/nonexistent/path.json")
        assert result == {}

    def test_load_list_default(self):
        result = load_json_safe("/nonexistent/path.json", default=[])
        assert result == []

    def test_save_and_load_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            data = {"level": 5, "xp": 100, "items": [1, 2, 3]}
            save_json_safe(path, data)
            loaded = load_json_safe(path)
            assert loaded == data
        finally:
            os.unlink(path)

    def test_save_atomic_creates_no_tmp_on_success(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_json_safe(path, {"a": 1})
            assert not os.path.exists(path + ".tmp")
        finally:
            os.unlink(path)

    def test_load_corrupted_json_returns_default(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            f.write("{invalid json!!!")
            path = f.name
        try:
            result = load_json_safe(path, default={"fallback": True})
            assert result == {"fallback": True}
        finally:
            os.unlink(path)

    def test_load_empty_file_returns_default(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            path = f.name
        try:
            result = load_json_safe(path, default=[])
            assert result == []
        finally:
            os.unlink(path)

    def test_save_to_readonly_dir_doesnt_crash(self):
        # Should log error but not raise
        save_json_safe("/nonexistent_dir/test.json", {"a": 1})


# --- Constants validation ---

class TestConstants:
    def test_foods_have_valid_structure(self):
        for emoji, name, hunger, xp in FOODS:
            assert isinstance(emoji, str) and len(emoji) > 0
            assert isinstance(name, str) and len(name) > 0
            assert isinstance(hunger, int) and hunger > 0
            assert isinstance(xp, int) and xp > 0

    def test_mood_emojis_cover_all_moods(self):
        expected = {"happy", "hungry", "sleeping", "excited"}
        assert set(MOOD_EMOJIS.keys()) == expected

    def test_achievement_ids_unique(self):
        ids = [a["id"] for a in ACHIEVEMENTS]
        assert len(ids) == len(set(ids))

    def test_max_constants_positive(self):
        assert MAX_HUNGER > 0
        assert MAX_KIRBYS > 0
        assert EATS_UNTIL_POOP > 0


# --- resource_path ---

class TestResourcePath:
    def test_returns_string(self):
        result = resource_path("images/Y3il.gif")
        assert isinstance(result, str)

    def test_existing_resource_found(self):
        result = resource_path("images/Y3il.gif")
        assert os.path.exists(result)

    def test_missing_resource_still_returns_path(self):
        result = resource_path("images/nonexistent.gif")
        assert isinstance(result, str)
        assert "nonexistent.gif" in result
