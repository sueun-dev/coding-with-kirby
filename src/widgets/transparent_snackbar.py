from PyQt5.QtWidgets import QWidget, QPushButton, QApplication
from PyQt5.QtGui import QPainter, QColor, QFont, QLinearGradient
from PyQt5.QtCore import Qt, QRectF
from dialogs.ranking_board import RankingBoard


class TransparentSnackBar(QWidget):
    """
    Status bar at the top of the screen showing hunger, level, XP, mood,
    and action buttons.
    """

    BAR_HEIGHT = 36

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._init_ui()

    def _init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        screen = QApplication.primaryScreen().geometry()
        bar_width = min(900, screen.width() - 40)
        x_pos = (screen.width() - bar_width) // 2
        self.setGeometry(x_pos, 8, bar_width, self.BAR_HEIGHT)

        btn_style = (
            "background-color: rgba(255,255,255,30); color: white; "
            "border: 1px solid rgba(255,255,255,60); border-radius: 4px; "
            "font-size: 11px; font-weight: bold; padding: 2px 8px;"
        )

        self.feed_button = QPushButton("Feed", self)
        self.feed_button.setGeometry(bar_width - 280, 6, 60, 24)
        self.feed_button.setStyleSheet(btn_style)
        self.feed_button.clicked.connect(self.controller.spawn_snack)

        self.ranking_button = QPushButton("Ranking", self)
        self.ranking_button.setGeometry(bar_width - 210, 6, 70, 24)
        self.ranking_button.setStyleSheet(btn_style)
        self.ranking_button.clicked.connect(self._show_ranking)

        self.stats_button = QPushButton("Stats", self)
        self.stats_button.setGeometry(bar_width - 130, 6, 55, 24)
        self.stats_button.setStyleSheet(btn_style)
        self.stats_button.clicked.connect(self._show_stats)

        self.quit_button = QPushButton("Quit", self)
        self.quit_button.setGeometry(bar_width - 65, 6, 55, 24)
        self.quit_button.setStyleSheet(
            btn_style.replace("rgba(255,255,255,30)", "rgba(255,80,80,40)")
        )
        self.quit_button.clicked.connect(lambda: self.controller.app.quit())

        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Gradient background
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor(30, 30, 50, 200))
        gradient.setColorAt(1, QColor(50, 30, 70, 200))
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(self.rect()), 8, 8)

        painter.setPen(QColor(255, 255, 255, 220))
        font = QFont("Arial", 11)
        font.setBold(True)
        painter.setFont(font)

        c = self.controller
        mood_emoji = {"happy": "😊", "hungry": "😫", "sleeping": "💤", "excited": "🤩"}.get(c.mood, "😊")
        level = c.level
        xp = c.xp
        xp_needed = c.xp_for_next_level

        # Hunger bar
        hunger_x = 12
        painter.drawText(hunger_x, 0, 200, self.BAR_HEIGHT, Qt.AlignVCenter, f"{mood_emoji} Hunger: {c.hunger}%")

        # XP bar background
        xp_bar_x = 220
        xp_bar_w = 120
        xp_bar_y = 12
        xp_bar_h = 12
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(60, 60, 80, 180))
        painter.drawRoundedRect(xp_bar_x, xp_bar_y, xp_bar_w, xp_bar_h, 4, 4)

        # XP bar fill
        xp_ratio = min(1.0, xp / xp_needed) if xp_needed > 0 else 1.0
        fill_w = int(xp_bar_w * xp_ratio)
        xp_gradient = QLinearGradient(xp_bar_x, 0, xp_bar_x + xp_bar_w, 0)
        xp_gradient.setColorAt(0, QColor(80, 200, 120))
        xp_gradient.setColorAt(1, QColor(0, 255, 150))
        painter.setBrush(xp_gradient)
        painter.drawRoundedRect(xp_bar_x, xp_bar_y, fill_w, xp_bar_h, 4, 4)

        # XP text
        painter.setPen(QColor(255, 255, 255, 220))
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(xp_bar_x, xp_bar_y - 1, xp_bar_w, xp_bar_h + 2, Qt.AlignCenter, f"{xp}/{xp_needed}")

        # Level & stats
        font.setPointSize(11)
        painter.setFont(font)
        size_pct = round(c.pet.scale_factor * 100, 1)
        painter.drawText(355, 0, 250, self.BAR_HEIGHT, Qt.AlignVCenter, f"Lv.{level}  Size: {size_pct}%  Eats: {c.total_eats}")

    def _show_ranking(self):
        board = RankingBoard(self)
        board.exec_()

    def _show_stats(self):
        from dialogs.stats_dialog import StatsDialog
        dialog = StatsDialog(self.controller, self)
        dialog.exec_()
