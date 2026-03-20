"""
Shared constants, configuration, and utility functions for the Kirby desktop pet.
"""
import json
import logging
import math
import os
import sys

__version__ = "2.2.0"

logger = logging.getLogger(__name__)

# --- File paths ---
STATE_FILE = "kirby_state.json"
RANKING_FILE = "ranking.json"

# --- UI constants ---
MOOD_EMOJIS = {
    "happy": "😊",
    "hungry": "😫",
    "sleeping": "💤",
    "excited": "🤩",
}

# --- Food definitions: (emoji, name, hunger_restore, xp_reward) ---
FOODS = [
    ("\U0001F34E", "Apple", 10, 5),
    ("\U0001F370", "Cake", 25, 15),
    ("\U0001F354", "Burger", 30, 20),
    ("\U0001F355", "Pizza", 35, 25),
    ("\U0001F363", "Sushi", 20, 30),
    ("\U0001F366", "Ice Cream", 15, 10),
    ("\U00002B50", "Star Candy", 5, 50),
]

# --- Achievement definitions ---
ACHIEVEMENTS = [
    {"id": "first_bite", "name": "First Bite", "desc": "Eat your first food", "eats_req": 1},
    {"id": "hungry_boy", "name": "Hungry Boy", "desc": "Eat 10 foods", "eats_req": 10},
    {"id": "level5", "name": "Growing Up", "desc": "Reach level 5", "level_req": 5},
    {"id": "level10", "name": "Big Kirby", "desc": "Reach level 10", "level_req": 10},
    {"id": "level25", "name": "Mega Kirby", "desc": "Reach level 25", "level_req": 25},
    {"id": "glutton", "name": "Glutton", "desc": "Eat 50 foods", "eats_req": 50},
    {"id": "legend", "name": "Legend", "desc": "Eat 200 foods", "eats_req": 200},
    {"id": "pet_lover", "name": "Pet Lover", "desc": "Pet Kirby 20 times", "pets_req": 20},
    {"id": "star_hunter", "name": "Star Hunter", "desc": "Eat 10 Star Candies", "star_req": 10},
]

# --- Gameplay constants ---
EATS_UNTIL_POOP = 3
POOP_SPAWN_CHANCE = 0.4
RANDOM_EVENT_CHANCE = 0.3
CPU_HIGH_THRESHOLD = 80
MAX_KIRBYS = 6
BREEDING_DISTANCE = 50
BREED_COOLDOWN_FRAMES = 60
POOP_CLEAN_XP = 5
BREED_XP = 30
STAR_FIND_XP = 10
MAX_HUNGER = 100
HUNGER_AUTO_FEED_THRESHOLD = 90
HUNGER_STARVING_THRESHOLD = 95
MAX_POOPS = 20
MAX_SNACKS = 10
MAX_PARTICLES = 500

# --- Physics constants ---
PARTICLE_GRAVITY = 0.08
PARTICLE_DECAY_RANGE = (0.015, 0.035)
PARTICLE_TICK_MS = 16

# --- Timer intervals (ms) ---
HUNGER_TICK_MS = 1000
HUNGER_RATE = 1
AUTO_SAVE_MS = 30_000
MOOD_TICK_MS = 2000
SLEEP_THRESHOLD_S = 60
TRAY_REFRESH_MS = 1000
EVENT_TICK_MS = 15_000
CPU_TICK_MS = 5000
BREED_CHECK_MS = 500
BUBBLE_TICK_MS = 16
FADE_TICK_MS = 30

