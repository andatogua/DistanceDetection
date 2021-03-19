import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


import numpy as np
import cv2
import os

from scipy.spatial import distance
from datetime import datetime

class videoStreaming(QThread):
    imagenfinal=pyqtSignal(QImage)
    datosguardar=pyqtSignal(int,int,float,str)



    def extraer_cajas_confianzas_idsclases(self,salidas, confianza, ancho, alto):
        cajas = []
        lista_confianza = []
        ids_clases = []

        for salida in salidas:
            for deteccion in salida:            
                # Extraer los puntajes, los id de las clases, y la confianza de la predicción
                puntajes = deteccion[5:]
                id_clase = np.argmax(puntajes)
                conf = puntajes[id_clase]
                # se muestra sólo si supera el nivel de confianza establecido
                if conf > confianza and id_clase == 0:
                    # redimensionar la caja que enmarcará a la persona
                    caja = deteccion[0:4] * np.array([ancho, alto, ancho, alto])
                    centroX, centroY, _ancho, _alto = caja.astype('int')

                    # obtener las coordenadas superior izquierda para dibujar el rectángulo
                    x = int(centroX - (_ancho / 2))
                    y = int(centroY - (_alto / 2))

                    #las coordenadas se añaden a la lista de cajas
                    cajas.append([x, y, int(_ancho), int(_alto)])
                    
                    #se añaden los niveles de confianza obtenidos
                    lista_confianza.append(float(conf))
                    
                    #se añaden las identificaciones de las clases obtenidas
                    ids_clases.append(id_clase)

        return cajas, lista_confianza, ids_clases


    def dibujar_cajas(self,imagen, cajas, lista_confianza, ids_clases, idxs, color,contador):
        resultados = []
        infractores = set()
        dist_promedio = 0.0
        contador += 1
        if len(idxs) > 0:
            for i in idxs.flatten():
                # extraer las coordenadas de las cajas
                x, y = cajas[i][0], cajas[i][1]
                ancho, alto = cajas[i][2], cajas[i][3]
                #posición de los pies
                cx = x + (ancho/2)
                cy = y + (alto)
                # bloque añadido
                r = (lista_confianza[i], (x, y, x + ancho, y + alto), (cx,cy))
                resultados.append(r)
                if len(resultados) >= 2:
                    centroides = np.array([r[2] for r in resultados])
                    D = distance.cdist(centroides,centroides, metric='euclidean')
                    for i in range(0, D.shape[0]-1):
                        for j in range(i + 1, D.shape[1]):
                            if D[i,j] < 270 :
                                infractores.add(i)
                                infractores.add(j)
                                dist_promedio += D[i][j]
                                contador = 0
                for (i, ( _, bbox, centroid)) in enumerate(resultados):
                    (x, y, x2, y2) = bbox
                    #(cX, cY) = centroid
                    if i in infractores:
                        color = (0,0,255)
                    else:
                        color = (0,255,0)
                    #fin bloque añadido

                    #if etiquetas[ids_clases[i]] == 'person':
                    # dibujar la caja que enmarca a cada persona con su respectivo nivel de confianza
                    #color = [int(c) for c in colors[classIDs[i]]]
                    cv2.rectangle(imagen, (x, y), (x2,y2), color, 2)
                    texto = "{}: {:.1f}%".format('Persona', lista_confianza[i]*100)
                    cv2.putText(imagen, texto, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            cv2.putText(imagen, "Personas: {0}".format(len(resultados)), (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)
            cv2.putText(imagen, "Incumplidas: {0}".format(len(infractores)), (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
            cv2.putText(imagen, "Cumplidas: {0}".format(len(resultados)-len(infractores)), (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)        
            if len(infractores) != 0:
                dist_promedio = dist_promedio / len(infractores)
        return imagen,len(resultados),len(infractores),dist_promedio, contador


    def prediccion(self,red, nombres_etiquetas, imagen, confianza, umbral):
        alto, ancho = imagen.shape[:2]
        
        # crear blob desde la imagen
        blob = cv2.dnn.blobFromImage(imagen, 1 / 255.0, (320, 320), swapRB=True, crop=False)
        red.setInput(blob)
        salidas = red.forward(nombres_etiquetas)

        # extraer elementos
        cajas, confianzas, idsclases = self.extraer_cajas_confianzas_idsclases(salidas, confianza, ancho, alto)

        # aplicar umbral
        idxs = cv2.dnn.NMSBoxes(cajas, confianzas, confianza, umbral)

        return cajas, confianzas, idsclases, idxs


    def run(self):

            
        #cargar etiquetas
        etiquetas = open('../model/coco.names').read().strip().split('\n')

        #color verde por defecto para las personas
        color = (0,255,0)

        #cargar pesos y configuración de YOLOv3
        red = cv2.dnn.readNetFromDarknet('../model/yolov3.cfg','../model/yolov3.weights')

        #comprobar GPU
        indice_gpu = cv2.cuda.getDevice()
        if indice_gpu >= 0:
            red.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
            red.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
            #imprimir información de GPU
            cv2.cuda.printCudaDeviceInfo(indice_gpu)
            
        # Obtener etiquetas de la red
        n_etiquetas = red.getLayerNames()
        nombres_etiquetas = [n_etiquetas[i[0] - 1] for i in red.getUnconnectedOutLayers()]

        #indicamos nivel de confianza
        confianza = 0.5

        #indicamos el nivel de umbral
        umbral = 0.2
        

        #inicializamos video
        video = cv2.VideoCapture(1)
        
        
        #redimiensionamos video
        video.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        video.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        #variables temporales
        temp_personas = 0
        temp_incumplidas = 0
        temp_dist_promedio = 0.0
        contador = 0
        guardar = False

        #iniciar renderizado de video
        while video.isOpened():
            _, imagen = video.read()

            cajas, confianzas, idclases, idxs = self.prediccion(red, nombres_etiquetas, imagen, confianza, umbral)

            imagen, _personas,_infractores,_dist_promedio,contador = self.dibujar_cajas(imagen, cajas, confianzas, idclases, idxs, color,contador)
            imagen = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
            imagen = cv2.flip(imagen,1)
            imagenaplanada= cv2.flip(imagen,1)
            qtImagen= QImage(imagenaplanada.data, imagenaplanada.shape[1], imagenaplanada.shape[0], QImage.Format_RGB888)
            img= qtImagen.scaled(1280,720,Qt.KeepAspectRatio)
            self.imagenfinal.emit(img)

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
                


            """cv2.imshow('Deteccion de personas con YOLOv3', imagen)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break"""
        


