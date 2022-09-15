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

# XML-Bibliotheken
from lxml import etree
# noinspection PyUnresolvedReferences
from lxml.etree import QName

# QGIS-Bibliotheken
from qgis.PyQt.QtCore import QCoreApplication

# Geo-Bibliotheken
from osgeo import ogr

# Plugin
from .utilitiesGeom import UtilitiesGeom
from .utilitiesIfc import UtilitiesIfc
from .converter import Converter
from .converter_eade import EADEConverter
try:
    from ..model.xmlns import XmlNs
except ImportError:
    sys.path.insert(0, '..')
    from model.xmlns import XmlNs


#####


class LoD1Converter(Converter):
    """ Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien in LoD1 """

    def __init__(self, task, ifc, name, trans, eade):
        """ Konstruktor der Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien in LoD1

        Args:
            task: Die zugrunde liegende zentrale Converter-Klasse
            ifc: IFC-Datei
            name: Name des Modells
            trans: Transformer-Objekt
            eade: Ob die EnergyADE gewählt wurde als Boolean
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
        return QCoreApplication.translate('LoD1Converter', msg)

    def convert(self, root):
        """ Konvertiert von IFC zu CityGML im Level of Detail (LoD) 1

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
        self.bldgCount = len(ifcBuildings)
        for ifcBuilding in ifcBuildings:
            self.bldgGeom = ogr.Geometry(ogr.wkbGeometryCollection)
            chCOM = etree.SubElement(root, QName(XmlNs.core, "cityObjectMember"))
            chBldg = etree.SubElement(chCOM, QName(XmlNs.bldg, "Building"))

            # Gebäudeattribute
            self.task.logging.emit(self.tr(u'Building attributes are extracted'))
            height = self.convertBldgAttr(self.ifc, ifcBuilding, chBldg)
            if self.task.isCanceled():
                return False
            self.progress += (10 / self.bldgCount) if not self.eade else (5 / self.bldgCount)
            self.task.setProgress(self.progress)

            # Gebäudekörper
            self.task.logging.emit(self.tr(u'Building solid is calculated'))
            footPrint = self.convertSolid(ifcBuilding, chBldg, height)
            if self.task.isCanceled():
                return False

            # Adresse
            self.task.logging.emit(self.tr(u'Building address is extracted'))
            self.convertAddress(ifcBuilding, ifcSite, chBldg)
            if self.task.isCanceled():
                return False
            self.progress += (10 / self.bldgCount)
            self.task.setProgress(self.progress)

            # Bounding Box
            self.task.logging.emit(self.tr(u'Building bound is calculated'))
            bbox = self.convertBound(self.geom, chBound, self.trans)
            if self.task.isCanceled():
                return False
            self.progress += (10 / self.bldgCount)
            self.task.setProgress(self.progress)

            # EnergyADE
            if self.eade:
                # Wetterdaten
                self.task.logging.emit(self.tr(u'Energy ADE: weather data is extracted'))
                EADEConverter.convertWeatherData(ifcProject, ifcSite, chBldg, bbox)
                if self.task.isCanceled():
                    return False
                self.progress += (5 / self.bldgCount)
                self.task.setProgress(self.progress)

                # Gebäudeattribute
                self.task.logging.emit(self.tr(u'Energy ADE: building attributes are extracted'))
                EADEConverter.convertBldgAttr(self.ifc, ifcBuilding, chBldg, bbox, footPrint)
                if self.task.isCanceled():
                    return False
                self.progress += (5 / self.bldgCount)
                self.task.setProgress(self.progress)

                # Thermale Zone
                self.task.logging.emit(self.tr(u'Energy ADE: thermal zone is calculated'))
                linkUZ, chBldgTZ, constructions = EADEConverter.calcThermalZone(self.ifc, ifcBuilding, chBldg, root, [],
                                                                                1)
                if self.task.isCanceled():
                    return False
                self.progress += (10 / self.bldgCount)
                self.task.setProgress(self.progress)

                # Nutzungszone
                self.task.logging.emit(self.tr(u'Energy ADE: usage zone is calculated'))
                EADEConverter.calcUsageZone(self.ifc, ifcProject, ifcBuilding, chBldg, linkUZ, chBldgTZ)
                if self.task.isCanceled():
                    return False
                self.progress += (5 / self.bldgCount)
                self.task.setProgress(self.progress)

        return root

    def convertSolid(self, ifcBuilding, chBldg, height):
        """ Konvertiert den Gebäudeumriss von IFC zu CityGML

        Args:
            ifcBuilding: Das IFC-Gebäude, aus dem der Gebäudeumriss entnommen werden soll
            chBldg: XML-Element, an dem der Gebäudeumriss angefügt werden soll
            height: Die Gebäudehöhe, als float

        Returns:
            Die Grundflächengeometrie
        """
        # Prüfung, ob die Höhe unbekannt ist
        if height is None or height == 0:
            self.task.logging.emit(self.tr(
                u'Due to the missing height and roof, no building geometry can be calculated'))

        # IFC-Elemente der Grundfläche
        ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="BASESLAB")
        if len(ifcSlabs) == 0:
            ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="FLOOR")
            # Wenn keine Grundfläche vorhanden
            if len(ifcSlabs) == 0:
                self.task.logging.emit(self.tr(u"Due to the missing baseslab, no building geometry can be calculated"))
                return

        geometries = []
        # Berechnung der Grundfläche
        self.task.logging.emit(self.tr(u'Building geometry: base surface is calculated'))
        geometries.append(self.calcPlane(ifcSlabs, self.trans)[1])
        if self.task.isCanceled():
            return False
        self.progress += (15 / self.bldgCount) if not self.eade else (10 / self.bldgCount)
        self.task.setProgress(self.progress)

        # Berechnung des Daches
        self.task.logging.emit(self.tr(u'Building geometry: roof surface is calculated'))
        geometries.append(self.calcRoof(geometries[0], height))
        if self.task.isCanceled():
            return False
        self.progress += (15 / self.bldgCount) if not self.eade else (10 / self.bldgCount)
        self.task.setProgress(self.progress)

        # Berechnung der Wände
        self.task.logging.emit(self.tr(u'Building geometry: wall surfaces are calculated'))
        geometries += self.calcWalls(geometries[0], height)
        if self.task.isCanceled():
            return False
        self.progress += (20 / self.bldgCount) if not self.eade else (10 / self.bldgCount)
        self.task.setProgress(self.progress)

        # Geometrie
        if geometries is not None and len(geometries) > 0:
            # XML-Struktur
            chBldgSolid = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod1Solid"))
            chBldgSolidSol = etree.SubElement(chBldgSolid, QName(XmlNs.gml, "Solid"))
            chBldgSolidExt = etree.SubElement(chBldgSolidSol, QName(XmlNs.gml, "exterior"))
            chBldgSolidCS = etree.SubElement(chBldgSolidExt, QName(XmlNs.gml, "CompositeSurface"))
            for geometry in geometries:
                self.geom.AddGeometry(geometry)
                self.bldgGeom.AddGeometry(geometry)
                chBldgSolidSM = etree.SubElement(chBldgSolidCS, QName(XmlNs.gml, "surfaceMember"))
                geomXML = UtilitiesGeom.geomToGml(geometry)
                chBldgSolidSM.append(geomXML)
        return geometries[0]

    @staticmethod
    def calcRoof(geomBase, height):
        """ Berechnet das Dach als Anhebung der Grundfläche

        Args:
            geomBase: Grundfläche des Gebäudes, als Polygon-Geometrie
            height: Höhe der Anhebung, als float

        Returns:
            Das erzeugte Dach, als Geometrie
        """
        # Grundfläche
        ringBase = geomBase.GetGeometryRef(0)

        # Dachfläche
        geomRoof, ringRoof = ogr.Geometry(ogr.wkbPolygon), ogr.Geometry(ogr.wkbLinearRing)
        for i in range(ringBase.GetPointCount() - 1, -1, -1):
            pt = ringBase.GetPoint(i)
            ringRoof.AddPoint(pt[0], pt[1], pt[2] + height)
        geomRoof.AddGeometry(ringRoof)

        return geomRoof

    @staticmethod
    def calcWalls(geomBase, height):
        """ Berechnet die Wände als Extrusion der Grundfläche

        Args:
            geomBase: Grundfläche des Körpers, als Polygon
            height: Höhe der Extrusion, als float

        Returns:
            Die erzeugten Wand-Geometrien, als Liste
        """
        # Grundfläche
        ringBase = geomBase.GetGeometryRef(0)

        # Wandflächen
        geomWalls = []
        for i in range(0, ringBase.GetPointCount() - 1):
            geomWall, ringWall = ogr.Geometry(ogr.wkbPolygon), ogr.Geometry(ogr.wkbLinearRing)
            pt1, pt2 = ringBase.GetPoint(i), ringBase.GetPoint(i + 1)
            ringWall.AddPoint(pt1[0], pt1[1], pt1[2])
            ringWall.AddPoint(pt1[0], pt1[1], pt1[2] + height)
            ringWall.AddPoint(pt2[0], pt2[1], pt2[2] + height)
            ringWall.AddPoint(pt2[0], pt2[1], pt2[2])
            ringWall.CloseRings()
            geomWall.AddGeometry(ringWall)
            geomWalls.append(geomWall)

        return geomWalls
