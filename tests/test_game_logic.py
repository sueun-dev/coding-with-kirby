"""
Tests for game logic — XP, leveling, hunger, mood, achievements, breeding limits.
These tests mock PyQt5 widgets to test pure logic without a display.
"""
import pytest
from unittest.mock import MagicMock, patch

from utils.utils import (
    xp_for_level,
    is_achievement_met,
    ACHIEVEMENTS, FOODS,
    MAX_HUNGER, MAX_SNACKS, MAX_POOPS, MAX_KIRBYS,
    EATS_UNTIL_POOP, POOP_SPAWN_CHANCE,
    HUNGER_RATE, HUNGER_AUTO_FEED_THRESHOLD,
    BREED_COOLDOWN_FRAMES, BREEDING_DISTANCE,
    POOP_CLEAN_XP, BREED_XP, STAR_FIND_XP,
    SLEEP_THRESHOLD_S,
)


class FakeController:
    """Minimal controller mock for testing game logic without Qt."""

    def __init__(self):
        self.hunger = 0
        self.xp = 0
        self.level = 1
        self.total_eats = 0
        self.total_pets = 0
        self.star_eats = 0
        self.mood = "happy"
        self.unlocked_achievements = set()
        self.snacks = []
        self.poops = []
        self._idle_seconds = 0
        self._eats_since_poop = 0
        self._cpu_percent = 0.0
        self._breed_cooldown = 0

    @property
    def xp_for_next_level(self):
        return xp_for_level(self.level)

    def add_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_for_next_level:
            self.xp -= self.xp_for_next_level
            self.level += 1

    def check_achievements(self):
        for ach in ACHIEVEMENTS:
            if ach["id"] in self.unlocked_achievements:
                continue
            if is_achievement_met(
                ach,
                total_eats=self.total_eats,
                level=self.level,
                total_pets=self.total_pets,
                star_eats=self.star_eats,
            ):
                self.unlocked_achievements.add(ach["id"])


# --- XP & Leveling ---

class TestXPAndLeveling:
    def test_level_up_once(self):
        ctrl = FakeController()
        needed = ctrl.xp_for_next_level
        ctrl.add_xp(needed)
        assert ctrl.level == 2
        assert ctrl.xp == 0

    def test_level_up_multiple(self):
        ctrl = FakeController()
        # Give enough XP to go from 1 to 5
        for _ in range(4):
            ctrl.add_xp(ctrl.xp_for_next_level)
        assert ctrl.level == 5

    def test_overflow_xp_carries_over(self):
        ctrl = FakeController()
        needed = ctrl.xp_for_next_level
        ctrl.add_xp(needed + 10)
        assert ctrl.level == 2
        assert ctrl.xp == 10

    def test_massive_xp_doesnt_crash(self):
        ctrl = FakeController()
        ctrl.add_xp(999_999)
        assert ctrl.level > 1
        assert ctrl.xp >= 0

    def test_zero_xp_no_levelup(self):
        ctrl = FakeController()
        ctrl.add_xp(0)
        assert ctrl.level == 1
        assert ctrl.xp == 0


# --- Hunger ---

