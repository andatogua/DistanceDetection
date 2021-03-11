from PyQt5.QtWidgets import QApplication
from functions.interface import MainWindow

from db.db import crearConexion

import sys

def main():
    if not crearConexion():
        sys.exit(1)
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()