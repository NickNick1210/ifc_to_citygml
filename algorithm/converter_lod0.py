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

# XML-Bibliotheken
from lxml import etree
# noinspection PyUnresolvedReferences
from lxml.etree import QName

# QGIS-Bibliotheken
from qgis.PyQt.QtCore import QCoreApplication

# Plugin
from ..model.xmlns import XmlNs
from .utilitiesGeom import UtilitiesGeom
from .utilitiesIfc import UtilitiesIfc
from .converter import Converter
from .converter_eade import EADEConverter


#####


class LoD0Converter(Converter):
    """ Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien in LoD0 """

    def __init__(self, task, ifc, name, trans, eade):
        """ Konstruktor der Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien in LoD0

        Args:
            task: Die zugrunde liegende zentrale Converter-Klasse
            ifc: IFC-Datei
            name: Name des Modells
            trans: Transformer-Klasse
            eade: Ob die EnergyADE gewählt wurde, als Boolean
        """
        super().__init__(task, ifc, name, trans, eade)

        # Initialisierung von Attributen
        self.progress = 10

    @staticmethod
    def tr(msg):
        """ Übersetzt den gegebenen Text

        Args:
            msg: zu übersetzender Text

        Returns:
            Übersetzter Text
        """
        return QCoreApplication.translate('LoD0Converter', msg)

    def convert(self, root):
        """ Konvertiert von IFC zu CityGML im Level of Detail (LoD) 0

        Args:
            root: Das vorbereitete XML-Schema
        """
        # IFC-Grundelemente
        ifcProject = self.ifc.by_type("IfcProject")[0]
        ifcSite = self.ifc.by_type("IfcSite")[0]
        ifcBuildings = self.ifc.by_type("IfcBuilding")

        # XML-Struktur
        chName = etree.SubElement(root, QName(XmlNs.gml, "name"))
        chName.text = self.name
        chBound = etree.SubElement(root, QName(XmlNs.gml, "boundedBy"))

        if self.task.isCanceled():
            return False

        # Über alle enthaltenen Gebäude iterieren
        bldgCount = len(ifcBuildings)
        for ifcBuilding in ifcBuildings:
            chCOM = etree.SubElement(root, QName(XmlNs.core, "cityObjectMember"))
            chBldg = etree.SubElement(chCOM, QName(XmlNs.bldg, "Building"))

            # Gebäudeattribute
            self.task.logging.emit(self.tr(u'Building attributes are extracted'))
            self.convertBldgAttr(self.ifc, ifcBuilding, chBldg)
            if self.task.isCanceled():
                return False
            self.progress += (10 / bldgCount)
            self.task.setProgress(self.progress)

            # Grundfläche
            self.task.logging.emit(self.tr(u'Building footprint is calculated'))
            footPrint = self.convertFootPrint(ifcBuilding, chBldg)
            if self.task.isCanceled():
                return False
            self.progress += (25 / bldgCount) if not self.eade else (15 / bldgCount)
            self.task.setProgress(self.progress)

            # Dachkantenfläche
            self.task.logging.emit(self.tr(u'Building roofedge is calculated'))
            self.convertRoofEdge(ifcBuilding, chBldg)
            if self.task.isCanceled():
                return False
            self.progress += (25 / bldgCount) if not self.eade else (15 / bldgCount)
            self.task.setProgress(self.progress)

            # Adresse
            self.task.logging.emit(self.tr(u'Building address is extracted'))
            addressSuccess = self.convertAddress(ifcBuilding, ifcSite, chBldg)
            if not addressSuccess:
                self.task.logging.emit(self.tr(u'No address details existing'))
            if self.task.isCanceled():
                return False
            self.progress += (10 / bldgCount)
            self.task.setProgress(self.progress)

            # Bounding Box
            self.task.logging.emit(self.tr(u'Building bound is calculated'))
            bbox = self.convertBound(self.geom, chBound, self.trans)
            if self.task.isCanceled():
                return False
            self.progress += (10 / bldgCount)
            self.task.setProgress(self.progress)

            # EnergyADE
            if self.eade:
                # Wetterdaten
                self.task.logging.emit(self.tr(u'Energy ADE: weather data is extracted'))
                EADEConverter.convertWeatherData(ifcProject, ifcSite, chBldg, bbox)
                if self.task.isCanceled():
                    return False
                self.progress += (10 / bldgCount)
                self.task.setProgress(self.progress)

                # Gebäudeattribute
                self.task.logging.emit(self.tr(u'Energy ADE: building attributes are extracted'))
                EADEConverter.convertBldgAttr(self.ifc, ifcBuilding, chBldg, bbox, footPrint)
                if self.task.isCanceled():
                    return False
                self.progress += (10 / bldgCount)
                self.task.setProgress(self.progress)

        return root

    def convertFootPrint(self, ifcBuilding, chBldg):
        """ Konvertiert die Grundfläche von IFC zu CityGML

        Args:
            ifcBuilding: Das Gebäude, aus dem die Grundfläche entnommen werden soll
            chBldg: XML-Element, an dem die Grundfläche angefügt werden soll

        Returns:
            Geometrie der Grundfläche
        """
        # IFC-Elemente
        ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="BASESLAB")
        if len(ifcSlabs) == 0:
            ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="FLOOR")
            # Wenn keine Grundfläche vorhanden
            if len(ifcSlabs) == 0:
                self.task.logging.emit(self.tr(u"Due to the missing baseslab, no FootPrint geometry can be calculated"))
                return

        # Geometrie
        geometry = self.calcPlane(ifcSlabs, self.trans)[1]
        if geometry is not None:
            self.geom.AddGeometry(geometry)
            self.bldgGeom.AddGeometry(geometry)
            geomXML = UtilitiesGeom.geomToGml(geometry)
            if geomXML is not None:
                # XML-Struktur
                chBldgFootPrint = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod0FootPrint"))
                chBldgFootPrintMS = etree.SubElement(chBldgFootPrint, QName(XmlNs.gml, "MultiSurface"))
                chBldgFootPrintSM = etree.SubElement(chBldgFootPrintMS, QName(XmlNs.gml, "surfaceMember"))
                chBldgFootPrintSM.append(geomXML)
        return geometry

    def convertRoofEdge(self, ifcBuilding, chBldg):
        """ Konvertiert die Dachkantenfläche von IFC zu CityGML

        Args:
            ifcBuilding: Das Gebäude, aus dem die Dachkantenfläche entnommen werden soll
            chBldg: XML-Element, an dem die Dachkantenfläche angefügt werden soll
        """

        # IFC-Elemente
        ifcRoofs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="ROOF")
        if len(ifcRoofs) == 0:
            ifcRoofs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcRoof", result=[])
            # Wenn kein Dach vorhanden
            if len(ifcRoofs) == 0:
                self.task.logging.emit(self.tr(u"Due to the missing roof, no RoofEdge geometry can be calculated"))
                return

        # Geometrie
        geometry = self.calcPlane(ifcRoofs, self.trans)[1]
        self.geom.AddGeometry(geometry)
        self.bldgGeom.AddGeometry(geometry)
        geomXML = UtilitiesGeom.geomToGml(geometry)
        if geomXML is not None:
            # XML-Struktur
            chBldgRoofEdge = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod0RoofEdge"))
            chBldgRoofEdgeMS = etree.SubElement(chBldgRoofEdge, QName(XmlNs.gml, "MultiSurface"))
            chBldgRoofEdgeSM = etree.SubElement(chBldgRoofEdgeMS, QName(XmlNs.gml, "surfaceMember"))
            chBldgRoofEdgeSM.append(geomXML)
