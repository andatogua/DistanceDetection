#importar módulos
import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


import numpy as np
import cv2
import os

from scipy.spatial import distance
from datetime import datetime
from .timerMessage import TimerMessageBox

class videoStreaming(QThread):
	imagenfinal=pyqtSignal(QImage)
	datosguardar=pyqtSignal(int,int,float,str)
	error = pyqtSignal(bool)

	def dibujarcajas(self,idxs,cajas,confianzas,fotograma,contador):

		resultados = [] #contiene la lista de mejores predicciones
		infractores = set()
		sumaDistanciaPromedio = 0.0
		contador += 1
		if len(idxs) > 0:
			for i in idxs.flatten():
				x , y, ancho, alto = cajas[i] #coordenadas de las cajas
				#coordenadas de los pies
				piesx = x + ancho/2
				piesy = y + alto
				resultados.append((confianzas[i],(x,y,x+ancho,y+alto),(piesx,piesy)))
		#debe existir almenos 2  personas
			if len(resultados) >= 2:
				centroides = np.array([r[2] for r in resultados])
				D = distance.cdist(centroides,centroides, metric='euclidean')
				#método para leer sólo la mitad de la matriz cuadrada
				for i in range(0,D.shape[0]-1):
					for j in range(i+1,D.shape[1]):
						if D[i,j] < 300: #370 es un valor referencia
							infractores.add(i)
							infractores.add(j)
							sumaDistanciaPromedio += D[i,j]
							contador = 0 #cuenta fotogramas si no hay detecciones
			for (i,(c,cajon,_)) in enumerate(resultados): #i es el mismo indice tanto para D como para resultados
				if i in infractores:					  #porque los centroides son obtenidos de ese arreglo
					color = (0,0,255) #BGR
				else:
					color = (0,255,0) #BGR
				x1,y1,x2,y2 = cajon #coordenadas para dibuhar caja
				texto = "{}: {:.1f}%".format("Persona",c*100)
				cv2.rectangle(fotograma,(x1,y1),(x2,y2),color, 1)
				cv2.putText(fotograma,texto,(x1,y1-5),cv2.FONT_HERSHEY_SIMPLEX,	0.5,color,1)
			cv2.putText(fotograma, "Personas: {0}".format(len(resultados)), (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)
			cv2.putText(fotograma, "Incumplidas: {0}".format(len(infractores)), (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
			cv2.putText(fotograma, "Cumplidas: {0}".format(len(resultados)-len(infractores)), (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)        

			if len(infractores) != 0:
				sumaDistanciaPromedio = sumaDistanciaPromedio /len(infractores)
		return fotograma, len(resultados),len(infractores),sumaDistanciaPromedio, contador

	def deteccion(self,fotograma,red,capasRedimension,confianza,umbral):

		alto,ancho = fotograma.shape[:2] #(640,480,3)
		#capturamos el blob de la imagen
		blob = cv2.dnn.blobFromImage(fotograma, 1/255, (224,224), swapRB=True, crop=False )
		
		red.setInput(blob)
		salidas = red.forward(capasRedimension)
		
		cajas = []
		confianzas = []
		clases = []

		for salida in salidas:
			for deteccion in salida:
				puntajes = deteccion[5:]
				idclase = np.argmax(puntajes)
				conf = puntajes[idclase]
				if conf > confianza and idclase == 0:
					caja = deteccion[0:4] * np.array([ancho, alto, ancho, alto])
					cx,cy,an,al=caja.astype('int')
					#obetener punto superior izquierdo de la caja que servirá para graficar el rectangulo
					x = int(cx - an/2)
					y = int(cy - al/2)

					#se añaden a la lista de cajas
					cajas.append([x,y,int(an),int(al)])

					#se añade a la lista de confianzas
					confianzas.append(float(conf))
		idxs = cv2.dnn.NMSBoxes(cajas, confianzas, confianza, umbral) #devuelve los indices de las mejores predicciones
		return idxs,cajas,confianzas

	def inicio(self):
		#definir variables
		red = cv2.dnn.readNetFromDarknet('model/yolov3.cfg','model/yolov3.weights') #cargamos la red
		

		#verificamos si existe GPU conectada
		indiceGPU = cv2.cuda.getDevice()#se obtiene el indice 0 o mayor si existe, si no existe devuelve -1

		if indiceGPU >= 0:
			red.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)	#activar funciones cumputacionales de CUDA
			red.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
			print('use CUDA')

		numeroDeCapas = red.getLayerNames() #obtiene las capas de deteccion a 3 escalas
		capasRedimension =[numeroDeCapas[i[0]-1] for i in red.getUnconnectedOutLayers()]

		#iniciar captura de video
		video = cv2.VideoCapture(0)
		video.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
		video.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
		return video, red, capasRedimension

	def run(self):
		confianza = 0.5
		umbral = 0.4
		contador = 0 

		#variables temporales
		temp_personas = 0
		temp_incumplidas = 0
		temp_dist_promedio = 0.0
		contador = 0
		guardar = False
		av = True

		video,red,capasRedimension = self.inicio()
		#renderizar video en fotogramas
		while video.isOpened():
			available,fotograma = video.read()
			try:
				
				idxs,cajas,confianzas = self.deteccion(fotograma,red,capasRedimension,confianza,umbral)
				fotograma,_personas,_infractores,_dist_promedio,contador = self.dibujarcajas(idxs,cajas,confianzas,fotograma,contador)

				#enviar la señal a la aplicación con la imagen como argumento
				imagen = cv2.cvtColor(fotograma, cv2.COLOR_BGR2RGB)
				imagen = cv2.flip(imagen,1)
				imagenaplanada= cv2.flip(imagen,1)
				qtImagen= QImage(imagenaplanada.data, imagenaplanada.shape[1], imagenaplanada.shape[0], QImage.Format_RGB888)
				img= qtImagen.scaled(1280,720,Qt.KeepAspectRatio)
				self.imagenfinal.emit(img)
				
				"""
				condicional que permite actualizar los datos temporales antes de guardar los registros
				mientras existan detecciones no se emite la señal para guardar en BD
				debe pasar 15 fotogramas para emitir la señal
				se renderiza a 5fps 

				guarda la mayor cantidad de infractores posibles y no cada vez que aparezce uno
				"""
				if _infractores > temp_incumplidas:
					temp_personas = _personas
					temp_incumplidas = _infractores
					temp_dist_promedio = _dist_promedio
					fecha = str(datetime.now())
					guardar = True
				if contador == 15 and guardar:
					#print(temp_personas,temp_incumplidas,temp_dist_promedio,fecha)
					self.datosguardar.emit(temp_personas,temp_incumplidas,temp_dist_promedio,fecha)
					
					contador = 0
					temp_dist_promedio = 0.0
					temp_incumplidas = 0
					temp_personas = 0
					guardar = False
			except:
				self.error.emit(True)
				break
			
				