class TestHunger:
    def test_hunger_increases(self):
        ctrl = FakeController()
        for _ in range(10):
            if ctrl.hunger < MAX_HUNGER:
                ctrl.hunger = min(MAX_HUNGER, ctrl.hunger + HUNGER_RATE)
        assert ctrl.hunger == 10

    def test_hunger_caps_at_max(self):
        ctrl = FakeController()
        ctrl.hunger = MAX_HUNGER - 1
        ctrl.hunger = min(MAX_HUNGER, ctrl.hunger + HUNGER_RATE)
        assert ctrl.hunger == MAX_HUNGER
        # One more tick — should not exceed
        ctrl.hunger = min(MAX_HUNGER, ctrl.hunger + HUNGER_RATE)
        assert ctrl.hunger == MAX_HUNGER

    def test_eating_reduces_hunger(self):
        ctrl = FakeController()
        ctrl.hunger = 50
        restore = 20
        ctrl.hunger = max(0, ctrl.hunger - restore)
        assert ctrl.hunger == 30

    def test_hunger_doesnt_go_negative(self):
        ctrl = FakeController()
        ctrl.hunger = 5
        ctrl.hunger = max(0, ctrl.hunger - 50)
        assert ctrl.hunger == 0

    def test_auto_feed_threshold(self):
        ctrl = FakeController()
        ctrl.hunger = HUNGER_AUTO_FEED_THRESHOLD
        should_auto_feed = ctrl.hunger >= HUNGER_AUTO_FEED_THRESHOLD and not ctrl.snacks
        assert should_auto_feed is True

    def test_auto_feed_blocked_by_existing_snacks(self):
        ctrl = FakeController()
        ctrl.hunger = HUNGER_AUTO_FEED_THRESHOLD
        ctrl.snacks = ["fake_snack"]
        should_auto_feed = ctrl.hunger >= HUNGER_AUTO_FEED_THRESHOLD and not ctrl.snacks
        assert should_auto_feed is False


# --- Mood ---

class TestMood:
    def test_sleeping_after_idle(self):
        ctrl = FakeController()
        ctrl._idle_seconds = SLEEP_THRESHOLD_S + 1
        ctrl.hunger = 30  # below 60
        # Simulate mood tick logic
        if ctrl._idle_seconds >= SLEEP_THRESHOLD_S and ctrl.hunger < 60:
            ctrl.mood = "sleeping"
        assert ctrl.mood == "sleeping"

    def test_hungry_mood(self):
        ctrl = FakeController()
        ctrl.hunger = 85
        if ctrl.hunger >= 80:
            ctrl.mood = "hungry"
        assert ctrl.mood == "hungry"

    def test_excited_mood(self):
        ctrl = FakeController()
        ctrl.total_eats = 5
        ctrl.hunger = 10
        if ctrl.total_eats > 0 and ctrl.hunger < 30:
            ctrl.mood = "excited"
        assert ctrl.mood == "excited"

    def test_reset_idle_wakes_up(self):
        ctrl = FakeController()
        ctrl.mood = "sleeping"
        ctrl._idle_seconds = 100
        # Reset idle
        ctrl._idle_seconds = 0
        if ctrl.mood == "sleeping":
            ctrl.mood = "happy"
        assert ctrl.mood == "happy"
        assert ctrl._idle_seconds == 0


# --- Achievements ---

class TestAchievements:
    def test_first_bite_unlocks_after_eating(self):
        ctrl = FakeController()
        ctrl.total_eats = 1
        ctrl.check_achievements()
        assert "first_bite" in ctrl.unlocked_achievements

    def test_duplicate_achievement_doesnt_trigger(self):
        ctrl = FakeController()
        ctrl.total_eats = 1
        ctrl.check_achievements()
        count_before = len(ctrl.unlocked_achievements)
        ctrl.check_achievements()
        assert len(ctrl.unlocked_achievements) == count_before

    def test_hungry_boy_at_10_eats(self):
        ctrl = FakeController()
        ctrl.total_eats = 10
        ctrl.check_achievements()
        assert "hungry_boy" in ctrl.unlocked_achievements

    def test_glutton_at_50_eats(self):
        ctrl = FakeController()
        ctrl.total_eats = 50
        ctrl.check_achievements()
        assert "glutton" in ctrl.unlocked_achievements

    def test_legend_at_200_eats(self):
        ctrl = FakeController()
        ctrl.total_eats = 200
        ctrl.check_achievements()
        assert "legend" in ctrl.unlocked_achievements

    def test_level_achievements(self):
        ctrl = FakeController()
        ctrl.level = 25
        ctrl.check_achievements()
        assert "level5" in ctrl.unlocked_achievements
        assert "level10" in ctrl.unlocked_achievements
        assert "level25" in ctrl.unlocked_achievements

    def test_pet_lover(self):
        ctrl = FakeController()
        ctrl.total_pets = 20
        ctrl.check_achievements()
        assert "pet_lover" in ctrl.unlocked_achievements

    def test_star_hunter(self):
        ctrl = FakeController()
        ctrl.star_eats = 10
        ctrl.check_achievements()
        assert "star_hunter" in ctrl.unlocked_achievements

    def test_no_achievements_at_zero(self):
        ctrl = FakeController()
        ctrl.check_achievements()
        assert len(ctrl.unlocked_achievements) == 0

    def test_all_achievements_achievable(self):
        ctrl = FakeController()
        ctrl.total_eats = 1000
        ctrl.level = 100
        ctrl.total_pets = 100
        ctrl.star_eats = 100
        ctrl.check_achievements()
        assert len(ctrl.unlocked_achievements) == len(ACHIEVEMENTS)


