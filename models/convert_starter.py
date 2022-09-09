# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (02.09.2022)
 ***************************************************************************/
"""

#####

# IFC-Bibliotheken
import ifcopenshell
import ifcopenshell.util.pset

# XML-Bibliotheken
from lxml import etree
# noinspection PyUnresolvedReferences
from lxml.etree import QName

# QGIS-Bibliotheken
from qgis.core import QgsTask
from qgis.PyQt.QtCore import QCoreApplication, pyqtSignal

# Plugin
from .xmlns import XmlNs
from .transformer import Transformer
from .converter_lod0 import LoD0Converter
from .converter_lod1 import LoD1Converter
from .converter_lod2 import LoD2Converter
from .converter_lod3 import LoD3Converter
from .converter_lod4 import LoD4Converter


#####


class ConvertStarter(QgsTask):
    """ Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien """

    logging = pyqtSignal(str)

    def __init__(self, description, parent, inPath, outPath, lod, eade, integr):
        """ Konstruktor der Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien

        Args:
            description: Beschreibung des QgsTasks
            parent: Die zugrunde liegende zentrale Model-Klasse
            inPath: Pfad zur IFC-Datei
            outPath: Pfad zur CityGML-Datei
            lod: Gewähltes Level of Detail (LoD), als Integer
            eade: Ob die EnergyADE gewählt wurde, als Boolean
            integr: Ob die QGIS-Integration gewählt wurde, als Boolean
        """
        super().__init__(description, QgsTask.CanCancel)

        # Initialisierung von Attributen
        self.parent = parent
        self.inPath, self.outPath = inPath, outPath
        self.lod, self.eade, self.integr = lod, eade, integr

    @staticmethod
    def tr(msg):
        """ Übersetzt den gegebenen Text

        Args:
            msg: zu übersetzender Text

        Returns:
            Übersetzter Text
        """
        return QCoreApplication.translate('Converter', msg)

    def run(self):
        """ Führt die Konvertierung aus """
        # Initialisieren
        ifc = self.readIfc(self.inPath)
        if self.lod >= 3 or (self.lod == 2 and self.eade):
            self.setProgress(2.5)
        else:
            self.setProgress(5)

        root = self.createSchema()
        trans = Transformer(ifc)
        name = self.outPath[self.outPath.rindex("\\") + 1:-4]
        if self.lod >= 3 or (self.lod == 2 and self.eade):
            self.setProgress(5)
        else:
            self.setProgress(10)

        if self.isCanceled():
            return False

        # Eigentliche Konvertierung: Unterscheidung nach den LoD
        dedConv = None
        if self.lod == 0:
            dedConv = LoD0Converter(self, ifc, name, trans, self.eade)
        elif self.lod == 1:
            dedConv = LoD1Converter(self, ifc, name, trans, self.eade)
        elif self.lod == 2:
            dedConv = LoD2Converter(self, ifc, name, trans, self.eade)
        elif self.lod == 3:
            dedConv = LoD3Converter(self, ifc, name, trans, self.eade)
        elif self.lod == 4:
            dedConv = LoD4Converter(self, ifc, name, trans, self.eade)
        root = dedConv.convert(root)

        if self.isCanceled():
            return False

        # Schreiben der CityGML in eine Datei
        self.logging.emit(self.tr(u'CityGML file is generated'))
        self.writeCGML(root)
        if self.isCanceled():
            return False
        if self.lod >= 3 or (self.lod == 2 and self.eade):
            self.setProgress(97.5)
        else:
            self.setProgress(95)

        # Integration der CityGML in QGIS
        if self.integr:
            self.logging.emit(self.tr(u'Model is integrated into QGIS'))
            self.parent.gis.loadIntoGIS(self.outPath)

        # Abschließen
        self.finished(True)
        return True

    @staticmethod
    def readIfc(path):
        """ Liest eine IFC-Datei ein

        Args:
            path: Pfad zur IFC-Datei

        Returns:
            Eingelesene IFC-Datei
        """
        return ifcopenshell.open(path)

    @staticmethod
    def createSchema():
        """ Bereitet die CityGML-Struktur vor

        Returns:
            XML-Element der CityGML-Struktur
        """
        return etree.Element(QName(XmlNs.core, "CityModel"),
                             nsmap={'core': XmlNs.core, None: XmlNs.xmlns, 'bldg': XmlNs.bldg, 'gen': XmlNs.gen,
                                    'grp': XmlNs.grp, 'app': XmlNs.app, 'gml': XmlNs.gml, 'xAL': XmlNs.xAL,
                                    'xlink': XmlNs.xlink, 'xsi': XmlNs.xsi, 'energy': XmlNs.energy})

    def writeCGML(self, root):
        """ Schreibt die XML-Struktur in eine GML-Datei

        Args:
            root: XML-Element
        """
        etree.ElementTree(root).write(self.outPath, xml_declaration=True, encoding="UTF-8", pretty_print=True)

    def finished(self, result):
        """ EventListener, wenn die Konvertierung abgeschlossen wurde

        Args:
            result: Ob die Konvertierung erfolgreich war als Boolean
        """
        self.parent.completed(result)
