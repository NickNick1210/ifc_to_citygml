# Standard-Bibliotheken
import os
from datetime import datetime

# QGIS-Bibliotheken
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import QCoreApplication


class DialogVM:

    def __init__(self):
        self.logText = ""
        self.ifcInfo = ""
        self.ifcMsg = ""

    def log(self, msg):
        self.logText = msg

    def setIfcInfo(self, msg):
        self.ifcInfo = msg

    def setIfcMsg(self, msg):
        self.ifcMsg = msg
