import numpy as np
import cv2
import os

from scipy.spatial import distance

def extraer_cajas_confianzas_idsclases(salidas, confianza, ancho, alto):
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


def dibujar_cajas(imagen, cajas, lista_confianza, ids_clases, idxs, color):
    resultados = []
    infractores = set()
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
                        if D[i,j] < 100 :
                            infractores.add(i)
                            infractores.add(j)
                            print(i,j,D[i][j])
            for (i, _) in enumerate(resultados):
                #(x, y, ancho, alto) = bbox
                #(cX, cY) = centroid
                if i in infractores:
                    print(i)
                    color = (0,0,255)

                #fin bloque añadido

                #if etiquetas[ids_clases[i]] == 'person':
                # dibujar la caja que enmarca a cada persona con su respectivo nivel de confianza
                #color = [int(c) for c in colors[classIDs[i]]]
                cv2.rectangle(imagen, (x, y), (ancho,alto), color, 2)
                texto = "{}: {:.1f}%".format('Persona', lista_confianza[i]*100)
                cv2.putText(imagen, texto, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                cv2.putText(imagen, "Personas: {0}".format(len(resultados)), (150, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    return imagen


def prediccion(red, nombres_etiquetas, imagen, confianza, umbral):
    alto, ancho = imagen.shape[:2]
    
    # crear blob desde la imagen
    blob = cv2.dnn.blobFromImage(imagen, 1 / 255.0, (128, 128), swapRB=True, crop=False)
    red.setInput(blob)
    salidas = red.forward(nombres_etiquetas)

    # extraer elementos
    cajas, confianzas, idsclases = extraer_cajas_confianzas_idsclases(salidas, confianza, ancho, alto)

    # aplicar umbral
    idxs = cv2.dnn.NMSBoxes(cajas, confianzas, confianza, umbral)

    return cajas, confianzas, idsclases, idxs



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
nombres_etiquetas = red.getLayerNames()
nombres_etiquetas = [nombres_etiquetas[i[0] - 1] for i in red.getUnconnectedOutLayers()]

#indicamos nivel de confianza
confianza = 0.5

#indicamos el nivel de umbral
umbral = 0.3

#inicializamos video
video = cv2.VideoCapture(0)
#redimiensionamos video
video.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
video.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

#iniciar renderizado de video
while video.isOpened():
    _, imagen = video.read()

    cajas, confianzas, idclases, idxs = prediccion(red, nombres_etiquetas, imagen, confianza, umbral)

    imagen = dibujar_cajas(imagen, cajas, confianzas, idclases, idxs, color)

    cv2.imshow('Deteccion de personas con YOLOv3', imagen)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

