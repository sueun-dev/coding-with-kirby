import sys
import os

STATE_FILE = "kirby_state.json"
RANKING_FILE = "ranking.json"

# Food definitions: (image_index, name, hunger_restore, xp_reward)
FOODS = [
    (1, "Apple", 10, 5),
    (2, "Cake", 25, 15),
    (3, "Burger", 30, 20),
    (4, "Pizza", 35, 25),
    (5, "Sushi", 20, 30),
    (6, "Ice Cream", 15, 10),
    (7, "Star Candy", 5, 50),
]

ACHIEVEMENTS = [
    {"id": "first_bite", "name": "First Bite", "desc": "Eat your first food", "xp_req": 0, "eats_req": 1},
    {"id": "hungry_boy", "name": "Hungry Boy", "desc": "Eat 10 foods", "xp_req": 0, "eats_req": 10},
    {"id": "level5", "name": "Growing Up", "desc": "Reach level 5", "level_req": 5, "eats_req": 0},
    {"id": "level10", "name": "Big Kirby", "desc": "Reach level 10", "level_req": 10, "eats_req": 0},
    {"id": "level25", "name": "Mega Kirby", "desc": "Reach level 25", "level_req": 25, "eats_req": 0},
    {"id": "glutton", "name": "Glutton", "desc": "Eat 50 foods", "xp_req": 0, "eats_req": 50},
    {"id": "legend", "name": "Legend", "desc": "Eat 200 foods", "xp_req": 0, "eats_req": 200},
    {"id": "pet_lover", "name": "Pet Lover", "desc": "Pet Kirby 20 times", "pets_req": 20, "eats_req": 0},
    {"id": "star_hunter", "name": "Star Hunter", "desc": "Eat 10 Star Candies", "star_req": 10, "eats_req": 0},
]


def xp_for_level(level):
    """XP required to reach the next level. Scales quadratically."""
    return int(50 * (1.3 ** level))


def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', None)
    if base_path is None:
        base_path = os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
        )
    return os.path.join(base_path, relative_path)