# --- Pet physics ---
PET_FPS = 60
PET_MAX_SPEED = 2.2
PET_CHASE_MAX_SPEED = 4.0
PET_ACCELERATION = 0.08
PET_FRICTION = 0.96
PET_THROW_FRICTION = 0.985
PET_THROW_GRAVITY = 0.15
PET_FLIP_SPEED_THRESHOLD = 0.3
PET_THROW_STOP_SPEED = 0.5
PET_MAX_THROW_SPEED = 18.0
PET_MIN_THROW_SPEED = 2.0
PET_WANDER_NUDGE_CHANCE = 0.02
PET_REST_SWAY_CHANCE = 0.03
PET_CHASE_ACCEL_MULTIPLIER = 1.8
PET_CHASE_STEERING = 0.12
PET_BOUNCE_FACTOR_NORMAL = 0.5
PET_BOUNCE_FACTOR_THROWN = 0.6
PET_MAX_THROW_BOUNCES = 3

# Baby overrides
BABY_MAX_SPEED = 3.0
BABY_CHASE_MAX_SPEED = 5.0
BABY_ACCELERATION = 0.12
BABY_SCALE = 0.5

# State timers (frames)
WANDER_DURATION = (150, 420)
IDLE_DURATION = (30, 120)
REST_DURATION = (90, 240)
INIT_WANDER_DURATION = (120, 360)

# --- Snack ---
SNACK_SPAWN_MARGIN = 60

# --- Ranking board ---
RANKING_WINDOW_SIZE = (420, 500)
RANKING_REFRESH_MS = 5000
RANKING_ROW_HEIGHT = 44

# --- Username ---
MAX_USERNAME_LENGTH = 20


def xp_for_level(level):
    """XP required to reach the next level. Scales quadratically."""
    return int(50 * (1.3 ** level))


def is_achievement_met(ach, *, total_eats=0, level=0, total_pets=0, star_eats=0):
    """Check if an achievement's requirements are satisfied."""
    if ach.get("eats_req", 0) > 0 and total_eats < ach["eats_req"]:
        return False
    if ach.get("level_req", 0) > 0 and level < ach["level_req"]:
        return False
    if ach.get("pets_req", 0) > 0 and total_pets < ach["pets_req"]:
        return False
    if ach.get("star_req", 0) > 0 and star_eats < ach["star_req"]:
        return False
    return True


def validate_state(state):
    """Validate and sanitize loaded game state. Returns cleaned dict."""
    if not isinstance(state, dict):
        return {}
    cleaned = {}
    cleaned["hunger"] = max(0, min(MAX_HUNGER, int(state.get("hunger", 0))))
    cleaned["xp"] = max(0, int(state.get("xp", 0)))
    cleaned["level"] = max(1, int(state.get("level", 1)))
    cleaned["total_eats"] = max(0, int(state.get("total_eats", 0)))
    cleaned["total_pets"] = max(0, int(state.get("total_pets", 0)))
    cleaned["star_eats"] = max(0, int(state.get("star_eats", 0)))
    try:
        sf = float(state.get("scale_factor", 1.0))
        if not math.isfinite(sf):
            sf = 1.0
    except (TypeError, ValueError):
        sf = 1.0
    cleaned["scale_factor"] = max(0.1, min(10.0, sf))
    achievements = state.get("achievements", [])
    valid_ids = {a["id"] for a in ACHIEVEMENTS}
    cleaned["achievements"] = [a for a in achievements if a in valid_ids]
    return cleaned


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller builds."""
    base_path = getattr(sys, '_MEIPASS', None)
    if base_path is None:
        base_path = os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
        )
    full_path = os.path.join(base_path, relative_path)
    if not os.path.exists(full_path):
        logger.warning("Resource not found: %s", full_path)
    return full_path


def load_json_safe(filepath, default=None):
    """Load JSON file with error handling. Returns *default* on failure."""
    if default is None:
        default = {}
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        logger.error("Failed to load %s: %s", filepath, exc)
        return default


def save_json_safe(filepath, data):
    """Write JSON file atomically with error handling and backup."""
    tmp_path = filepath + ".tmp"
    try:
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        # Atomic rename
        os.replace(tmp_path, filepath)
    except OSError as exc:
        logger.error("Failed to save %s: %s", filepath, exc)
        # Clean up temp file if it exists
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
