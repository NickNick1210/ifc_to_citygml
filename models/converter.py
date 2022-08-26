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

# IFC-Bibliotheken
import ifcopenshell
import ifcopenshell.util.pset

# XML-Bibliotheken
from lxml import etree
# noinspection PyUnresolvedReferences
from lxml.etree import QName

# QGIS-Bibliotheken
from qgis.core import QgsTask
from qgis.PyQt.QtCore import QCoreApplication

# Plugin
from .xmlns import XmlNs
from .transformer import Transformer
from .converter_lod0 import LoD0Converter
from .converter_lod1 import LoD1Converter
from .converter_lod2 import LoD2Converter
from .converter_lod3 import LoD3Converter
from .converter_lod4 import LoD4Converter


#####


class Converter(QgsTask):
    """ Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien """

    def __init__(self, description, parent, inPath, outPath, lod, eade, integr):
        """ Konstruktor der Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien

        Args:
            parent: Die zugrunde liegende zentrale Model-Klasse
            inPath: Pfad zur IFC-Datei
            outPath: Pfad zur CityGML-Datei
            lod: Gewähltes Level of Detail (LoD) als Integer
            eade: Ob die EnergyADE gewählt wurde als Boolean
            integr: Ob die QGIS-Integration gewählt wurde als Boolean
        """
        super().__init__(description, QgsTask.CanCancel)

        # Initialisierung von Attributen
        self.exception = None
        self.parent = parent
        self.inPath, self.outPath = inPath, outPath
        self.lod, self.eade, self.integr = lod, eade, integr
        self.dedConv = None

    @staticmethod
    def tr(msg):
        """ Übersetzen

        Args:
            msg: zu übersetzender Text

        Returns:
            Übersetzter Text
        """
        return QCoreApplication.translate('Converter', msg)

    def run(self):
        """ Ausführen der Konvertierung """
        # Initialisieren von IFC und CityGML
        ifc = self.readIfc(self.inPath)
        root = self.createSchema()

        # Initialisieren vom Transformer
        trans = Transformer(ifc)

        # Name des Modells
        name = self.outPath[self.outPath.rindex("\\") + 1:-4]

        # Eigentliche Konvertierung: Unterscheidung nach den LoD
        dedConv = None
        if self.lod == 0:
            dedConv = LoD0Converter(self.parent, ifc, name, trans, self.eade)
        elif self.lod == 1:
            dedConv = LoD1Converter(self.parent, ifc, name, trans, self.eade)
        elif self.lod == 2:
            dedConv = LoD2Converter(self.parent, ifc, name, trans, self.eade)
        elif self.lod == 3:
            dedConv = LoD3Converter(self.parent, ifc, name, trans, self.eade)
        elif self.lod == 4:
            dedConv = LoD4Converter(self.parent, ifc, name, trans, self.eade)
        root = dedConv.convert(root)

        # Schreiben der CityGML in eine Datei
        self.parent.dlg.log(self.tr(u'CityGML file is generated'))
        self.writeCGML(root)

        # Integration der CityGML in QGIS
        if self.integr:
            self.parent.dlg.log(self.tr(u'Model is integrated into QGIS'))
            self.parent.gis.loadIntoGIS(self.outPath)

        # Abschließen
        self.finished(True)
        return True

    @staticmethod
    def readIfc(path):
        """ Einlesen einer IFC-Datei

        Args:
            path: Pfad zur IFC-Datei

        Returns:
            Eingelesene IFC-Datei
        """
        return ifcopenshell.open(path)

    @staticmethod
    def createSchema():
        """ Vorbereiten der CityGML-Struktur

        Returns:
            XML-Element
        """
        return etree.Element(QName(XmlNs.core, "CityModel"),
                             nsmap={'core': XmlNs.core, None: XmlNs.xmlns, 'bldg': XmlNs.bldg, 'gen': XmlNs.gen,
                                    'grp': XmlNs.grp, 'app': XmlNs.app, 'gml': XmlNs.gml, 'xAL': XmlNs.xAL,
                                    'xlink': XmlNs.xlink, 'xsi': XmlNs.xsi, 'energy': XmlNs.energy})

    def writeCGML(self, root):
        """ Schreiben der XML-Struktur in eine GML-Datei

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
