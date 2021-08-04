from PyQt5.QtMultimedia import *
import cv2

def checkCam():
    index = 0
    available = False
    cams = QCameraInfo.availableCameras()
    print(len(cams))
    for i in range(len(cams)):
        c = cv2.VideoCapture(i)
        if c.isOpened():
            s,f = c.read()
            if s and len(f) != 0:
                print('Camera: {}  is available'.format(cams[i].description()))
            index = i
            available = s
            c.release()
            break
    print(index)
    return available,index

