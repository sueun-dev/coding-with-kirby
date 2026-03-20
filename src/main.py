import sys
from PyQt5.QtWidgets import QApplication
from core.main_controller import MainController


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running with tray icon
    controller = MainController(app)
    app.aboutToQuit.connect(controller.save_state)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
