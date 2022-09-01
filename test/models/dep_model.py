# -*- coding: utf-8 -*-

# QGIS-Bibliotheken
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsApplication, Qgis


class Model:

    def __init__(self):
        self.completedTest = False

    def completed(self, result):
        self.completedTest = True
