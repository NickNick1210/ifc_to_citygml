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

# XML-Bibliotheken
from lxml import etree
# noinspection PyUnresolvedReferences
from lxml.etree import QName

# QGIS-Bibliotheken
from qgis.PyQt.QtCore import QCoreApplication

# Geo-Bibliotheken
from osgeo import ogr

# Plugin
from .xmlns import XmlNs
from .utilitiesGeom import UtilitiesGeom
from .utilitiesIfc import UtilitiesIfc
from .converter_gen import GenConverter
from .converter_eade import EADEConverter


#####


class LoD1Converter:
    """ Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien """

    def __init__(self, parent, ifc, name, trans, eade):
        """ Konstruktor der Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien

        Args:
            parent: Die zugrunde liegende zentrale Converter-Klasse
            ifc: IFC-Datei
            name: Name des Modells
            trans: Transformer-Objekt
            eade: Ob die EnergyADE gewählt wurde als Boolean
        """

        # Initialisierung von Attributen
        self.parent = parent
        self.eade = eade
        self.ifc = ifc
        self.trans = trans
        self.geom = ogr.Geometry(ogr.wkbGeometryCollection)
        self.bldgGeom = ogr.Geometry(ogr.wkbGeometryCollection)
        self.name = name

    @staticmethod
    def tr(msg):
        """ Übersetzen

        Args:
            msg: zu übersetzender Text

        Returns:
            Übersetzter Text
        """
        return QCoreApplication.translate('LoD1Converter', msg)

    def convert(self, root):
        """ Konvertieren von IFC zu CityGML im Level of Detail (LoD) 1

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

        # Über alle enthaltenen Gebäude iterieren
        for ifcBuilding in ifcBuildings:
            self.bldgGeom = ogr.Geometry(ogr.wkbGeometryCollection)
            chCOM = etree.SubElement(root, QName(XmlNs.core, "cityObjectMember"))
            chBldg = etree.SubElement(chCOM, QName(XmlNs.bldg, "Building"))

            # Konvertierung
            self.parent.dlg.log(self.tr(u'Building attributes are extracted'))
            height = GenConverter.convertBldgAttr(self.ifc, ifcBuilding, chBldg)
            footPrint = self.convertSolid(ifcBuilding, chBldg, height)
            self.parent.dlg.log(self.tr(u'Building address is extracted'))
            GenConverter.convertAddress(ifcBuilding, ifcSite, chBldg)
            self.parent.dlg.log(self.tr(u'Building bound is calculated'))
            bbox = GenConverter.convertBound(self.geom, chBound, self.trans)

            # EnergyADE
            if self.eade:
                self.parent.dlg.log(self.tr(u'Energy ADE: weather data is extracted'))
                EADEConverter.convertWeatherData(ifcProject, ifcSite, chBldg, bbox)
                self.parent.dlg.log(self.tr(u'Energy ADE: building attributes are extracted'))
                EADEConverter.convertEadeBldgAttr(self.ifc, ifcBuilding, chBldg, bbox, footPrint)
                self.parent.dlg.log(self.tr(u'Energy ADE: thermal zone is calculated'))
                linkUZ, chBldgTZ, constructions = EADEConverter.calcLoDThermalZone(self.ifc, ifcBuilding, chBldg, root,
                                                                                   [], 1)
                self.parent.dlg.log(self.tr(u'Energy ADE: usage zone is calculated'))
                EADEConverter.calcLoDUsageZone(self.ifc, ifcProject, ifcBuilding, chBldg, linkUZ, chBldgTZ)

        return root

    def convertSolid(self, ifcBuilding, chBldg, height):
        """ Konvertieren des Gebäudeumrisses von IFC zu CityGML

        Args:
            ifcBuilding: Das Gebäude, aus dem der Gebäudeumriss entnommen werden soll
            chBldg: XML-Element an dem der Gebäudeumriss angefügt werden soll
            height: Die Gebäudehöhe
        """
        # Prüfung, ob die Höhe unbekannt ist
        if height is None or height == 0:
            self.parent.dlg.log(self.tr(u'Due to the missing height and roof, no building geometry can be calculated'))

        # IFC-Elemente der Grundfläche
        ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="BASESLAB")
        if len(ifcSlabs) == 0:
            ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="FLOOR")
            # Wenn keine Grundfläche vorhanden
            if len(ifcSlabs) == 0:
                self.parent.dlg.log(self.tr(u"Due to the missing baseslab, no building geometry can be calculated"))
                return

        # Berechnung der Geometrien
        geometries = []
        self.parent.dlg.log(self.tr(u'Building geometry: base surface is calculated'))
        geometries.append(GenConverter.calcPlane(ifcSlabs, self.trans)[1])
        self.parent.dlg.log(self.tr(u'Building geometry: roof surface is calculated'))
        geometries.append(self.calcRoof(geometries[0], height))
        self.parent.dlg.log(self.tr(u'Building geometry: wall surfaces are calculated'))
        geometries += self.calcWalls(geometries[0], height)

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
        """ Berechnung des Daches als Anhebung der Grundfläche

        Args:
            geomBase: Grundfläche des Gebäudes als Polygon-Geometrie
            height: Höhe der Anhebung als float

        Returns:
            Das erzeugte Dach als Geometrie
        """
        # Grundfläche
        ringBase = geomBase.GetGeometryRef(0)

        # Dachfläche
        geomRoof = ogr.Geometry(ogr.wkbPolygon)
        ringRoof = ogr.Geometry(ogr.wkbLinearRing)
        for i in range(ringBase.GetPointCount() - 1, -1, -1):
            pt = ringBase.GetPoint(i)
            ringRoof.AddPoint(pt[0], pt[1], pt[2] + height)
        geomRoof.AddGeometry(ringRoof)

        return geomRoof

    @staticmethod
    def calcWalls(geomBase, height):
        """ Berechnung der Wände als Extrusion der Grundfläche

        Args:
            geomBase: Grundfläche des Körpers als Polygon
            height: Höhe der Extrusion als float

        Returns:
            Liste der erzeugten Wand-Geometrien
        """
        # Grundfläche
        ringBase = geomBase.GetGeometryRef(0)

        # Wandflächen
        geomWalls = []
        for i in range(0, ringBase.GetPointCount() - 1):
            geomWall = ogr.Geometry(ogr.wkbPolygon)
            ringWall = ogr.Geometry(ogr.wkbLinearRing)
            pt1 = ringBase.GetPoint(i)
            pt2 = ringBase.GetPoint(i + 1)
            ringWall.AddPoint(pt1[0], pt1[1], pt1[2])
            ringWall.AddPoint(pt1[0], pt1[1], pt1[2] + height)
            ringWall.AddPoint(pt2[0], pt2[1], pt2[2] + height)
            ringWall.AddPoint(pt2[0], pt2[1], pt2[2])
            ringWall.CloseRings()
            geomWall.AddGeometry(ringWall)
            geomWalls.append(geomWall)

        return geomWalls
