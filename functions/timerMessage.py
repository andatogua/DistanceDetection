from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class TimerMessageBox(QMessageBox):
    def __init__(self, timeout=3, text="", parent=None):
        super(TimerMessageBox, self).__init__(parent)
        self.setWindowTitle("Atención..!!")
        self.setIcon(QMessageBox.Warning)
        self.time_to_wait = timeout
        self.setText("Detección Guardada".format(timeout))
        self.setStandardButtons(QMessageBox.NoButton)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.changeContent)
        self.timer.start()

    def changeContent(self):
        self.setText("Detección Guardada..!".format(self.time_to_wait))
        self.time_to_wait -= 1
        if self.time_to_wait <= 0:
            self.close()

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()