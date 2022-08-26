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
import math
import sys
import uuid
from copy import deepcopy
from datetime import datetime
import numpy as np

# IFC-Bibliotheken
import ifcopenshell
import ifcopenshell.util.pset
from ifcopenshell.util import element

# XML-Bibliotheken
from lxml import etree
# noinspection PyUnresolvedReferences
from lxml.etree import QName

# QGIS-Bibliotheken
from qgis.core import QgsTask
from qgis.PyQt.QtCore import QCoreApplication

# Geo-Bibliotheken
from osgeo import ogr
import sympy
from sympy import Point3D, Plane, Line

# Plugin
from .xmlns import XmlNs
from .mapper import Mapper
from .transformer import Transformer
from .utilitiesGeom import UtilitiesGeom
from .utilitiesIfc import UtilitiesIfc


#####


class LoD4Converter(QgsTask):
    """ Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien """

    @staticmethod
    def tr(msg):
        """ Übersetzen

        Args:
            msg: zu übersetzender Text

        Returns:
            Übersetzter Text
        """
        return QCoreApplication.translate('LoD4Converter', msg)

    def convertLoD4(self, root, eade):
        """ Konvertieren von IFC zu CityGML im Level of Detail (LoD) 4

        Args:
            root: Das vorbereitete XML-Schema
            eade: Ob die EnergyADE gewählt wurde als Boolean
        """

        # IFC-Grundelemente
        ifcProject = self.ifc.by_type("IfcProject")[0]
        ifcSite = self.ifc.by_type("IfcSite")[0]
        ifcBuildings = self.ifc.by_type("IfcBuilding")

        # XML-Struktur
        chName = etree.SubElement(root, QName(XmlNs.gml, "name"))
        chName.text = self.outPath[self.outPath.rindex("\\") + 1:-4]
        chBound = etree.SubElement(root, QName(XmlNs.gml, "boundedBy"))

        # Über alle enthaltenen Gebäude iterieren
        for ifcBuilding in ifcBuildings:
            chCOM = etree.SubElement(root, QName(XmlNs.core, "cityObjectMember"))
            chBldg = etree.SubElement(chCOM, QName(XmlNs.bldg, "Building"))

            # Konvertierung
            self.parent.dlg.log(self.tr(u'Building attributes are extracted'))
            self.convertBldgAttr(ifcBuilding, chBldg)
            links, footPrint, surfaces = self.convertLoD4BldgBound(ifcBuilding, chBldg)
            self.convertLoDSolid(chBldg, links, 4)
            self.parent.dlg.log(self.tr(u'Rooms are calculated'))
            self.convertLoD4Interior(ifcBuilding, chBldg)
            self.parent.dlg.log(self.tr(u'Building address is extracted'))
            self.convertAddress(ifcBuilding, ifcSite, chBldg)
            self.parent.dlg.log(self.tr(u'Building bound is calculated'))
            bbox = self.convertBound(self.geom, chBound)

            # EnergyADE
            if eade:
                self.parent.dlg.log(self.tr(u'Energy ADE is calculated'))
                self.parent.dlg.log(self.tr(u'Energy ADE: weather data is extracted'))
                self.convertWeatherData(ifcProject, ifcSite, chBldg, bbox)
                self.parent.dlg.log(self.tr(u'Energy ADE: building attributes are extracted'))
                self.convertEadeBldgAttr(ifcBuilding, chBldg, bbox, footPrint)
                self.parent.dlg.log(self.tr(u'Energy ADE: thermal zone is calculated'))
                linkUZ, chBldgTZ, constructions = self.calcLoD3ThermalZone(ifcBuilding, chBldg, surfaces)
                self.parent.dlg.log(self.tr(u'Energy ADE: usage zone is calculated'))
                self.calcLoDUsageZone(ifcProject, ifcBuilding, chBldg, linkUZ, chBldgTZ)
                self.parent.dlg.log(self.tr(u'Energy ADE: construction is calculated'))
                materials = self.convertConstructions(root, constructions)
                self.parent.dlg.log(self.tr(u'Energy ADE: material is calculated'))
                self.convertMaterials(root, materials)

        return root

    def convertLoD4BldgBound(self, ifcBuilding, chBldg):
        """ Konvertieren des erweiterten Gebäudeumrisses von IFC zu CityGML in Level of Detail (LoD) 4

        Args:
            ifcBuilding: Das Gebäude, aus dem der Gebäudeumriss entnommen werden soll
            chBldg: XML-Element an dem der Gebäudeumriss angefügt werden soll

        Returns:
            GML-IDs der Bestandteile des erweiterten Gebäudeumrisses als Liste
            Die Grundflächengeometrie
            Die GML-IDs der Bestandteile mit zugehörigen IFC-Elementen als Liste
        """
        # Berechnung
        self.parent.dlg.log(self.tr(u'Building geometry: base surfaces are calculated'))
        bases, basesOrig, floors = self.calcLoD3Bases(ifcBuilding)
        self.parent.dlg.log(self.tr(u'Building geometry: roof surfaces are calculated'))
        roofs, roofsOrig = self.calcLoD3Roofs(ifcBuilding)
        self.parent.dlg.log(self.tr(u'Building geometry: wall surfaces are calculated'))
        walls = self.calcLoD3Walls(ifcBuilding)
        self.parent.dlg.log(self.tr(u'Building geometry: door surfaces are calculated'))
        openings = self.calcLoD3Openings(ifcBuilding, "ifcDoor")
        self.parent.dlg.log(self.tr(u'Building geometry: window surfaces are calculated'))
        openings += self.calcLoD3Openings(ifcBuilding, "ifcWindow")
        self.parent.dlg.log(self.tr(u'Building geometry: openings are assigned to walls'))
        walls = self.assignOpenings(openings, walls)
        self.parent.dlg.log(self.tr(u'Building geometry: wall and opening surfaces are adjusted to each other'))
        walls, wallMainCounts = self.adjustWallOpenings(walls)
        self.parent.dlg.log(self.tr(u'Building geometry: wall surfaces are adjusted in their height'))
        walls = self.adjustWallSize(walls, floors, roofs, basesOrig, roofsOrig, wallMainCounts)

        # Geometrie
        links, surfaces = [], []
        for base in bases:
            linksBase, gmlId, openSurf = self.setElementGroup(chBldg, base[0], "GroundSurface", 3, name=base[1],
                                                              openings=base[2])
            links += linksBase
            surfaces.append([gmlId, base[3]])
            surfaces += openSurf
        for roof in roofs:
            linksRoof, gmlId, openSurf = self.setElementGroup(chBldg, roof[0], "RoofSurface", 3, name=roof[1],
                                                              openings=roof[2])
            links += linksRoof
            surfaces.append([gmlId, roof[3]])
            surfaces += openSurf
        for wall in walls:
            linksWall, gmlId, openSurf = self.setElementGroup(chBldg, wall[0], "WallSurface", 3, name=wall[1],
                                                              openings=wall[2])
            links += linksWall
            surfaces.append([gmlId, wall[3]])
            surfaces += openSurf
        return links, bases[0][0][0], surfaces

    def convertLoD4Interior(self, ifcBuilding, chBldg):
        """ Konvertieren des Gebäudeinneren von IFC zu CityGML in Level of Detail (LoD) 4

        Args:
            ifcBuilding: Das Gebäude, aus dem der Gebäudeumriss entnommen werden soll
            chBldg: XML-Element an dem der Gebäudeumriss angefügt werden soll
        """
        # TODO: LoD4 - Interieur

        # IFC-Elemente der Grundfläche
        ifcSpaces = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSpace", result=[])
        if len(ifcSpaces) == 0:
            self.parent.dlg.log(self.tr(u"Due to the missing rooms, they will also be missing in CityGML"))
            return []

        for ifcSpace in ifcSpaces:
            chIntRoom = etree.SubElement(chBldg, QName(XmlNs.bldg, "interiorRoom"))
            chRoom = etree.SubElement(chIntRoom, QName(XmlNs.bldg, "Room"))

            # Eigenschaften
            if ifcSpace.Name is not None or ifcSpace.LongName is not None:
                chRoomName = etree.SubElement(chRoom, QName(XmlNs.gml, "name"))
                if ifcSpace.Name is not None:
                    chRoomName.text = ifcSpace.Name
                else:
                    chRoomName.text = ifcSpace.LongName
            if ifcSpace.Description is not None or (ifcSpace.Name is not None and ifcSpace.LongName is not None):
                chRoomDescr = etree.SubElement(chRoom, QName(XmlNs.gml, "description"))
                if ifcSpace.Description is not None:
                    chRoomDescr.text = ifcSpace.Description
                else:
                    chRoomDescr.text = ifcSpace.LongName

            links = self.convertLoD4RoomBound(ifcSpace, chRoom)
            self.convertLoDSolid(chRoom, links, 4)
            self.convertLoD4Furniture(ifcSpace, chRoom)
            self.convertLoD4Installation(ifcSpace, chRoom)

    # noinspection PyMethodMayBeStatic
    def convertLoD4RoomBound(self, ifcSpace, chRoom):
        """ Konvertieren des Raumes von IFC zu CityGML in Level of Detail (LoD) 4

        Args:
            ifcSpace: Der Raum, aus dem der Raumumriss entnommen werden soll
            chRoom: XML-Element an dem der Raumumriss angefügt werden soll
        """
        # Heraussuchen von Böden/Decken (IfcSlab), Wänden (IfcWall/IfcCurtainWall) und Öffnungen (IfcDoor/IfcWindow)
        #   aus dem IfcSpace (über IfcRelAggregates)
        # Setzen als bldg:FloorSurface/CeilingSurface/ClosureSurface und bldg:InteriorWallSurface (mit bdlg:Door/Window)
        #   in bldg:boundedBy
        # Entnehmen von grundlegenden Eigenschaften (Name)
        # Berechnung der Geometrie
        return []

    # noinspection PyMethodMayBeStatic
    def convertLoD4Furniture(self, ifcSpace, chRoom):
        """ Konvertieren der Möblierung eines Raumes von IFC zu CityGML in Level of Detail (LoD) 4

        Args:
            ifcSpace: Der Raum, aus dem die Möbel entnommen werden sollen
            chRoom: XML-Element an dem die Möbel angefügt werden sollen
        """
        # Heraussuchen von Möbeln (ifcFurniture/IfcSystemFurnitureElemen)
        #   aus dem IfcSpace (über IfcRelContainedInSpatialStructure)
        # Setzen als bldg:BuildingFurniture in bldg:interiorFurniture
        # Entnehmen von grundlegenden Eigenschaften (Name, Description, Function)
        # Berechnung der Geometrie
        return

    # noinspection PyMethodMayBeStatic
    def convertLoD4Installation(self, ifcSpace, chRoom):
        """ Konvertieren der Installationen eines Raumes von IFC zu CityGML in Level of Detail (LoD) 4

        Args:
            ifcSpace: Der Raum, aus dem die Installationen entnommen werden sollen
            chRoom: XML-Element an dem die Installationen angefügt werden sollen
        """
        # Heraussuchen von Installationen (IfcStair, IfcRamp, IfcRailing, IfcColumn, IfcBeam, IfcChimney, ...)
        #   aus dem IfcSpace (über IfcRelConrtainedInSpatialStructure)
        # Setzen als bldg:IntBuildingInstallation in bldg:roomInstallation
        # Entnehmen von grundlegenden Eigenschaften (Name, Description, Function)
        # Berechnung der Geometrie
        return

