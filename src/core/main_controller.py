"""Central game controller — all UI lives in the macOS menu-bar tray icon."""

from __future__ import annotations

import datetime
import logging
import math
import random

import psutil
from PyQt5.QtWidgets import QApplication, QInputDialog
from PyQt5.QtCore import QTimer, QPointF

from widgets.pet_widget import PetWidget
from widgets.snack_widget import SnackWidget
from widgets.poop_widget import PoopWidget
from widgets.thought_bubble import ThoughtBubble
from utils.utils import (
    STATE_FILE, RANKING_FILE, ACHIEVEMENTS,
    xp_for_level, is_achievement_met, validate_state,
    load_json_safe, save_json_safe,
    EATS_UNTIL_POOP, POOP_SPAWN_CHANCE, RANDOM_EVENT_CHANCE,
    CPU_HIGH_THRESHOLD, MAX_KIRBYS, BREEDING_DISTANCE,
    BREED_COOLDOWN_FRAMES, POOP_CLEAN_XP, BREED_XP, STAR_FIND_XP,
    MAX_HUNGER, HUNGER_SLEEP_THRESHOLD, HUNGER_HUNGRY_THRESHOLD,
    HUNGER_EXCITED_THRESHOLD, HUNGER_AUTO_FEED_THRESHOLD,
    HUNGER_STARVING_THRESHOLD,
    MAX_POOPS, MAX_SNACKS, BABY_SCALE, MAX_USERNAME_LENGTH,
    MAX_LEVELUPS_PER_TICK, BABY_SPAWN_MARGIN, BABY_SPAWN_VX_RANGE, BABY_SPAWN_VY,
    EVENT_TRIP_HOP, EVENT_DANCE_HSPEED, EVENT_DANCE_HOP,
    EVENT_SNEEZE_PUSH, EVENT_SNEEZE_HOP, EVENT_HICCUP_HOP,
    PET_GROWTH_BASE, PET_GROWTH_DIMINISH,
    HUNGER_TICK_MS, HUNGER_RATE, AUTO_SAVE_MS, MOOD_TICK_MS,
    SLEEP_THRESHOLD_S, TRAY_REFRESH_MS, EVENT_TICK_MS,
    CPU_TICK_MS, BREED_CHECK_MS, BUBBLE_TICK_MS,
)
from core.tray_menu import TrayPresenter
from utils.particles import ParticleOverlay

logger = logging.getLogger(__name__)


