import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("INPI Monitor")
    app.setOrganizationName("Personal")

    window = MainWindow()
    window.show()

    # If an XML file is passed as argument, open it automatically
    if len(sys.argv) > 1 and sys.argv[1].endswith(".xml"):
        path = sys.argv[1]
        if os.path.isfile(path):
            window.tab_xml.carregar_arquivo_externo(path)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