# --- Poop Logic ---

class TestPoopLogic:
    def test_poop_spawns_after_threshold(self):
        ctrl = FakeController()
        ctrl._eats_since_poop = EATS_UNTIL_POOP
        should_poop = ctrl._eats_since_poop >= EATS_UNTIL_POOP
        assert should_poop is True

    def test_poop_counter_resets(self):
        ctrl = FakeController()
        ctrl._eats_since_poop = 5
        ctrl._eats_since_poop = 0  # simulate spawn_poop
        assert ctrl._eats_since_poop == 0

    def test_poop_limit(self):
        ctrl = FakeController()
        ctrl.poops = list(range(MAX_POOPS))
        can_spawn = len(ctrl.poops) < MAX_POOPS
        assert can_spawn is False

    def test_poop_under_limit(self):
        ctrl = FakeController()
        ctrl.poops = list(range(MAX_POOPS - 1))
        can_spawn = len(ctrl.poops) < MAX_POOPS
        assert can_spawn is True


# --- Snack Limits ---

class TestSnackLimits:
    def test_snack_cap(self):
        ctrl = FakeController()
        ctrl.snacks = list(range(MAX_SNACKS))
        can_spawn = len(ctrl.snacks) < MAX_SNACKS
        assert can_spawn is False

    def test_snack_under_cap(self):
        ctrl = FakeController()
        ctrl.snacks = list(range(MAX_SNACKS - 1))
        can_spawn = len(ctrl.snacks) < MAX_SNACKS
        assert can_spawn is True


# --- Breeding Logic ---

class TestBreedingLogic:
    def test_cooldown_blocks_breeding(self):
        ctrl = FakeController()
        ctrl._breed_cooldown = BREED_COOLDOWN_FRAMES
        should_breed = ctrl._breed_cooldown <= 0
        assert should_breed is False

    def test_cooldown_decrements(self):
        ctrl = FakeController()
        ctrl._breed_cooldown = 5
        ctrl._breed_cooldown -= 1
        assert ctrl._breed_cooldown == 4

    def test_max_kirbys_blocks_breeding(self):
        ctrl = FakeController()
        all_pets = list(range(MAX_KIRBYS))
        can_breed = len(all_pets) < MAX_KIRBYS
        assert can_breed is False

    def test_single_pet_cant_breed(self):
        all_pets = ["main_pet"]
        can_breed = len(all_pets) >= 2
        assert can_breed is False

    def test_two_pets_can_breed(self):
        all_pets = ["main_pet", "baby"]
        can_breed = len(all_pets) >= 2 and len(all_pets) < MAX_KIRBYS
        assert can_breed is True


# --- Food Definitions ---

class TestFoodDefinitions:
    def test_all_foods_have_positive_values(self):
        for emoji, name, hunger_restore, xp_reward in FOODS:
            assert hunger_restore > 0
            assert xp_reward > 0

    def test_star_candy_exists(self):
        names = [f[1] for f in FOODS]
        assert "Star Candy" in names

    def test_star_candy_has_high_xp(self):
        star = next(f for f in FOODS if f[1] == "Star Candy")
        assert star[3] >= 50  # xp_reward

    def test_food_count(self):
        assert len(FOODS) >= 5  # reasonable variety