class MainController:
    """Central game controller.

    Owns the game state and every game system (food, XP, hunger, mood,
    achievements, poop, random events, CPU monitor, breeding, persistence).
    The macOS menu-bar UI is delegated to :class:`TrayPresenter`.
    """

    def __init__(self, app: QApplication) -> None:
        self.app = app
        self.username = self._ask_username()

        # Game state
        self.hunger = 0
        self.xp = 0
        self.level = 1
        self.total_eats = 0
        self.total_pets = 0
        self.star_eats = 0
        self.mood = "happy"
        self.unlocked_achievements: set[str] = set()
        self.snacks: list[SnackWidget] = []
        self.poops: list[PoopWidget] = []
        self._idle_seconds: float = 0.0
        self._eats_since_poop = 0
        self._cpu_percent = 0.0
        self._breed_cooldown = 0

        # Widgets
        self.particles = ParticleOverlay()
        self.pet = PetWidget(self)
        self.extra_pets: list[PetWidget] = []
        self.bubble = ThoughtBubble()

        self._load_state()
        self._setup_tray()
        self._init_timers()
        self._time_greeting()

    # --- Initialization helpers ---

    @staticmethod
    def _ask_username() -> str:
        username, ok = QInputDialog.getText(None, "Username", "Enter your username:")
        name = username.strip() if ok and username.strip() else "Player"
        return name[:MAX_USERNAME_LENGTH]

    def _init_timers(self) -> None:
        """Create and start all game timers."""
        timer_defs = [
            (HUNGER_TICK_MS,  self._hunger_tick),
            (MOOD_TICK_MS,    self._mood_tick),
            (AUTO_SAVE_MS,    self.save_state),
            (BUBBLE_TICK_MS,  self._update_bubble_pos),
            (TRAY_REFRESH_MS, self.tray.refresh),
            (EVENT_TICK_MS,   self._random_event),
            (CPU_TICK_MS,     self._cpu_tick),
            (BREED_CHECK_MS,  self._check_breeding),
        ]
        self._timers: list[QTimer] = []
        for interval_ms, callback in timer_defs:
            timer = QTimer()
            timer.timeout.connect(callback)
            timer.start(interval_ms)
            self._timers.append(timer)

    def stop_all_timers(self) -> None:
        """Stop every timer and tear down widgets cleanly. Called on quit."""
        for timer in self._timers:
            timer.stop()
        # Tear down widget-owned timers / movies.
        self.particles.stop()
        self.bubble.stop()
        self.pet.stop()
        for baby in self.extra_pets:
            baby.stop()
            baby.close()
        for snack in self.snacks:
            snack.close()
        for poop in self.poops:
            poop.close()

    # --- Tray (macOS menu bar) ---

    def _setup_tray(self) -> None:
        self.tray = TrayPresenter(self, self.app)

    def show_ranking(self) -> None:
        from dialogs.ranking_board import RankingBoard
        RankingBoard().exec_()

    def show_achievements(self) -> None:
        from dialogs.stats_dialog import StatsDialog
        StatsDialog(self).exec_()

    # --- Properties ---

    @property
    def xp_for_next_level(self) -> int:
        return xp_for_level(self.level)

    @property
    def cpu_percent(self) -> float:
        """Most recent CPU-load reading, in percent."""
        return self._cpu_percent

    # --- Food ---

    def spawn_snack(self) -> None:
        if len(self.snacks) >= MAX_SNACKS:
            return  # prevent snack spam
        self.snacks.append(SnackWidget())

    def _remove_snack(self, snack: SnackWidget) -> None:
        if snack in self.snacks:
            snack.close()
            self.snacks.remove(snack)

    def check_collision(self) -> None:
        pet_rect = self.pet.frameGeometry()
        for snack in self.snacks[:]:
            if pet_rect.intersects(snack.frameGeometry()):
                self._eat(snack)

        for baby in self.extra_pets:
            baby_rect = baby.frameGeometry()
            for snack in self.snacks[:]:
                if baby_rect.intersects(snack.frameGeometry()):
                    self._eat(snack)
                    break

    def _eat(self, snack: SnackWidget) -> None:
        self.hunger = max(0, self.hunger - snack.hunger_restore)
        self._add_xp(snack.xp_reward)
        self.total_eats += 1
        self._eats_since_poop += 1
        if snack.food_name == "Star Candy":
            self.star_eats += 1

        center = snack.frameGeometry().center()
        self.particles.emit_eat(center.x(), center.y())

        thoughts = [
            f"Yum! {snack.food_name}!",
            "Delicious~",
            f"+{snack.xp_reward} XP!",
            "More food!",
            "Poyo~!",
        ]
        self.bubble.show_text(random.choice(thoughts), 2000)
        self._remove_snack(snack)
        self._reset_idle()
        self._check_achievements()

        if self._eats_since_poop >= EATS_UNTIL_POOP and random.random() < POOP_SPAWN_CHANCE:
            self._spawn_poop()

    # --- XP / Level ---

    def _add_xp(self, amount: int) -> None:
        self.xp += amount
        count = 0
        while self.xp >= self.xp_for_next_level and count < MAX_LEVELUPS_PER_TICK:
            needed = self.xp_for_next_level
            if needed <= 0:
                break
            self.xp -= needed
            self.level += 1
            self._on_level_up()
            count += 1

    def _on_level_up(self) -> None:
        growth = PET_GROWTH_BASE / (1 + (self.level - 1) * PET_GROWTH_DIMINISH)
        self.pet.scale_factor += growth
        self.pet.apply_scale()

        center = self.pet.frameGeometry().center()
        self.particles.emit_level_up(center.x(), center.y())
        self.bubble.show_text(f"Level {self.level}!", 3000)

    # --- Hunger ---

    def _hunger_tick(self) -> None:
        if self.hunger < MAX_HUNGER:
            self.hunger = min(MAX_HUNGER, self.hunger + HUNGER_RATE)
        # Auto-feed only if no snacks already pending
        if self.hunger >= HUNGER_AUTO_FEED_THRESHOLD and not self.snacks:
            self.spawn_snack()

    # --- Mood ---

    def _mood_tick(self) -> None:
        self._idle_seconds += MOOD_TICK_MS / 1000

        if self._idle_seconds >= SLEEP_THRESHOLD_S and self.hunger < HUNGER_SLEEP_THRESHOLD:
            if self.mood != "sleeping":
                self.mood = "sleeping"
                self.bubble.show_text("Zzz...", 5000)
        elif self.hunger >= HUNGER_HUNGRY_THRESHOLD:
            self.mood = "hungry"
            if self.hunger >= HUNGER_STARVING_THRESHOLD:
                self.bubble.show_text("I'm starving...", 3000)
        elif self.total_eats > 0 and self.hunger < HUNGER_EXCITED_THRESHOLD:
            self.mood = "excited"
        else:
            self.mood = "happy"

        # Emit Zzz particles on every sleeping tick (covers the transition tick).
        if self.mood == "sleeping":
            self._emit_sleep_particles()

    def _emit_sleep_particles(self) -> None:
        center = self.pet.frameGeometry().center()
        self.particles.emit_sleep(center.x(), center.y() - 30)

    def _reset_idle(self) -> None:
        self._idle_seconds = 0.0
        if self.mood == "sleeping":
            self.mood = "happy"

    # --- Petting ---

    def pet_kirby(self) -> None:
        self.total_pets += 1
        self._reset_idle()
        center = self.pet.frameGeometry().center()
        self.particles.emit_heart(center.x(), center.y() - 20)

        reactions = ["Poyo~!", "♥♥♥", "Hehe~", "That tickles!", "More pets!"]
        self.bubble.show_text(random.choice(reactions), 2500)
        self._check_achievements()

    # --- Achievements ---

    def _check_achievements(self) -> None:
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
                center = self.pet.frameGeometry().center()
                self.particles.emit_achievement(center.x(), center.y())
                self.bubble.show_text(f"🏆 {ach['name']}!", 4000)

    # --- Poop ---

    def _spawn_poop(self) -> None:
        # Reset the eat-counter whenever a poop is attempted — even at the cap —
        # so it never grows unbounded while MAX_POOPS poops are on screen.
        self._eats_since_poop = 0
        if len(self.poops) >= MAX_POOPS:
            return  # prevent infinite poop
        pos = self.pet.pos()
        poop = PoopWidget(pos.x() + self.pet.width() // 2, pos.y() + self.pet.height(), self)
        self.poops.append(poop)
        center = poop.frameGeometry().center()
        self.particles.emit_poop(center.x(), center.y())
        self.bubble.show_text(random.choice(["Oops...", "Uh oh~", "Excuse me!"]), 2000)

    def clean_poop(self, poop: PoopWidget) -> None:
        if poop in self.poops:
            center = poop.frameGeometry().center()  # capture before close()
            poop.close()
            self.poops.remove(poop)
            self._add_xp(POOP_CLEAN_XP)
            self.particles.emit_eat(center.x(), center.y())
            self.bubble.show_text(random.choice(["Thanks!", "Clean~!", "Sparkle!"]), 1500)

    # --- Random Events ---

    def _random_event(self) -> None:
        if self.mood == "sleeping":
            return
        if random.random() > RANDOM_EVENT_CHANCE:
            return

        events = [
            self._event_trip,
            self._event_find_star,
            self._event_dance,
            self._event_sneeze,
            self._event_hiccup,
        ]
        random.choice(events)()

    def _event_trip(self) -> None:
        self.bubble.show_text("*trips* Poyo!", 2500)
        center = self.pet.frameGeometry().center()
        self.particles.emit_eat(center.x(), center.y())
        self.pet.vel.setY(EVENT_TRIP_HOP)

    def _event_find_star(self) -> None:
        self._add_xp(STAR_FIND_XP)
        self.bubble.show_text(f"Found a star! +{STAR_FIND_XP} XP!", 3000)
        center = self.pet.frameGeometry().center()
        self.particles.emit_achievement(center.x(), center.y())

    def _event_dance(self) -> None:
        self.bubble.show_text("Dance time!", 3000)
        center = self.pet.frameGeometry().center()
        self.pet.vel = QPointF(
            random.choice([-EVENT_DANCE_HSPEED, EVENT_DANCE_HSPEED]), EVENT_DANCE_HOP
        )
        for _ in range(6):
            self.particles.emit_heart(
                center.x() + random.randint(-30, 30),
                center.y() + random.randint(-30, 30),
            )

    def _event_sneeze(self) -> None:
        self.bubble.show_text("Achoo!", 2000)
        direction = -EVENT_SNEEZE_PUSH if self.pet.is_facing_right else EVENT_SNEEZE_PUSH
        self.pet.vel = QPointF(direction, EVENT_SNEEZE_HOP)

    def _event_hiccup(self) -> None:
        self.bubble.show_text("*hic* ...hic!", 2500)
        self.pet.vel.setY(EVENT_HICCUP_HOP)

    # --- CPU Monitor ---

    def _cpu_tick(self) -> None:
        self._cpu_percent = psutil.cpu_percent(interval=None)
        if self._cpu_percent > CPU_HIGH_THRESHOLD:
            self.bubble.show_text(
                random.choice(["So hot...", "CPU burning!", "Need rest...", "Working hard!"]),
                3000,
            )
            center = self.pet.frameGeometry().center()
            self.particles.emit_sweat(center.x(), center.y())

    # --- Time-based ---

    def _time_greeting(self) -> None:
        hour = datetime.datetime.now().hour
        greetings = [
            (range(5, 9),   "Good morning! Let's code!"),
            (range(9, 12),  "Time to be productive!"),
            (range(12, 14), "Lunch time? Feed me!"),
            (range(14, 18), "Afternoon coding session!"),
            (range(18, 22), "Evening already? Keep going!"),
        ]
        msg = "So late... still coding?"
        for hours, greeting in greetings:
            if hour in hours:
                msg = greeting
                break
        QTimer.singleShot(2000, lambda: self.bubble.show_text(msg, 4000))

    # --- Breeding ---

    def _check_breeding(self) -> None:
        if self._breed_cooldown > 0:
            self._breed_cooldown -= 1
            return

        all_pets = [self.pet] + self.extra_pets
        if len(all_pets) < 2 or len(all_pets) >= MAX_KIRBYS:
            return

        for i in range(len(all_pets)):
            for j in range(i + 1, len(all_pets)):
                ac = all_pets[i].frameGeometry().center()
                bc = all_pets[j].frameGeometry().center()
                if math.hypot(ac.x() - bc.x(), ac.y() - bc.y()) < BREEDING_DISTANCE:
                    self._breed(all_pets[i], all_pets[j])
                    return

    def _breed(self, parent_a: PetWidget, parent_b: PetWidget) -> None:
        # Re-check limit (guard against concurrent breeding)
        if len([self.pet] + self.extra_pets) >= MAX_KIRBYS:
            return
        self._breed_cooldown = BREED_COOLDOWN_FRAMES

        screen = QApplication.primaryScreen().geometry()
        max_x = screen.width() - BABY_SPAWN_MARGIN
        max_y = screen.height() - BABY_SPAWN_MARGIN
        mid_x = max(0, min(max_x, (parent_a.pos().x() + parent_b.pos().x()) / 2))
        mid_y = max(0, min(max_y, (parent_a.pos().y() + parent_b.pos().y()) / 2))

        for _ in range(12):
            self.particles.emit_heart(
                int(mid_x) + random.randint(-20, 20),
                int(mid_y) + random.randint(-20, 20),
            )

        self.bubble.show_text(
            random.choice(["A baby Kirby!", "New friend!", "Poyo poyo~!", "Family grows!"]),
            4000,
        )

        baby = PetWidget(self, is_baby=True)
        baby.scale_factor = BABY_SCALE
        baby.apply_scale()
        baby.move(int(mid_x), int(mid_y))
        baby.pos_f = QPointF(mid_x, mid_y)
        baby.vel = QPointF(random.uniform(*BABY_SPAWN_VX_RANGE), BABY_SPAWN_VY)
        self.extra_pets.append(baby)

        self._add_xp(BREED_XP)

    # --- Bubble follow ---

    def _update_bubble_pos(self) -> None:
        pos = self.pet.pos()
        self.bubble.follow(pos.x(), pos.y())

    # --- Persistence ---

    def _load_state(self) -> None:
        raw = load_json_safe(STATE_FILE, default={})
        if not raw:
            return
        state = validate_state(raw)
        self.hunger = state["hunger"]
        self.xp = state["xp"]
        self.level = state["level"]
        self.total_eats = state["total_eats"]
        self.total_pets = state["total_pets"]
        self.star_eats = state["star_eats"]
        self.unlocked_achievements = set(state["achievements"])
        self.pet.scale_factor = state["scale_factor"]
        self.pet.apply_scale()

    def save_state(self) -> None:
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
        save_json_safe(STATE_FILE, state)
        self._update_ranking()

    def _update_ranking(self) -> None:
        ranking = load_json_safe(RANKING_FILE, default=[])
        if not isinstance(ranking, list):
            ranking = []
        # Drop our previous entry and any malformed (non-dict) rows.
        ranking = [
            e for e in ranking
            if isinstance(e, dict) and e.get("username") != self.username
        ]
        ranking.append({
            "username": self.username,
            "size": round(self.pet.scale_factor * 100, 1),
            "level": self.level,
        })
        save_json_safe(RANKING_FILE, ranking)
