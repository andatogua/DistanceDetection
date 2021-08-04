from PyQt5.QtSql import *
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QTableView,
)

def crearConexion():
    con = QSqlDatabase.addDatabase("QSQLITE")
    con.setDatabaseName("registro.sqlite")
    if not con.open():
        QMessageBox.critical(
            None,
            "Error!",
            "Database Error: %s" % con.lastError().databaseText(),
        )
        return False
    print("Conexión creada")
    if creartabla():
        print('Tabla creada')
    return True

def creartabla():
    q = QSqlQuery()
    if (q.prepare("create table if not exists registro(id integer primary key autoincrement not null, incumplidos integer, total integer, dist_promedio real, fecha text)")):
        if (q.exec()):
            return True

def guardar(incumplidos,personas,dist_promedio,fecha):
    q = QSqlQuery()
    if (q.prepare("insert into registro (incumplidos,total,dist_promedio,fecha) values (" + str(incumplidos) + "," + str(personas) +"," + str(dist_promedio) + ",datetime('" + fecha + "'))")):
        if (q.exec()):
            return True
    else:
        print(q.lastError().text())

def datosdia(dia):
    datos = []
    incum = 0
    total = 0 
    dist_prom = 0
    n = 0
    hora = ''
    q = QSqlQuery()
    if q.prepare("SELECT sum(incumplidos), sum(total), sum(dist_promedio), count(fecha),strftime('%H',fecha) FROM registro WHERE date(fecha)='" + dia + "' GROUP BY strftime('%H',fecha);"):
        if q.exec():
            while q.next():
                incum = q.value(0)
                total = q.value(1)
                dist_prom = q.value(2)
                n = q.value(3)
                hora = q.value(4)
                datos.append([incum,total,dist_prom,n,hora])
    return datos

def ultimadetdia(dia):
    fecha = ''
    q = QSqlQuery()
    if q.prepare("SELECT fecha FROM registro WHERE date(fecha)='" + dia + "' ORDER BY fecha DESC LIMIT 1;"):
        if q.exec():
            while q.next():
                fecha = q.value(0)
    return fecha

def totaldetinf():
    infractores, detecciones = 0, 0
    q = QSqlQuery()
    if q.prepare("SELECT sum(incumplidos), count(incumplidos) FROM registro;"):
        if q.exec():
            while q.next():
                infractores, detecciones = q.value(0),q.value(1)

    return infractores, detecciones