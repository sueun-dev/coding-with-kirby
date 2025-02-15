import sys
from PyQt5.QtWidgets import QApplication
from core.main_controller import MainController

def main():
    try:
        app = QApplication(sys.argv)
        controller = MainController(app)
        app.aboutToQuit.connect(controller.save_state)
        sys.exit(app.exec_())
    except Exception as e:
        print("Error in main:", e)

if __name__ == '__main__':
    main()
