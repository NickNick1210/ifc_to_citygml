# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (09.09.2022)
 ***************************************************************************/
"""

#####

# Standard-Bibliotheken
import sys
import platform

# QGIS-Bibliotheken
from qgis.PyQt.QtCore import QCoreApplication, QUrl
from qgis.core import QgsApplication, Qgis
from qgis.PyQt.QtWidgets import QLabel

# Plugin
import os
import sys

try:
    from ..algorithm.ifc_analyzer import IfcAnalyzer
    from ..algorithm.convert_starter import ConvertStarter
except ImportError:
    plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if plugin_root not in sys.path:
        sys.path.insert(0, plugin_root)
    from algorithm.ifc_analyzer import IfcAnalyzer
    from algorithm.convert_starter import ConvertStarter


#####


class Model:
    """ Zentrale Model-Klasse """

    def __init__(self, iface):
        """ Konstruktor der zentralen Model-Klasse

        Args:
            iface: Die QGIS-Interface-Instanz, an die sich das Plugin bindet
        """

        # Initialisierung von Attributen
        self.inPath, self.outPath = None, None
        self.valid = False
        self.dlg, self.gis = None, None
        self.task = None
        self.iface = iface

    def setVM(self, dlg, gis):
        """ Setzt die ViewModels

        Args:
            dlg: ViewModel zur GUI
            gis: ViewModel zu QGIS
        """
        self.dlg = dlg
        self.gis = gis

    @staticmethod
    def tr(msg):
        """ Übersetzt den gegebenen Text

        Args:
            msg: zu übersetzender Text

        Returns:
            Übersetzter Text
        """
        return QCoreApplication.translate('Model', msg)

    def ifcFileChanged(self):
        """ EventListener, wenn eine IFC-Datei als Eingabe angegeben wurde """
        # Abruf des Pfades
        self.inPath = self.dlg.getInputPath()

        # Analysieren der IFC-Datei
        self.valid = False
        self.checkEnable()
        if not self.inPath or not os.path.isfile(self.inPath):
            self.dlg.setIfcStatus(self.tr(u'not valid'), "red")
            self.dlg.setIfcMsg(self.tr(u'Input file not found!'))
            self.dlg.log(self.tr(u'Input file not found!'))
            return

        try:
            ifcAnalyzer = IfcAnalyzer(self, self.inPath)
        except OSError as exc:
            self.dlg.setIfcStatus(self.tr(u'not valid'), "red")
            self.dlg.setIfcMsg(self.tr(u'Unable to open IFC file!'))
            self.dlg.log(self.tr(u'Unable to open IFC file!') + f" ({exc})")
            return

        ifcAnalyzer.run(self.dlg.getOptionVal())

    def cgmlFileChanged(self):
        """ EventListener, wenn eine CityGML-Datei als Ausgabe angegeben wurde """
        # Abruf des Pfades
        self.outPath = self.dlg.getOutputPath()

        # Prüfen auf Konvertierungsfreigabe
        self.checkEnable()

    def checkEnable(self):
        """ Überprüft, ob beide Dateien angegeben und valide sind und gibt ggf. Konvertierung frei """
        self.dlg.enableRun(True)

    def run(self):
        """ Startet die Konvertierung """
        # Deaktivieren der GUI
        self.dlg.enableRun(False)
        self.dlg.enableDef(False)
        self.dlg.enableProgress(True)
        self.dlg.log(self.tr(u'Conversion started'))

        # Abruf der Einstellungen
        lod = self.dlg.getLod()
        eade = self.dlg.getOptionEade()
        integr = self.dlg.getOptionIntegr()
        slash = "/" if platform.system() == "Linux" else "\\"
        self.dlg.log(self.tr(u'Input') + ": " + self.inPath[self.inPath.rindex(slash) + 1:] + ", " + self.tr(
            u'Output') + ": " + self.outPath[self.outPath.rindex(slash) + 1:] + ", LoD: " + str(lod) +
                     ", EnergyADE: " + str(eade) + ", " + self.tr(u'QGIS integration') + ": " + str(integr))

        # Konvertieren starten
        target_crs = self.dlg.getTargetCrs()
        self.task = ConvertStarter(self.tr(u"IFC-to-CityGML Conversion"),self, self.inPath, self.outPath, lod, eade, integr, target_crs)
        QgsApplication.taskManager().addTask(self.task)
        self.task.progressChanged.connect(lambda t: self.dlg.setProgress(t))
        self.task.logging.connect(lambda t: self.dlg.log(t))

        # Falls die Konvertierung zu Testzwecken auf dem Mainthread ausgeführt werden soll
        # conv = ConvertStarter(self.tr(u"IFC-to-CityGML"), self, self.inPath, self.outPath, lod, eade, integr)
        # conv.run()

    def completed(self, result):
        """ Beendet die Konvertierung

            Args:
                result: Ob die Konvertierung erfolgreich war, als Boolean
        """
        output_dir = os.path.dirname(self.outPath) if self.outPath else None

        self.dlg.enableDef(True)
        self.dlg.enableProgress(False)
        self.dlg.setProgress(100)
        self.checkEnable()

        if result:
            self.dlg.log(self.tr(u'Conversion completed'))
            self._push_completion_message(
                self.tr("Success"),
                self.tr(u"IFC-to-CityGML conversion successfully completed"),
                Qgis.Success,
                output_dir,
            )
        else:
            self.dlg.log(self.tr(u'Conversion crashed'))
            self._push_completion_message(
                self.tr("Error"),
                self.tr(u"IFC-to-CityGML conversion failed"),
                Qgis.Critical,
                output_dir,
            )
        self.task = None

    def _push_completion_message(self, title, text, level, output_dir=None):
        bar = self.iface.messageBar()
        if output_dir:
            item = bar.createMessage(title, text)
            link = QLabel(
                f"<a href=\"{QUrl.fromLocalFile(output_dir).toString()}\">"
                f"{self.tr('Open output folder')}"
                f"</a>"
            )
            link.setOpenExternalLinks(True)
            item.layout().addWidget(link)
            bar.pushWidget(item, level, duration=0)
        else:
            bar.pushMessage(title, text, level=level, duration=0)

    def cancel(self):
        """ Bricht die Konvertierung ab """
        if self.task is not None:
            self.task.cancel()
