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

# IFC-to-CityGML
from .dialog_vm import Dialog_VM
from .gis_vm import GIS_VM
from .models.ifc_analyzer import IfcAnalyzer

class Model():
    def __init__(self, parent=None):
        """Constructor."""
        self.inputPath = ""
        self.outputPath = ""
        self.valid = False


    def setVM(self, Dialog_VM, GIS_VM):
        self.dlg = Dialog_VM
        self.gis = GIS_VM


    def ifcFileChanged(self):
        self.inputPath = self.dlg.getInputPath()
        self.valid = False

        self.dlg.setIfcInfo("")
        self.dlg.setIfcMsg("")
        if(self.inputPath != ""):
            self.fileName = self.inputPath[self.inputPath.rindex("\\")+1:-4]
            self.ifcAnalyzer = IfcAnalyzer(self, self.inputPath)
            self.dlg.log("IFC-Datei '" + self.fileName + "' wird analysiert")
        else:
            self.checkEnable()


    def cgmlFileChanged(self):
        self.outputPath = self.dlg.getOutputPath()
        self.checkEnable()


    def checkEnable(self):
        if(self.inputPath != "" and self.outputPath != "" and self.valid == True):
            self.dlg.enableRun(True)
        else:
            self.dlg.enableRun(False)


    def run(self):
        self.dlg.enableRun(False)
        self.dlg.enableDef(False)
        self.dlg.log("Konvertierung gestartet")



