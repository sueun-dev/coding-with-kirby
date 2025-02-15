import os
import json
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtCore import QTimer
from widgets.pet_widget import PetWidget
from widgets.snack_widget import SnackWidget
from widgets.transparent_snackbar import TransparentSnackBar
from utils.utils import STATE_FILE, RANKING_FILE

class MainController:
    """
    Manages interactions between Kirby, food items, and the snack bar.
    Maintains Kirby's hunger level and handles persistent state and ranking.
    """
    def __init__(self, app):
        try:
            self.app = app
            username, ok = QInputDialog.getText(None, "Username", "Enter your username:")
            self.username = username.strip() if ok and username.strip() != "" else "Player"
            self.snacks = []
            self.hunger = 0
            self.pet = PetWidget(self)
            self.snack_bar = TransparentSnackBar(self)
            self.load_state()
            self.hunger_timer = QTimer()
            self.hunger_timer.timeout.connect(self.update_hunger)
            self.hunger_timer.start(1000)
        except Exception as e:
            print("Error in MainController.__init__:", e)

    def spawn_snack(self):
        try:
            new_snack = SnackWidget()
            self.snacks.append(new_snack)
        except Exception as e:
            print("Error in MainController.spawn_snack:", e)

    def remove_snack(self, snack):
        try:
            if snack in self.snacks:
                snack.close()
                self.snacks.remove(snack)
        except Exception as e:
            print("Error in MainController.remove_snack:", e)

    def check_collision(self):
        try:
            for snack in self.snacks[:]:
                if self.pet.frameGeometry().intersects(snack.frameGeometry()):
                    self.remove_snack(snack)
                    self.hunger = max(0, self.hunger - 20)
                    self.snack_bar.update()
                    self.pet.level_up()
        except Exception as e:
            print("Error in MainController.check_collision:", e)

    def update_hunger(self):
        try:
            if self.hunger < 100:
                self.hunger += 2
                if self.hunger > 100:
                    self.hunger = 100
            self.snack_bar.update()
            if self.hunger >= 80 and not self.snacks:
                self.spawn_snack()
        except Exception as e:
            print("Error in MainController.update_hunger:", e)

    def load_state(self):
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, "r") as f:
                    state = json.load(f)
                self.hunger = state.get("hunger", 0)
                self.pet.scale_factor = state.get("scale_factor", 1.0)
                new_width = int(self.pet.original_size.width() * self.pet.scale_factor)
                new_height = int(self.pet.original_size.height() * self.pet.scale_factor)
                self.pet.resize(new_width, new_height)
                self.pet.label.resize(new_width, new_height)
                print("State loaded:", state)
        except Exception as e:
            print("Error loading state:", e)

    def save_state(self):
        try:
            state = {
                "hunger": self.hunger,
                "scale_factor": self.pet.scale_factor
            }
            with open(STATE_FILE, "w") as f:
                json.dump(state, f)
            print("State saved:", state)
            self.update_ranking()
        except Exception as e:
            print("Error saving state:", e)

    def update_ranking(self):
        try:
            ranking = []
            if os.path.exists(RANKING_FILE):
                with open(RANKING_FILE, "r") as f:
                    ranking = json.load(f)
            ranking = [entry for entry in ranking if entry.get("username") != self.username]
            size_percent = round(self.pet.scale_factor * 100, 1)
            level = int((self.pet.scale_factor - 1.0) * 1000)
            ranking.append({
                "username": self.username,
                "size": size_percent,
                "level": level
            })
            with open(RANKING_FILE, "w") as f:
                json.dump(ranking, f)
            print("Ranking updated:", ranking)
        except Exception as e:
            print("Error updating ranking:", e)
