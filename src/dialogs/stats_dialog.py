from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from utils.utils import ACHIEVEMENTS


class StatsDialog(QDialog):
    """Shows detailed Kirby stats and achievements."""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kirby Stats")
        self.setFixedSize(400, 520)
        self.setStyleSheet("background-color: #1a1a2e; color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        c = controller

        title = QLabel(f"📊 {c.username}'s Kirby")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #FFD700; margin-bottom: 12px;")
        layout.addWidget(title)

        stats = [
            f"Level: {c.level}",
            f"XP: {c.xp} / {c.xp_for_next_level}",
            f"Size: {round(c.pet.scale_factor * 100, 1)}%",
            f"Total Foods Eaten: {c.total_eats}",
            f"Star Candies Eaten: {c.star_eats}",
            f"Times Petted: {c.total_pets}",
            f"Hunger: {c.hunger}%",
            f"Mood: {c.mood}",
        ]
        for s in stats:
            lbl = QLabel(s)
            lbl.setFont(QFont("Arial", 12))
            lbl.setStyleSheet("padding: 2px 0;")
            layout.addWidget(lbl)

        # Achievements section
        ach_title = QLabel("🏆 Achievements")
        ach_title.setFont(QFont("Arial", 14, QFont.Bold))
        ach_title.setStyleSheet("color: #FFD700; margin-top: 16px; margin-bottom: 4px;")
        layout.addWidget(ach_title)

        for ach in ACHIEVEMENTS:
            unlocked = self._check_unlocked(ach, c)
            icon = "✅" if unlocked else "🔒"
            color = "#90EE90" if unlocked else "#666"
            lbl = QLabel(f"{icon} {ach['name']} — {ach['desc']}")
            lbl.setFont(QFont("Arial", 10))
            lbl.setStyleSheet(f"color: {color}; padding: 1px 0;")
            layout.addWidget(lbl)

        layout.addStretch()

    @staticmethod
    def _check_unlocked(ach, controller):
        if ach.get("eats_req", 0) > 0 and controller.total_eats < ach["eats_req"]:
            return False
        if ach.get("level_req", 0) > 0 and controller.level < ach["level_req"]:
            return False
        if ach.get("pets_req", 0) > 0 and controller.total_pets < ach["pets_req"]:
            return False
        if ach.get("star_req", 0) > 0 and controller.star_eats < ach["star_req"]:
            return False
        return True
