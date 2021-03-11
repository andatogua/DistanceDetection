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
    return True