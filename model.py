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
from .models.converter import Converter
from qgis.PyQt.QtCore import QCoreApplication


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
            self.ifcAnalyzer = IfcAnalyzer(self, self.inputPath)
            self.ifcAnalyzer.run(self.dlg.getOptionVal())
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
        self.dlg.enableProgress(True)
        self.dlg.log(QCoreApplication.translate('IFC-to-CityGML', u'Conversion started'))

        self.converter = Converter(self, self.inputPath, self.outputPath)

        lod = self.dlg.getLod()
        eade = self.dlg.getOptionEade()
        integr = self.dlg.getOptionIntegr()
        self.dlg.log(QCoreApplication.translate('IFC-to-CityGML', u'Input') + ": " + self.inputPath[self.inputPath.rindex("\\")+1:] + ", " + QCoreApplication.translate('IFC-to-CityGML', u'Output') + ": " + self.outputPath[self.outputPath.rindex("\\")+1:] + ", LoD: " + str(lod) + ", EnergyADE: " + str(eade) + ", " + QCoreApplication.translate('IFC-to-CityGML', u'QGIS integration') + ": " + str(integr))
        self.converter.run(lod, eade, integr)


    def completed(self):
        self.dlg.log(QCoreApplication.translate('IFC-to-CityGML', u'Conversion completed'))

