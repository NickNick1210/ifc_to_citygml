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

# QGIS-Bibliotheken
from qgis.PyQt.QtCore import QCoreApplication

# Plugin
from .models.ifc_analyzer import IfcAnalyzer
from .models.converter import Converter


#####


class Model:
    """ Zentrale Model-Klasse """

    def __init__(self):
        """ Konstruktor der zentralen Model-Klasse """

        # Initialisierung von Attributen
        self.inputPath = None
        self.outputPath = None
        self.valid = False
        self.dlg = None
        self.gis = None

    def setVM(self, dlg, gis):
        """ Setzen der ViewModels

        Args:
            dlg: ViewModel zur GUI
            gis: ViewModel zu QGIS
        """
        self.dlg = dlg
        self.gis = gis

    @staticmethod
    def tr(msg):
        """ Übersetzen

        Args:
            msg: zu übersetzender Text

        Returns:
            Übersetzter Text
        """
        return QCoreApplication.translate('IFC-to-CityGML', msg)

    def ifcFileChanged(self):
        """ EventListener, wenn eine (andere) IFC-Datei als Eingabe angegeben wurde """
        # Abruf des Pfades
        self.inputPath = self.dlg.getInputPath()

        # Analysieren der IFC-Datei
        self.valid = False
        self.checkEnable()
        ifcAnalyzer = IfcAnalyzer(self, self.inputPath)
        ifcAnalyzer.run(self.dlg.getOptionVal())

    def cgmlFileChanged(self):
        """ EventListener, wenn eine (andere) CityGML-Datei als Ausgabe angegeben wurde """
        # Abruf des Pfades
        self.outputPath = self.dlg.getOutputPath()

        # Prüfen auf Konvertierungsfreigabe
        self.checkEnable()

    def checkEnable(self):
        """ Überprüfung, ob beide Dateien angegeben und valide, sowie ggf. Freigabe der Konvertierung """
        if self.valid and self.outputPath is not None:
            self.dlg.enableRun(True)
        else:
            self.dlg.enableRun(False)

    def run(self):
        """ Starten der Konvertierung """
        # Deaktivieren der GUI
        self.dlg.enableRun(False)
        self.dlg.enableDef(False)
        self.dlg.enableProgress(True)
        self.dlg.log(self.tr(u'Conversion started'))

        # Abruf der Einstellungen
        lod = self.dlg.getLod()
        eade = self.dlg.getOptionEade()
        integr = self.dlg.getOptionIntegr()
        self.dlg.log(self.tr(u'Input') + ": " + self.inputPath[self.inputPath.rindex("\\") + 1:] + ", " + self.tr(
            u'Output') + ": " + self.outputPath[self.outputPath.rindex("\\") + 1:] + ", LoD: " + str(
            lod) + ", EnergyADE: " + str(eade) + ", " + self.tr(u'QGIS integration') + ": " + str(integr))

        # Konvertieren starten
        converter = Converter(self, self.inputPath, self.outputPath)
        converter.run(lod, eade, integr)

    def completed(self):
        """ Beenden der Konvertierung """
        self.dlg.log(QCoreApplication.translate('IFC-to-CityGML', u'Conversion completed'))
