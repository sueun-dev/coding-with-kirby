import os
import json
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem
from utils.utils import RANKING_FILE

class RankingBoard(QDialog):
    """
    A dialog that displays the ranking of all players.
    Auto-refreshes every 5 seconds to simulate online updates.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ranking Board")
        self.setGeometry(100, 100, 500, 400)
        self.layout = QVBoxLayout(self)
        self.list_widget = QListWidget(self)
        self.layout.addWidget(self.list_widget)
        self.refresh_ranking()
        from PyQt5.QtCore import QTimer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_ranking)
        self.timer.start(5000)

    def refresh_ranking(self):
        try:
            self.list_widget.clear()
            if os.path.exists(RANKING_FILE):
                with open(RANKING_FILE, "r") as f:
                    ranking = json.load(f)
                ranking.sort(key=lambda entry: entry.get("level", 0), reverse=True)
                for entry in ranking:
                    username = entry.get("username", "Unknown")
                    size = entry.get("size", 100)
                    level = entry.get("level", 0)
                    item_text = f"{username}: Size: {size}%  Level: {level}"
                    self.list_widget.addItem(QListWidgetItem(item_text))
            else:
                self.list_widget.addItem("No ranking data available.")
        except Exception as e:
            print("Error in RankingBoard.refresh_ranking:", e)
