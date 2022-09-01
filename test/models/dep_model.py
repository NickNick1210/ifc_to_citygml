# -*- coding: utf-8 -*-

# QGIS-Bibliotheken
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsApplication, Qgis

import sys

from dep_dialog_vm import DialogVM


class Model:

    def __init__(self):
        self.dlg = DialogVM()
        self.completedTest = False
        self.valid = None

    def completed(self, result):
        self.completedTest = True

    def checkEnable(self):
        pass
