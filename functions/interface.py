from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import os

from .distance_detection_class import videoStreaming

class MainWindow (QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.path = os.getcwd()
        path_ui = os.path.join(self.path,r"functions\interface.ui")
        uic.loadUi(path_ui,self)

        self.videoStreaming= videoStreaming()
        self.videoStreaming.imagenfinal.connect(self.cargarvideo)
        self.pushButton.clicked.connect(self.play)
        self.videoStreaming.start()
        self.move(0,0)


    def cargarvideo(self, Image):
        self.label.setPixmap(QPixmap.fromImage(Image))

    def play(self):
        print('play')
