from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *

import os
import numpy as np
from datetime import datetime,date

from .distance_detection_class import videoStreaming
from .canvas import MplCanvas
from db.db import guardar, datosdia,ultimadetdia

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

        available_cameras = QCameraInfo.availableCameras()
        self.statusBar().showMessage(available_cameras[1].description())

        self.videoStreaming= videoStreaming()
        self.videoStreaming.imagenfinal.connect(self.cargarvideo)
        self.videoStreaming.datosguardar.connect(self.guardarregistro)
        self.pushButton.clicked.connect(self.play)
        self.videoStreaming.start()
        self.move(0,0)

        self.dateEdit.setMaximumDate(datetime.now())
        self.dateEdit.setDate(datetime.now())
        self.dateEdit.dateChanged.connect(self.cargarreporte)

        self.grafica_uno = MplCanvas()
        self.ax = self.grafica_uno.axes.twinx()
        self.grafica_dos = MplCanvas()
        self.ax1 = self.grafica_dos.axes.twinx()

        self.gridLayout.addWidget(self.grafica_uno)
        self.gridLayout_2.addWidget(self.grafica_dos)

        self.cargarreporte()

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

    def cargarreporte(self):
        dia = self.dateEdit.date().toString('yyyy-MM-dd')
        ultimadeteccion = ultimadetdia(dia)
        diacompleto = datosdia(dia)
            

        self.grafica_uno.axes.clear()
        self.ax.clear()
        self.grafica_dos.axes.clear()
        self.ax1.clear()

        self.ult_cap_lbl.setText(ultimadeteccion)
        self.dist_prom_lbl.setText("{0:.1f} cm".format(0))
        self.porc_lbl.setText("{0:.1f} %".format(0))
        x = ['00','01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23']
        total = np.zeros(24,dtype=int)
        d_prom = np.zeros(24,dtype=int)
        porc_cumpl = np.zeros(24,dtype=int)
        num_registros = np.zeros(24,dtype=int)
        prom = 0
        cump = 0
        if len(diacompleto) > 0:
            for d in diacompleto:
                i = x.index(d[4])
                total[i] = d[1]/d[3]
                d_prom[i] = (d[2]/d[3])*(150/300)
                porc_cumpl[i] = 100-((d[0]/d[1])*100)
                num_registros[i] = d[3]
                prom += (d_prom[i])/len(diacompleto)
                cump += (porc_cumpl[i])/len(diacompleto)
            x1 = np.arange(len(x))
            p1 = self.grafica_uno.axes.bar(x1-0.15,num_registros,0.3,label='Total')
            self.grafica_uno.axes.set_ylabel('N° Infracciones')
            self.grafica_uno.axes.set_xlabel('Hora del día')
            self.grafica_uno.axes.set_xticks(x1)
            self.grafica_uno.axes.set_xticklabels(x,size='xx-small')

            color = 'tab:red'
            p2 = self.ax.bar(x1+0.15,d_prom,0.3,label='Distancia Prom',color=color)
            self.ax.set_ylabel('Distancia (cm)')
            lines = [p1,p2]
            self.grafica_uno.axes.legend(lines, [l.get_label() for l in lines])
            self.dist_prom_lbl.setText("{0:.1f} cm".format(prom))
            self.porc_lbl.setText("{0:.1f} %".format(cump))

            x2 = np.arange(len(x))
            self.grafica_dos.axes.bar(x2,porc_cumpl,0.3,label='Total C',color='tab:green')
            self.grafica_dos.axes.yaxis.label.set_color('green')
            self.grafica_dos.axes.set_ylabel('% Cumplimiento')
            self.grafica_dos.axes.set_xlabel('Hora del día')
            self.grafica_dos.axes.set_xticks(x2)
            self.grafica_dos.axes.set_xticklabels(x,size='xx-small')

            self.ax1.plot(x2,total,label='# Aproximado de personas',color='blue')
            self.ax1.set_ylabel('# Aproximado de personas')
            self.ax1.yaxis.label.set_color('blue')
            
            


        self.grafica_uno.axes.grid()
        self.grafica_dos.axes.grid()
        self.grafica_uno.draw()
        self.grafica_dos.draw()






