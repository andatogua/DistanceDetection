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