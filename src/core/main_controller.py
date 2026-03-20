import os
import json
from PyQt5.QtWidgets import QInputDialog, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer
from widgets.pet_widget import PetWidget
from widgets.snack_widget import SnackWidget
from widgets.transparent_snackbar import TransparentSnackBar
from widgets.thought_bubble import ThoughtBubble
from utils.utils import (
    STATE_FILE, RANKING_FILE, ACHIEVEMENTS, FOODS, xp_for_level, resource_path,
)
from utils.particles import ParticleOverlay


class MainController:
    """
    Central game controller managing Kirby's state, food, mood,
    leveling, achievements, particles, and persistence.
    """

    HUNGER_TICK_MS = 1000
    HUNGER_RATE = 1
    AUTO_SAVE_MS = 30_000
    MOOD_TICK_MS = 2000
    SLEEP_THRESHOLD_S = 60  # seconds idle before sleeping

    def __init__(self, app):
        self.app = app

        username, ok = QInputDialog.getText(None, "Username", "Enter your username:")
        self.username = username.strip() if ok and username.strip() else "Player"

        # State
        self.hunger = 0
        self.xp = 0
        self.level = 1
        self.total_eats = 0
        self.total_pets = 0
        self.star_eats = 0
        self.mood = "happy"
        self.unlocked_achievements = set()
        self.snacks = []
        self._idle_seconds = 0

        # Widgets
        self.particles = ParticleOverlay()
        self.pet = PetWidget(self)
        self.bubble = ThoughtBubble()
        self.snack_bar = TransparentSnackBar(self)

        self._load_state()

        # System tray
        self._setup_tray()

        # Timers
        self._hunger_timer = QTimer()
        self._hunger_timer.timeout.connect(self._hunger_tick)
        self._hunger_timer.start(self.HUNGER_TICK_MS)

        self._mood_timer = QTimer()
        self._mood_timer.timeout.connect(self._mood_tick)
        self._mood_timer.start(self.MOOD_TICK_MS)

        self._autosave_timer = QTimer()
        self._autosave_timer.timeout.connect(self.save_state)
        self._autosave_timer.start(self.AUTO_SAVE_MS)

        self._bubble_timer = QTimer()
        self._bubble_timer.timeout.connect(self._update_bubble_pos)
        self._bubble_timer.start(16)

    @property
    def xp_for_next_level(self):
        return xp_for_level(self.level)

    # --- Food ---

    def spawn_snack(self):
        snack = SnackWidget()
        self.snacks.append(snack)

    def _remove_snack(self, snack):
        if snack in self.snacks:
            snack.close()
            self.snacks.remove(snack)

    def check_collision(self):
        pet_rect = self.pet.frameGeometry()
        for snack in self.snacks[:]:
            if pet_rect.intersects(snack.frameGeometry()):
                self._eat(snack)

    def _eat(self, snack):
        self.hunger = max(0, self.hunger - snack.hunger_restore)
        self._add_xp(snack.xp_reward)
        self.total_eats += 1
        if snack.food_name == "Star Candy":
            self.star_eats += 1

        # Particles
        center = snack.frameGeometry().center()
        self.particles.emit_eat(center.x(), center.y())

        # Thought bubble
        thoughts = [
            f"Yum! {snack.food_name}!",
            "Delicious~",
            f"+{snack.xp_reward} XP!",
            "More food!",
            "Poyo~!",
        ]
        import random
        self.bubble.show_text(random.choice(thoughts), 2000)

        self._remove_snack(snack)
        self._reset_idle()
        self._check_achievements()
        self.snack_bar.update()

    # --- XP / Level ---

    def _add_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_for_next_level:
            self.xp -= self.xp_for_next_level
            self.level += 1
            self._on_level_up()

    def _on_level_up(self):
        # Grow Kirby
        growth = 0.02 / (1 + (self.level - 1) * 0.05)
        self.pet.scale_factor += growth
        self.pet.apply_scale()

        # Particles + bubble
        center = self.pet.frameGeometry().center()
        self.particles.emit_level_up(center.x(), center.y())
        self.bubble.show_text(f"Level {self.level}!", 3000)

    # --- Hunger ---

    def _hunger_tick(self):
        if self.hunger < 100:
            self.hunger = min(100, self.hunger + self.HUNGER_RATE)
        self.snack_bar.update()

        # Auto-spawn food when very hungry
        if self.hunger >= 90 and not self.snacks:
            self.spawn_snack()

    # --- Mood ---

    def _mood_tick(self):
        self._idle_seconds += self.MOOD_TICK_MS / 1000

        if self._idle_seconds >= self.SLEEP_THRESHOLD_S and self.hunger < 60:
            if self.mood != "sleeping":
                self.mood = "sleeping"
                self.bubble.show_text("Zzz...", 5000)
                center = self.pet.frameGeometry().center()
                self.particles.emit_sleep(center.x(), center.y() - 30)
        elif self.hunger >= 80:
            self.mood = "hungry"
            if self.hunger >= 95:
                self.bubble.show_text("I'm starving...", 3000)
        elif self.total_eats > 0 and self.hunger < 30:
            self.mood = "excited"
        else:
            self.mood = "happy"

        # Occasional sleep Z particles
        if self.mood == "sleeping":
            center = self.pet.frameGeometry().center()
            self.particles.emit_sleep(center.x(), center.y() - 30)

        self.snack_bar.update()

    def _reset_idle(self):
        self._idle_seconds = 0
        if self.mood == "sleeping":
            self.mood = "happy"

    # --- Petting ---

    def pet_kirby(self):
        self.total_pets += 1
        self._reset_idle()
        center = self.pet.frameGeometry().center()
        self.particles.emit_heart(center.x(), center.y() - 20)

        import random
        reactions = ["Poyo~!", "♥♥♥", "Hehe~", "That tickles!", "More pets!"]
        self.bubble.show_text(random.choice(reactions), 2500)
        self._check_achievements()

    # --- Achievements ---

    def _check_achievements(self):
        for ach in ACHIEVEMENTS:
            if ach["id"] in self.unlocked_achievements:
                continue
            if self._is_achievement_met(ach):
                self.unlocked_achievements.add(ach["id"])
                center = self.pet.frameGeometry().center()
                self.particles.emit_achievement(center.x(), center.y())
                self.bubble.show_text(f"🏆 {ach['name']}!", 4000)

    def _is_achievement_met(self, ach):
        if ach.get("eats_req", 0) > 0 and self.total_eats < ach["eats_req"]:
            return False
        if ach.get("level_req", 0) > 0 and self.level < ach["level_req"]:
            return False
        if ach.get("pets_req", 0) > 0 and self.total_pets < ach["pets_req"]:
            return False
        if ach.get("star_req", 0) > 0 and self.star_eats < ach["star_req"]:
            return False
        return True

    # --- Bubble follow ---

    def _update_bubble_pos(self):
        pos = self.pet.pos()
        self.bubble.follow(pos.x(), pos.y())

    # --- System Tray ---

    def _setup_tray(self):
        icon_path = resource_path("images/Y3il.gif")
        self.tray = QSystemTrayIcon(QIcon(icon_path), self.app)

        menu = QMenu()
        feed_action = QAction("Feed Kirby", menu)
        feed_action.triggered.connect(self.spawn_snack)
        menu.addAction(feed_action)

        stats_action = QAction("Stats", menu)
        stats_action.triggered.connect(self._show_stats_from_tray)
        menu.addAction(stats_action)

        menu.addSeparator()
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self.app.quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.setToolTip(f"Kirby — Lv.{self.level}")
        self.tray.show()

    def _show_stats_from_tray(self):
        from dialogs.stats_dialog import StatsDialog
        dialog = StatsDialog(self, None)
        dialog.exec_()

    # --- Persistence ---

    def _load_state(self):
        if not os.path.exists(STATE_FILE):
            return
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
        self.hunger = state.get("hunger", 0)
        self.xp = state.get("xp", 0)
        self.level = state.get("level", 1)
        self.total_eats = state.get("total_eats", 0)
        self.total_pets = state.get("total_pets", 0)
        self.star_eats = state.get("star_eats", 0)
        self.unlocked_achievements = set(state.get("achievements", []))
        self.pet.scale_factor = state.get("scale_factor", 1.0)
        self.pet.apply_scale()

    def save_state(self):
        state = {
            "hunger": self.hunger,
            "xp": self.xp,
            "level": self.level,
            "total_eats": self.total_eats,
            "total_pets": self.total_pets,
            "star_eats": self.star_eats,
            "scale_factor": self.pet.scale_factor,
            "achievements": list(self.unlocked_achievements),
        }
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        self._update_ranking()
        self.tray.setToolTip(f"Kirby — Lv.{self.level}")

    def _update_ranking(self):
        ranking = []
        if os.path.exists(RANKING_FILE):
            with open(RANKING_FILE, "r") as f:
                ranking = json.load(f)
        ranking = [e for e in ranking if e.get("username") != self.username]
        ranking.append({
            "username": self.username,
            "size": round(self.pet.scale_factor * 100, 1),
            "level": self.level,
        })
        with open(RANKING_FILE, "w") as f:
            json.dump(ranking, f, indent=2)
