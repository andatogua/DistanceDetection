from PyQt5.QtWidgets import QApplication, QMessageBox
from functions.interface import MainWindow

from db.db import crearConexion

import sys

from functions.camlist import checkCam

def main():
    available,_ = checkCam()
    if not crearConexion():
        sys.exit(1)
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    if not available:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error de cámara")
        msg.setWindowTitle("Error")
        msg.setInformativeText('Verifique la conexión y reinicie el sistema')
        msg.exec_()
        sys.exit(1)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()