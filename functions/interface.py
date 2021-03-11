from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import os

from .distance_detection_class import videoStreaming
from db.db import guardar

class TimerMessageBox(QMessageBox):
    def __init__(self, timeout=3, parent=None):
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

class MainWindow (QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.path = os.getcwd()
        path_ui = os.path.join(self.path,r"functions\interface.ui")
        uic.loadUi(path_ui,self)

        self.videoStreaming= videoStreaming()
        self.videoStreaming.imagenfinal.connect(self.cargarvideo)
        self.videoStreaming.datosguardar.connect(self.guardarregistro)
        self.pushButton.clicked.connect(self.play)
        self.videoStreaming.start()
        self.move(0,0)

    def mostrarmensaje(self):
        mensaje = TimerMessageBox(3,self)
        mensaje.exec_()

    def cargarvideo(self, Image):
        self.label.setPixmap(QPixmap.fromImage(Image))

    def guardarregistro(self,personas,incumplidos,dist_promedio,fecha):
        if (guardar(incumplidos,personas,dist_promedio,fecha)):
            self.mostrarmensaje()

    def play(self):
        print('play')
