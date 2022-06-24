# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.1 (23.06.2022)
 ***************************************************************************/
"""

#####

# Standard-Bibliotheken
import os
from datetime import datetime

# QGIS-Bibliotheken
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

# Laden der GUI-Datei, sodass PyQt das Plugin mit den Elementen des Qt-Designer bestücken kann
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dialog.ui'))


class Dialog_VM(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent, model):
        """Constructor."""
        super(Dialog_VM, self).__init__(None)
        self.model = model

        # GUI aufbauen
        self.setupUi(self)

        # Datei-Format-Filter für die Dateiauswahlen setzen
        self.fileWidget_ifc.setFilter("Industry Foundation Classes (*.ifc)")
        self.fileWidget_cgml.setFilter("Geography Markup Language (*.gml)")

        # EventListener für den Startknopf
        self.button_run.clicked.connect(model.run)
        self.fileWidget_ifc.fileChanged.connect(model.ifcFileChanged)
        self.fileWidget_cgml.fileChanged.connect(model.cgmlFileChanged)

        self.log("Tool gestartet")


    def getInputPath(self):
        return self.fileWidget_ifc.filePath()

    def getOutputPath(self):
        return self.fileWidget_cgml.filePath()

    def getOptionEade(self):
        return self.checkBox_eade.isChecked()

    def getOptionIntegr(self):
        return self.checkBox_integr.isChecked()

    def getLod(self):
        if self.radioButton_lod0.isChecked():
            return 0
        elif self.radioButton_lod1.isChecked():
            return 1
        elif self.radioButton_lod1.isChecked():
            return 2
        elif self.radioButton_lod1.isChecked():
            return 3
        elif self.radioButton_lod1.isChecked():
            return 4
        else:
            return -1

    def log(self, msg):
        currTime = datetime.now().strftime("%H:%M:%S")
        self.textBrowser_log.append(currTime + "   " + msg)

    def enableProgress(self, enable):
        self.progressBar.setEnabled(enable)

    def setProgress(self, progr):
        self.progressBar.setValue(progr)

    def enableRun(self, enable):
        self.button_run.setEnabled(enable)

    def enableDef(self, enable):
        self.groupBox_ifc.setEnabled(enable)
        self.groupBox_cgml.setEnabled(enable)