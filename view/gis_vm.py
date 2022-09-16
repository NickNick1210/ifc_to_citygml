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
import os.path
import platform

# QGIS-Bibliotheken
from qgis.core import QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication

# XML-Bibliotheken
from lxml import etree


#####

class GisVM:
    """ ViewModel der GIS-View """

    def __init__(self, model):
        """ Konstruktor der ViewModel der GIS-View

        Args:
            model: Die zugrunde liegende zentrale Model-Klasse
        """
        # Initialisierung von Attributen
        self.model = model

    @staticmethod
    def tr(msg):
        """ Übersetzt den gegebenen Text

        Args:
            msg: zu übersetzender Text

        Returns:
            Übersetzter Text
        """
        return QCoreApplication.translate('GisVM', msg)

    def loadIntoGIS(self, path):
        """ Lädt den Datensatzes als Layer in QGIS

        Args:
            path: Pfad zum CityGML-Datensatz
        """

        # Erstellen des Vektorlayers
        slash = "/" if platform.system() == "Linux" else "\\"
        name = path[path.rindex(slash) + 1:-4]
        layer = QgsVectorLayer(path, name, "ogr")

        # Wenn Layer valide ist: Hinzufügen
        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            self.model.dlg.log(self.tr(u'CityGML building model added to QGIS'))
            self.set3dProperties(layer)

        # Wenn Layer invalide ist: Fehlermeldung
        else:
            self.model.dlg.log(self.tr(u'CityGML bulding model could not be added to QGIS'))

    def set3dProperties(self, layer):
        """ Setzt die 3D-Einstellungen, damit der Layer dreidimensional angezeigt werden kann

        Args:
            layer: Layer, dessen Einstellungen geändert werden sollen
        """

        # Stilvorlage einlesen
        filePath = os.path.dirname(__file__)
        stylePath = filePath[0:filePath.rfind('\\')] + '/resources/3D.qml'
        qml = etree.parse(stylePath)
        minV, maxV = qml.xpath("//Option[@name='minValue']")[0], qml.xpath("//Option[@name='maxValue']")[0]

        # Minimale und maximale Höhe berechnen und setzen
        minHeight, maxHeight = sys.maxsize, -sys.maxsize
        ix = layer.fields().indexFromName('measuredHeight')
        for feature in layer.getFeatures():
            height = feature.attributes()[ix]
            if height < minHeight:
                minHeight = height
            if height > maxHeight:
                maxHeight = height
        minV.set("value", str(minHeight))
        maxV.set("value", str(maxHeight))

        # Änderungen speichern
        qml.write(stylePath, xml_declaration=True, encoding="UTF-8", pretty_print=True)

        # Stil einlesen und Layer aktualisieren
        layer.loadNamedStyle(stylePath)
        layer.triggerRepaint()

        # Meldung
        self.model.dlg.log(self.tr(u'3D properties adjusted to display the building model'))
