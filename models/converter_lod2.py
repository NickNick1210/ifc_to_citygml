# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)
 ***************************************************************************/
"""

#####

# Standard-Bibliotheken
import math
import sys
import uuid
import numpy as np

# IFC-Bibliotheken
import ifcopenshell
import ifcopenshell.util.pset

# XML-Bibliotheken
from lxml import etree
# noinspection PyUnresolvedReferences
from lxml.etree import QName

# QGIS-Bibliotheken
from qgis.PyQt.QtCore import QCoreApplication

# Geo-Bibliotheken
from osgeo import ogr
import sympy
from sympy import Point3D, Plane, Line

# Plugin
from .xmlns import XmlNs
from .utilitiesGeom import UtilitiesGeom
from .utilitiesIfc import UtilitiesIfc
from .converter_gen import GenConverter
from .converter_eade import EADEConverter


#####


class LoD2Converter:
    """ Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien in LoD2 """

    def __init__(self, parent, task, ifc, name, trans, eade):
        """ Konstruktor der Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien in LoD2

        Args:
            parent: Die zugrunde liegende zentrale Model-Klasse
            parent: Die zugrunde liegende zentrale Converter-Klasse
            ifc: IFC-Datei
            name: Name des Modells
            trans: Transformer-Objekt
            eade: Ob die EnergyADE gewählt wurde als Boolean
        """

        # Initialisierung von Attributen
        self.parent, self.task = parent, task
        self.ifc = ifc
        self.name = name
        self.trans = trans
        self.eade = eade
        self.geom, self.bldgGeom = ogr.Geometry(ogr.wkbGeometryCollection), ogr.Geometry(ogr.wkbGeometryCollection)
        self.progress, self.bldgCount = 10 if not eade else 5, None

    @staticmethod
    def tr(msg):
        """ Übersetzt den gegebenen Text

        Args:
            msg: zu übersetzender Text

        Returns:
            Übersetzter Text
        """
        return QCoreApplication.translate('LoD2Converter', msg)

    def convert(self, root):
        """ Konvertiert von IFC zu CityGML im Level of Detail (LoD) 2

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
            chCOM = etree.SubElement(root, QName(XmlNs.core, "cityObjectMember"))
            chBldg = etree.SubElement(chCOM, QName(XmlNs.bldg, "Building"))

            # Gebäudeattribute
            self.task.logging.emit(self.tr(u'Building attributes are extracted'))
            height = GenConverter.convertBldgAttr(self.ifc, ifcBuilding, chBldg)
            if self.task.isCanceled():
                return False
            self.progress += (5 / self.bldgCount) if not self.eade else (2.5 / self.bldgCount)
            self.task.setProgress(self.progress)

            # Gebäudebestandteile
            self.task.logging.emit(self.tr(u'Building bounds are calculated'))
            links, footPrint, surfaces = self.convertBldgBound(ifcBuilding, chBldg, height)
            if self.task.isCanceled():
                return False

            # Gebäudekörper
            self.task.logging.emit(self.tr(u'Building solid is calculated'))
            GenConverter.convertSolid(chBldg, links, 2)
            if self.task.isCanceled():
                return False
            self.progress += (5 / self.bldgCount) if not self.eade else (2.5 / self.bldgCount)
            self.task.setProgress(self.progress)

            # Adresse
            self.task.logging.emit(self.tr(u'Building address is extracted'))
            GenConverter.convertAddress(ifcBuilding, ifcSite, chBldg)
            if self.task.isCanceled():
                return False
            self.progress += (5 / self.bldgCount) if not self.eade else (2.5 / self.bldgCount)
            self.task.setProgress(self.progress)

            # Bounding Box
            self.task.logging.emit(self.tr(u'Building bound is calculated'))
            bbox = GenConverter.convertBound(self.geom, chBound, self.trans)
            if self.task.isCanceled():
                return False
            self.progress += (5 / self.bldgCount) if not self.eade else (2.5 / self.bldgCount)
            self.task.setProgress(self.progress)

            # EnergyADE
            if self.eade:
                # Wetterdaten
                self.task.logging.emit(self.tr(u'Energy ADE: weather data is extracted'))
                EADEConverter.convertWeatherData(ifcProject, ifcSite, chBldg, bbox)
                if self.task.isCanceled():
                    return False
                self.progress += (2.5 / self.bldgCount)
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
                linkUZ, chBldgTZ, constructions = EADEConverter.calcThermalZone(self.ifc, ifcBuilding, chBldg, root,
                                                                                surfaces, 2)
                if self.task.isCanceled():
                    return False
                self.progress += (5 / self.bldgCount)
                self.task.setProgress(self.progress)

                # Nutzungszone
                self.task.logging.emit(self.tr(u'Energy ADE: usage zone is calculated'))
                EADEConverter.calcUsageZone(self.ifc, ifcProject, ifcBuilding, chBldg, linkUZ, chBldgTZ)
                if self.task.isCanceled():
                    return False
                self.progress += (2.5 / self.bldgCount)
                self.task.setProgress(self.progress)

                # Konstruktionen
                self.task.logging.emit(self.tr(u'Energy ADE: construction is calculated'))
                materials = EADEConverter.convertConstructions(root, constructions)
                if self.task.isCanceled():
                    return False
                self.progress += (2.5 / self.bldgCount)
                self.task.setProgress(self.progress)

                # Materialien
                self.task.logging.emit(self.tr(u'Energy ADE: material is calculated'))
                EADEConverter.convertMaterials(root, materials)
                if self.task.isCanceled():
                    return False
                self.progress += (2.5 / self.bldgCount)
                self.task.setProgress(self.progress)

        return root

    def convertBldgBound(self, ifcBuilding, chBldg, height):
        """ Konvertiert den erweiterten Gebäudeumriss von IFC zu CityGML in Level of Detail (LoD) 2

        Args:
            ifcBuilding: Das IFC-Gebäude, aus dem der Gebäudeumriss entnommen werden soll
            chBldg: XML-Element, an dem der Gebäudeumriss angefügt werden soll
            height: Die Gebäudehöhe, als float

        Returns:
            GML-IDs der Bestandteile des erweiterten Gebäudeumrisses, als Liste
            Die Grundflächengeometrie
            Die GML-IDs der Bestandteile mit zugehörigen IFC-Elementen, als Liste
        """
        # Prüfung, ob die Höhe unbekannt ist
        if height is None or height == 0:
            self.task.logging.emit(self.tr(u'Due to the missing height and roof, no building geometry can be calculated'))

        # IFC-Elemente der Grundfläche
        ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="BASESLAB")
        if len(ifcSlabs) == 0:
            ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="FLOOR")
            # Wenn keine Grundfläche vorhanden
            if len(ifcSlabs) == 0:
                self.task.logging.emit(self.tr(u"Due to the missing baseslab, no building geometry can be calculated"))
                return

        # Berechnung Grundfläche
        self.task.logging.emit(self.tr(u'Building geometry: base surface is calculated'))
        base = GenConverter.calcPlane(ifcSlabs, self.trans)
        if base is None:
            return []
        self.progress += (10 / self.bldgCount)
        self.task.setProgress(self.progress)

        # IFC-Elemente des Daches
        ifcRoofs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="ROOF")
        ifcRoofs += UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcRoof", result=[])
        if len(ifcRoofs) == 0:
            self.task.logging.emit(self.tr(
                u"Due to the missing roof, no building geometry can be calculated"))
            return None

        if self.task.isCanceled():
            return False

        # Berechnungen
        self.task.logging.emit(self.tr(u'Building geometry: roof surfaces are extracted'))
        roofs = self.extractRoofs(ifcRoofs)
        if self.task.isCanceled():
            return False

        self.task.logging.emit(self.tr(u'Building geometry: wall surfaces are calculated'))
        geomWalls, roofsNew = self.calcWalls(base, roofs, height)
        if self.task.isCanceled():
            return False

        self.task.logging.emit(self.tr(u'Building geometry: wall surfaces between roofs are calculated'))
        geomWallsR, roofs = self.calcRoofWalls(roofs + roofsNew)
        if self.task.isCanceled():
            return False

        self.task.logging.emit(self.tr(u'Building geometry: roof surfaces are calculated'))
        roofs = self.calcRoofs(roofs, base)
        if self.task.isCanceled():
            return False

        self.task.logging.emit(self.tr(u'Building geometry: roof and wall surfaces are adjusted'))
        geomWalls += self.checkRoofWalls(geomWallsR, roofs)
        for roof in roofs:
            roof[1] = UtilitiesGeom.simplify(roof[1], 0.01, 0.05)
            self.progress += (2 / self.bldgCount / len(roofs))
            self.task.setProgress(self.progress)
        if self.task.isCanceled():
            return False

        # Geometrie
        links, surfaces = [], []
        if geomWalls is not None and len(geomWalls) > 0 and roofs[1] is not None and len(roofs) > 0:

            # Base
            link, gmlId = self.setElement(chBldg, base[1], "GroundSurface", 2)
            links.append(link)
            surfaces.append([gmlId, base[0]])

            # Roofs
            for roof in roofs:
                if roof[1].GetGeometryName() == "POLYGON":
                    link, gmlId = self.setElement(chBldg, roof[1], "RoofSurface", 2)
                    links.append(link)
                    if roof[0] is not None:
                        surfaces.append([gmlId, roof[0]])
                    else:
                        ifcRoofs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcRoof", result=[])
                        ifcRoofs += UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="ROOF")
                        surfaces.append([gmlId, ifcRoofs[0]])

            # Walls
            for geomWall in geomWalls:
                link, gmlId = self.setElement(chBldg, geomWall, "WallSurface", 2)
                links.append(link)
                # Zufällige IfcWall
                ifcWalls = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcWall", result=[])
                ifcRelSpaceBound = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcRelSpaceBoundary", result=[])
                randomWall = None
                for ifcWall in ifcWalls:
                    extCt, intCt = 0, 0
                    for ifcRelSpaceBoundary in ifcRelSpaceBound:
                        relElem = ifcRelSpaceBoundary.RelatedBuildingElement
                        if relElem == ifcWall:
                            if ifcRelSpaceBoundary.InternalOrExternalBoundary == "EXTERNAL":
                                extCt += 1
                            elif ifcRelSpaceBoundary.InternalOrExternalBoundary == "INTERNAL":
                                intCt += 1
                    if extCt > 0 or (intCt == 0 and UtilitiesIfc.findPset(ifcWall, "Pset_WallCommon", "IsExternal")):
                        randomWall = ifcWall
                        break
                surfaces.append([gmlId, randomWall])

        return links, base[1], surfaces

    def extractRoofs(self, ifcRoofs):
        """ Extrahiert die Geometrien von Dächern aus IFC

        Args:
            ifcRoofs: Die IFC-Dächer, aus denen extrahiert werden soll

        Returns:
            Dächer-Geometrien mit den zugehörigen IFC-Elementen, als Liste
        """
        roofs = []
        for ifcRoof in ifcRoofs:
            # noinspection PyUnresolvedReferences
            settings = ifcopenshell.geom.settings()
            settings.set(settings.USE_WORLD_COORDS, True)
            # noinspection PyUnresolvedReferences
            shape = ifcopenshell.geom.create_shape(settings, ifcRoof)
            # Vertizes
            verts = shape.geometry.verts
            grVertsCurr = [[round(verts[i], 5), round(verts[i + 1], 5), round(verts[i + 2], 5)] for i in
                           range(0, len(verts), 3)]
            # Flächen
            faces = shape.geometry.faces
            grFacesCurr = [[faces[i], faces[i + 1], faces[i + 2]] for i in range(0, len(faces), 3)]
            # Vertizes der Flächen
            grVertsList = []
            for face in grFacesCurr:
                facePoints = [grVertsCurr[face[0]], grVertsCurr[face[1]], grVertsCurr[face[2]]]
                if not ((facePoints[0][0] == facePoints[1][0] and facePoints[0][1] == facePoints[1][1]) or (
                        facePoints[0][0] == facePoints[2][0] and facePoints[0][1] == facePoints[2][1]) or (
                                facePoints[1][0] == facePoints[2][0] and facePoints[1][1] == facePoints[2][1])):
                    points = []
                    for facePoint in facePoints:
                        point = self.trans.georeferencePoint(facePoint)
                        points.append(point)
                    grVertsList.append(points)

            # Geometrien erstellen
            geometries = ogr.Geometry(ogr.wkbMultiPolygon)
            for grVerts in grVertsList:
                # Polygon aus Ring aus Punkten erstellen
                geometry = ogr.Geometry(ogr.wkbPolygon)
                ring = ogr.Geometry(ogr.wkbLinearRing)
                for grVert in grVerts:
                    ring.AddPoint(grVert[0], grVert[1], grVert[2])
                ring.CloseRings()
                geometry.AddGeometry(ring)
                if geometry.IsSimple():
                    geometries.AddGeometry(geometry)

            # Alle Flächen in der gleichen Ebene vereinigen
            checkList, heights, areas, geometriesRefUnionList = [], [], [], []
            for i in range(0, geometries.GetGeometryCount()):
                if i not in checkList:
                    # Geometrie
                    geometry = geometries.GetGeometryRef(i)
                    ring = geometry.GetGeometryRef(0)

                    # Multipolygon
                    geometriesRef = ogr.Geometry(ogr.wkbMultiPolygon)
                    geometriesRef.AddGeometry(geometry)

                    # Ebeneneigenschaften
                    apv = np.array(ring.GetPoint(0))
                    r1 = np.array(ring.GetPoint(1)) - np.array(ring.GetPoint(0))
                    r2 = np.array(ring.GetPoint(2)) - np.array(ring.GetPoint(0))
                    nv = np.cross(r1, r2)
                    checkList.append(i)

                    for j in range(i + 1, geometries.GetGeometryCount()):
                        # Geometrie
                        ogeometry = geometries.GetGeometryRef(j)
                        oring = ogeometry.GetGeometryRef(0)

                        # Ebeneneigenschaften
                        oapv = np.array(oring.GetPoint(0))
                        or1 = np.array(oring.GetPoint(1)) - np.array(oring.GetPoint(0))
                        or2 = np.array(oring.GetPoint(2)) - np.array(oring.GetPoint(0))
                        onv = np.cross(or1, or2)

                        # Schnittwinkel
                        angle = np.arccos(np.linalg.norm(np.dot(nv, onv)) / (np.linalg.norm(nv) * np.linalg.norm(onv)))
                        if math.isnan(angle) or angle < 0.001:

                            # Distanz zwischen den Ebenen
                            dist = (np.linalg.norm(np.dot(oapv - apv, nv))) / (np.linalg.norm(nv))
                            if dist < 0.001:
                                geometriesRef.AddGeometry(ogeometry)
                                checkList.append(j)

                    # Vereinigen
                    geometriesRefUnion = geometriesRef.UnionCascaded()
                    ring = geometriesRefUnion.GetGeometryRef(0)

                    # Höhe herausfinden
                    minHeight, maxHeight = sys.maxsize, -sys.maxsize
                    for k in range(0, ring.GetPointCount()):
                        point = ring.GetPoint(k)
                        if point[2] > maxHeight:
                            maxHeight = point[2]
                        if point[2] < minHeight:
                            minHeight = point[2]
                    height = maxHeight - minHeight
                    heights.append(maxHeight)

                    # Ungefähre Fläche
                    area = geometriesRefUnion.GetArea()
                    area3d = height * height + area
                    areas.append(area3d)

                    geometriesRefUnionList.append(geometriesRefUnion)

            # Aus den vorhandenen Flächen die Außenfläche heraussuchen
            finalRoof = None
            for i in range(0, len(areas)):
                if areas[i] > 0.9 * max(areas) and round(heights[i], 2) >= round(max(heights) - 0.01, 2):
                    finalRoof = geometriesRefUnionList[i]
            roofs.append([ifcRoof, finalRoof])

            if self.task.isCanceled():
                return False

            self.progress += (10 / self.bldgCount / len(ifcRoofs))
            self.task.setProgress(self.progress)

        return roofs

    def calcWalls(self, base, roofs, height):
        """ Berechnt die Grundwände in Level of Detail (LoD) 2

        Args:
            base: Die Geometrie der Grundfläche mit den zugehörigen IFC-Elementen, als Liste
            roofs: Die Geometrien der Dächer mit den zugehörigen IFC-Elementen ,als Liste
            height: Die Gebäudehöhe, als float

        Returns:
            Die berechneten Wand-Geometrien, als Liste
            Neu erstellte Dach-Geometrien mit den zugehörigen IFC-Elementen, als Liste
        """
        walls, roofPoints, wallsWORoof, missingRoof = [], [], [], []

        # Über die Eckpunkte der Grundfläche Wände hochziehen
        ringBase = base[1].GetGeometryRef(0)
        for i in range(0, ringBase.GetPointCount() - 1):

            # Wand ohne Dachbegrenzung
            geomWall = ogr.Geometry(ogr.wkbPolygon)
            ringWall = ogr.Geometry(ogr.wkbLinearRing)
            pt1, pt2 = ringBase.GetPoint(i), ringBase.GetPoint(i + 1)
            ringWall.AddPoint(pt1[0], pt1[1], pt1[2])
            ringWall.AddPoint(pt1[0], pt1[1], pt1[2] + height)
            ringWall.AddPoint(pt2[0], pt2[1], pt2[2] + height)
            ringWall.AddPoint(pt2[0], pt2[1], pt2[2])
            ringWall.CloseRings()
            geomWall.AddGeometry(ringWall)

            # Schnitt von Dächern mit der Wand
            intPoints, intLines = [], []
            for roof in roofs:
                roofGeom = roof[1]
                # 2D-Schnitt
                intersect = geomWall.Intersection(roofGeom)
                if not intersect.IsEmpty():
                    ipt1, ipt2 = intersect.GetPoint(0), intersect.GetPoint(1)

                    # Schnittgerade über Ebenenschnitt (damit die Höhen korrekt sind)
                    rring = roofGeom.GetGeometryRef(0)
                    wPlane = Plane(Point3D(pt1[0], pt1[1], pt1[2]), Point3D(pt1[0], pt1[1], pt1[2] + 1),
                                   Point3D(pt2[0], pt2[1], pt2[2]))
                    rPlane = Plane(Point3D(rring.GetPoint(0)[0], rring.GetPoint(0)[1], rring.GetPoint(0)[2]),
                                   Point3D(rring.GetPoint(1)[0], rring.GetPoint(1)[1], rring.GetPoint(1)[2]),
                                   Point3D(rring.GetPoint(2)[0], rring.GetPoint(2)[1], rring.GetPoint(2)[2]))
                    sLine = wPlane.intersection(rPlane)[0]

                    # Einsetzen der beiden Endpunkte des 2D-Schnitts in Schnittgerade
                    r1x = (ipt1[0] - sLine.p1[0]) / (sLine.p2[0] - sLine.p1[0])
                    r2x = (ipt2[0] - sLine.p1[0]) / (sLine.p2[0] - sLine.p1[0])
                    r1y = (ipt1[1] - sLine.p1[1]) / (sLine.p2[1] - sLine.p1[1])
                    r2y = (ipt2[1] - sLine.p1[1]) / (sLine.p2[1] - sLine.p1[1])
                    z1x = sLine.p1[2] + r1x * (sLine.p2[2] - sLine.p1[2])
                    z2x = sLine.p1[2] + r2x * (sLine.p2[2] - sLine.p1[2])
                    z1y = sLine.p1[2] + r1y * (sLine.p2[2] - sLine.p1[2])
                    z2y = sLine.p1[2] + r2y * (sLine.p2[2] - sLine.p1[2])

                    # Z-Wert
                    if type(z1x) == sympy.core.numbers.ComplexInfinity or type(z1x) == sympy.core.numbers.NaN:
                        z1 = float(z1y)
                    elif type(z1y) == sympy.core.numbers.ComplexInfinity or type(z1y) == sympy.core.numbers.NaN:
                        z1 = float(z1x)
                    else:
                        z1 = float((z1x + z1y) / 2)
                    if type(z2x) == sympy.core.numbers.ComplexInfinity or type(z2x) == sympy.core.numbers.NaN:
                        z2 = float(z2y)
                    elif type(z2y) == sympy.core.numbers.ComplexInfinity or type(z2y) == sympy.core.numbers.NaN:
                        z2 = float(z2x)
                    else:
                        z2 = float((z2x + z2y) / 2)

                    # Einsetzen des Z-Werts in 2D-Schnitt
                    ipt1, ipt2 = [ipt1[0], ipt1[1], z1], [ipt2[0], ipt2[1], z2]

                    # Merken der Schnittpunkte
                    if ipt1 not in intPoints:
                        intPoints.append(ipt1)
                    if ipt2 not in intPoints:
                        intPoints.append(ipt2)
                    intLines.append([ipt1, ipt2])

                if self.task.isCanceled():
                    return False

            # Normalfall: Wenn min. 1 Dach über einer Wand ist
            if len(intLines) > 0:

                # Neue Wand-Geometrie
                geomWall = ogr.Geometry(ogr.wkbPolygon)
                ringWall = ogr.Geometry(ogr.wkbLinearRing)
                pt1, pt2 = ringBase.GetPoint(i), ringBase.GetPoint(i + 1)
                ringWall.AddPoint(pt1[0], pt1[1], pt1[2])

                # Sortieren der Schnittpunkte und -linien
                intPoints = UtilitiesGeom.sortPoints(intPoints, pt1, pt2)
                intLines = UtilitiesGeom.sortLines(intLines, pt1, pt2)

                # Schnittlinien durchgehen
                lIx2 = None
                for intLine in intLines:

                    # Punkte der Schnittgeraden
                    sortIntLine = UtilitiesGeom.sortPoints(intLine, pt1, pt2)
                    ipt1, ipt2 = sortIntLine[0], sortIntLine[1]
                    ix1, ix2 = intPoints.index(ipt1), intPoints.index(ipt2)

                    if not (lIx2 is not None and ix1 < lIx2 and ix2 < lIx2):
                        # Überschneidung von Schnittlinien
                        if lIx2 is not None and ix1 < lIx2:
                            if ix2 > lIx2 and not (
                                    intPoints[ix2][0] == intPoints[lIx2][0] and intPoints[ix2][1] ==
                                    intPoints[lIx2][1]):
                                if abs(ipt2[0] - ipt1[0]) > abs(ipt2[1] - ipt1[1]):
                                    xDiff = ipt2[0] - ipt1[0]
                                    xPart = intPoints[lIx2][0] - ipt1[0]
                                    proz = xPart / xDiff
                                else:
                                    yDiff = ipt2[1] - ipt1[1]
                                    yPart = intPoints[lIx2][1] - ipt1[1]
                                    proz = yPart / yDiff
                                zDiff = ipt2[2] - ipt1[2]
                                z = ipt1[2] + proz * zDiff
                                ringWall.AddPoint(intPoints[lIx2][0], intPoints[lIx2][1], z)
                                roofPoints.append([intPoints[lIx2][0], intPoints[lIx2][1], z])
                        else:
                            # Wenn der Startpunkt keinen Schnitt hat: Fehlendes Dach auf dem Anfangsteil der Wand
                            if ix1 == 0 and (ipt1[0] != pt1[0] or ipt1[1] != pt1[1]):
                                self.task.logging.emit(
                                    self.tr(u'Due to a missing roof, a wall height can\'t be calculated!'))

                                # Höhe des folgenden Punktes nehmen
                                ringWall.AddPoint(pt1[0], pt1[1], ipt1[2])
                                roofPoints.append([pt1[0], pt1[1], ipt1[2]])

                                # Fehlendes Dach merken
                                missingRoof.append([[pt1[0], pt1[1], ipt1[2]], [ipt1[0], ipt1[1], ipt1[2]]])

                            ringWall.AddPoint(ipt1[0], ipt1[1], ipt1[2])

                        if ix2 - ix1 > 2 or (ix2 - ix1 == 2 and ix1 + 1 != lIx2):
                            for j in range(ix1 + 1, ix2):
                                if j != lIx2:
                                    if abs(ipt2[0] - ipt1[0]) > abs(ipt2[1] - ipt1[1]):
                                        xDiff = ipt2[0] - ipt1[0]
                                        xPart = intPoints[j][0] - ipt1[0]
                                        proz = xPart / xDiff
                                    else:
                                        yDiff = ipt2[1] - ipt1[1]
                                        yPart = intPoints[j][1] - ipt1[1]
                                        proz = yPart / yDiff
                                    zDiff = ipt2[2] - ipt1[2]
                                    z = ipt1[2] + proz * zDiff
                                    if z > intPoints[j][2]:
                                        ringWall.AddPoint(intPoints[j][0], intPoints[j][1], z)
                                        roofPoints.append([intPoints[j][0], intPoints[j][1], z])
                                    else:
                                        ringWall.AddPoint(ipt2[0], ipt2[1], ipt2[2])
                        elif lIx2 is None or (lIx2 is not None and not (
                                intPoints[ix2][0] == intPoints[lIx2][0] and intPoints[ix2][1] == intPoints[lIx2][1])):
                            ringWall.AddPoint(ipt2[0], ipt2[1], ipt2[2])
                        lIx2 = ix2

                lastPoint = ringWall.GetPoint(ringWall.GetPointCount() - 1)

                if self.task.isCanceled():
                    return False

                # Wenn der Endpunkt keinen Schnitt hat: Fehlendes Dach auf dem letzten Teil der Wand
                if lastPoint[0] != pt2[0] or lastPoint[1] != pt2[1]:
                    self.task.logging.emit(self.tr(u'Due to a missing roof, a wall height can\'t be calculated!'))

                    # Höhe des vorherigen Punktes fortführen
                    ringWall.AddPoint(pt2[0], pt2[1], lastPoint[2])
                    roofPoints.append([pt2[0], pt2[1], lastPoint[2]])

                    # Fehlendes Dach merken
                    missingRoof.append([[lastPoint[0], lastPoint[1], lastPoint[2]], [pt2[0], pt2[1], lastPoint[2]]])

                # Abschließen der Geometrie
                ringWall.AddPoint(pt2[0], pt2[1], pt2[2])
                ringWall.CloseRings()
                geomWall.AddGeometry(ringWall)
                walls.append(geomWall)

                # Merken der genutzten Wand-Dach-Schnittpunkte
                for k in range(0, len(intPoints)):
                    if intPoints[k] not in roofPoints:
                        roofPoints.append(intPoints[k])

            # Wenn über keinem Teil der Wand ein Dach ist
            else:
                self.task.logging.emit(self.tr(u'Due to a missing roof, a wall height can\'t be calculated!'))
                wallsWORoof.append([pt1, pt2])

            if self.task.isCanceled():
                return False

            self.progress += (8 / self.bldgCount / (ringBase.GetPointCount() - 1))
            self.task.setProgress(self.progress)

        # Wenn über keinem Teil der Wand ein Dach ist
        for wall in wallsWORoof:
            # Geometrie erstellen
            geomWall = ogr.Geometry(ogr.wkbPolygon)
            ringWall = ogr.Geometry(ogr.wkbLinearRing)
            pt1, pt2 = wall[0], wall[1]
            ringWall.AddPoint(pt1[0], pt1[1], pt1[2])

            # Höhe aus angrenzenden Wänden suchen, ansonsten Gebäudehöhe
            z1, z2 = height, height
            for roofPoint in roofPoints:
                if roofPoint[0] == pt1[0] and roofPoint[1] == pt1[1]:
                    z1 = roofPoint[2]
                if roofPoint[0] == pt2[0] and roofPoint[1] == pt2[1]:
                    z2 = roofPoint[2]

            # Wandpunkte setzen
            ringWall.AddPoint(pt1[0], pt1[1], z1)
            roofPoints.append([pt1[0], pt1[1], z1])
            ringWall.AddPoint(pt2[0], pt2[1], z2)
            roofPoints.append([pt2[0], pt2[1], z2])
            ringWall.AddPoint(pt2[0], pt2[1], pt2[2])

            # Geometrie abschließen
            ringWall.CloseRings()
            geomWall.AddGeometry(ringWall)
            walls.append(geomWall)

            # Fehlendes Fach merken
            missingRoof.append([[pt1[0], pt1[1], z1], [pt2[0], pt2[1], z2]])

            if self.task.isCanceled():
                return False

        self.progress += (1 / self.bldgCount)
        self.task.setProgress(self.progress)

        # Neue Dächer, falls keine vorhanden
        roofsNew, done = [], []
        for i in range(0, len(missingRoof)):
            if i not in done:

                # Neue Dach-Geometrie über der Dachkante
                line = missingRoof[i]
                geomRoof = ogr.Geometry(ogr.wkbPolygon)
                ringRoof = ogr.Geometry(ogr.wkbLinearRing)
                ringRoof.AddPoint(line[0][0], line[0][1], line[0][2])
                ringRoof.AddPoint(line[1][0], line[1][1], line[1][2])
                lastPt = line[1]

                ended = False

                # Prüfen auf angrenzende Wände ohne Dach: Zu gesamtem Dach zusammenfügen
                while not ended:
                    for j in range(i + 1, len(missingRoof)):
                        if j not in done:
                            if missingRoof[j][0] == lastPt:
                                ringRoof.AddPoint(missingRoof[j][1][0], missingRoof[j][1][1], missingRoof[j][1][2])
                                lastPt = missingRoof[j][1]
                                done.append(j)
                                break
                        if j == len(missingRoof) - 1:
                            ended = True

                # Wenn angrenzende Wände gefunden: Abschließen und Hinzufügen der Geometrie
                if ringRoof.GetPointCount() > 2:
                    ringRoof.CloseRings()
                    geomRoof.AddGeometry(ringRoof)
                    if not geomRoof.IsEmpty() and geomRoof.GetGeometryName() == "POLYGON":
                        roofsNew.append([None, geomRoof])

            if self.task.isCanceled():
                return False

        self.progress += (1 / self.bldgCount)
        self.task.setProgress(self.progress)

        return walls, roofsNew

    def calcRoofWalls(self, roofs):
        """ Berechnet die Wände zwischen zwei Dächern, die nicht bereits über die Grundfläche erstellt wurden

        Args:
            roofs: Die Geometrien der Dächer, als Liste

        Returns:
            Die berechneten neuen Wände, als Liste
            Die angepassten Dächer, als Liste
        """
        roofsOut = roofs.copy()
        walls, wallsLine = [], []

        # Alle Dächer miteinander auf Schnitt prüfen
        for i in range(0, len(roofs)):
            roof1 = roofs[i][1]
            for j in range(i + 1, len(roofs)):
                roof2 = roofs[j][1]
                if roof1.Intersects(roof2):
                    intersect = roof1.Intersection(roof2)
                    if intersect is not None and intersect.GetGeometryName() == "LINESTRING" and not \
                            intersect.IsEmpty():
                        ringR1, ringR2 = roof1.GetGeometryRef(0), roof2.GetGeometryRef(0)

                        # Z-Koordinaten über Ebenen-Geraden-Schnitte berechnen
                        r1Plane = UtilitiesGeom.getPlane(ringR1.GetPoint(0), ringR1.GetPoint(1), ringR1.GetPoint(2))
                        r2Plane = UtilitiesGeom.getPlane(ringR2.GetPoint(0), ringR2.GetPoint(1), ringR2.GetPoint(2))
                        w1Line = Line(Point3D(intersect.GetPoint(0)[0], intersect.GetPoint(0)[1], 0),
                                      Point3D(intersect.GetPoint(0)[0], intersect.GetPoint(0)[1], 100))
                        w2Line = Line(Point3D(intersect.GetPoint(1)[0], intersect.GetPoint(1)[1], 0),
                                      Point3D(intersect.GetPoint(1)[0], intersect.GetPoint(1)[1], 100))
                        z11, z12 = float(r1Plane.intersection(w1Line)[0][2]), float(r2Plane.intersection(w1Line)[0][2])
                        z21, z22 = float(r1Plane.intersection(w2Line)[0][2]), float(r2Plane.intersection(w2Line)[0][2])

                        # Wenn die Dächer nicht auf selber Höhe sind: Neue Wand dazwischen
                        if not z11 - 0.001 < z12 < z11 + 0.001:
                            geomWall = ogr.Geometry(ogr.wkbPolygon)
                            ringWall = ogr.Geometry(ogr.wkbLinearRing)
                            ringWall.AddPoint(intersect.GetPoint(0)[0], intersect.GetPoint(0)[1], min(z11, z12))
                            ringWall.AddPoint(intersect.GetPoint(0)[0], intersect.GetPoint(0)[1], max(z11, z12))
                            ringWall.AddPoint(intersect.GetPoint(1)[0], intersect.GetPoint(1)[1], max(z21, z22))
                            ringWall.AddPoint(intersect.GetPoint(1)[0], intersect.GetPoint(1)[1], min(z21, z22))
                            ringWall.CloseRings()
                            geomWall.AddGeometry(ringWall)
                            wallsLine.append(geomWall)

                    elif intersect is not None and intersect.GetGeometryName() == "POLYGON" and not intersect.IsEmpty():
                        ringInt = intersect.GetGeometryRef(0)
                        ringR1, ringR2 = roof1.GetGeometryRef(0), roof2.GetGeometryRef(0)
                        r1Plane = UtilitiesGeom.getPlane(ringR1.GetPoint(0), ringR1.GetPoint(1), ringR1.GetPoint(2))
                        r2Plane = UtilitiesGeom.getPlane(ringR2.GetPoint(0), ringR2.GetPoint(1), ringR2.GetPoint(2))
                        z1, z2 = None, None
                        pt1, pt2 = [], []

                        # Z-Koordinaten der beiden Dächer heraussuchen
                        ptz1, ptz2 = None, None
                        for k in range(0, ringInt.GetPointCount() - 1):
                            point = ogr.Geometry(ogr.wkbPoint)
                            point.AddPoint(ringInt.GetPoint(k)[0], ringInt.GetPoint(k)[1])
                            if roof1.Contains(point):
                                for r2PtM in ringR2.GetPoints():
                                    if (r2PtM[0] - 0.001 <= ringInt.GetPoint(k)[0] <= r2PtM[0] + 0.001) and (
                                            r2PtM[1] - 0.001 <= ringInt.GetPoint(k)[1] <= r2PtM[1] + 0.001):
                                        z2, ptz2 = r2PtM[2], [r2PtM[0], r2PtM[1]]
                                        pt1.append([point.GetPoint(0)[0], point.GetPoint(0)[1]])
                            elif roof2.Contains(point):
                                for r1PtM in ringR1.GetPoints():
                                    if (r1PtM[0] - 0.001 <= ringInt.GetPoint(k)[0] <= r1PtM[0] + 0.001) and (
                                            r1PtM[1] - 0.001 <= ringInt.GetPoint(k)[1] <= r1PtM[1] + 0.001):
                                        z1, ptz1 = r1PtM[2], [r1PtM[0], r1PtM[1]]
                                        pt2.append([point.GetPoint(0)[0], point.GetPoint(0)[1]])
                        if z1 is None:
                            wLine1 = Line(Point3D(ptz2[0], ptz2[1], 0), Point3D(ptz2[0], ptz2[1], 100))
                            sPoint1 = r1Plane.intersection(wLine1)[0]
                            z1 = float(sPoint1[2])
                        if z2 is None:
                            wLine2 = Line(Point3D(ptz1[0], ptz1[1], 0), Point3D(ptz1[0], ptz1[1], 100))
                            sPoint2 = r2Plane.intersection(wLine2)[0]
                            z2 = float(sPoint2[2])

                        # NEUE WÄNDE #
                        last = None
                        wallsInt = []
                        for n in range(0, ringInt.GetPointCount()):
                            point = [ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1]]

                            p1, p2, p3, p4 = None, None, None, None
                            if last is not None and ((z1 <= z2 and point not in pt1) or (z2 < z1 and point not in pt2)):
                                # Geraden
                                wLineLast = Line(Point3D(last[0], last[1], 0), Point3D(last[0], last[1], 100))
                                wLineCurr = Line(Point3D(ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1], 0),
                                                 Point3D(ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1], 100))

                                # Schnittpunkte
                                sPoint1Last = r1Plane.intersection(wLineLast)[0]
                                p1Last = [last[0], last[1], float(sPoint1Last[2])]
                                sPoint2Last = r2Plane.intersection(wLineLast)[0]
                                p2Last = [last[0], last[1], float(sPoint2Last[2])]
                                sPoint1Curr = r1Plane.intersection(wLineCurr)[0]
                                p1Curr = [ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1], float(sPoint1Curr[2])]
                                sPoint2Curr = r2Plane.intersection(wLineCurr)[0]
                                p2Curr = [ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1], float(sPoint2Curr[2])]

                                # Wandgeometrie
                                geomWall = ogr.Geometry(ogr.wkbPolygon)
                                ringWall = ogr.Geometry(ogr.wkbLinearRing)

                                # Wenn Dach 1 unter Dach 2
                                if z1 <= z2 and point not in pt1:
                                    p1, p2, p3, p4 = p1Curr, p2Curr, p2Last, p1Last
                                # Wenn Dach 1 über Dach 2
                                elif z2 < z1 and point not in pt2:
                                    p1, p2, p3, p4 = p2Curr, p1Curr, p1Last, p2Last

                                # Wandgeometrie
                                ringWall.AddPoint(p1[0], p1[1], p1[2])
                                ringWall.AddPoint(p2[0], p2[1], p2[2])
                                ringWall.AddPoint(p3[0], p3[1], p3[2])
                                ringWall.AddPoint(p4[0], p4[1], p4[2])
                                ringWall.CloseRings()
                                geomWall.AddGeometry(ringWall)
                                wallsInt.append(geomWall)

                                # Letzten Schnittpunkt für folgenden Durchlauf speichern
                                last = [ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1]]

                            elif last is None:
                                # Letzten Schnittpunkt für folgenden Durchlauf speichern
                                last = [ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1]]

                            if not (z1 <= z2 and point not in pt1) and not (z2 < z1 and point not in pt2):
                                last = None

                        walls += wallsInt

                        # ANPASSUNG DER DÄCHER #
                        if z1 <= z2:
                            geomRoof = roofsOut[j][1]
                        else:
                            geomRoof = roofsOut[i][1]

                        roofInt = geomRoof.Difference(intersect).Simplify(0.0)
                        ringInt = roofInt.GetGeometryRef(0)
                        ringRoof = geomRoof.GetGeometryRef(0)
                        rPlane = UtilitiesGeom.getPlane(ringRoof.GetPoint(0), ringRoof.GetPoint(1),
                                                        ringRoof.GetPoint(2))

                        # Neue Geometrie
                        geomRoofOut = ogr.Geometry(ogr.wkbPolygon)
                        ringRoofOut = ogr.Geometry(ogr.wkbLinearRing)

                        # Punkte
                        for o in range(0, ringInt.GetPointCount()):
                            rLine = Line(Point3D(ringInt.GetPoint(o)[0], ringInt.GetPoint(o)[1], 0),
                                         Point3D(ringInt.GetPoint(o)[0], ringInt.GetPoint(o)[1], 100))
                            z = None
                            for p in range(0, ringRoof.GetPointCount() - 1):
                                if ringInt.GetPoint(o)[0] == ringRoof.GetPoint(p)[0] and ringInt.GetPoint(o)[1] == \
                                        ringRoof.GetPoint(p)[1]:
                                    z = ringRoof.GetPoint(p)[2]
                                    break
                            if z is None:
                                sPoint = rPlane.intersection(rLine)[0]
                                z = float(sPoint[2])
                            ringRoofOut.AddPoint(ringInt.GetPoint(o)[0], ringInt.GetPoint(o)[1], z)

                        # Geometrie abschließen
                        ringRoofOut.CloseRings()
                        geomRoofOut.AddGeometry(ringRoofOut)
                        if z1 <= z2:
                            roofsOut[j][1] = geomRoofOut
                        else:
                            roofsOut[i][1] = geomRoofOut

                if self.task.isCanceled():
                    return False

            self.progress += (5 / self.bldgCount / len(roofs))
            self.task.setProgress(self.progress)

        # ÜBERPRÜFUNG DER WÄNDE #
        walls += wallsLine
        wallsCheck, wallsMod = walls.copy(), {}

        # Verschneidung aller neuen Wände miteinander
        for o in range(0, len(wallsCheck)):
            for p in range(o + 1, len(wallsCheck)):
                wallO = wallsMod[str(o)] if str(o) in wallsMod else wallsCheck[o]
                wallP = wallsMod[str(p)] if str(p) in wallsMod else wallsCheck[p]
                intersect = wallO.Intersection(wallP)
                if not intersect.IsEmpty():
                    ipt1, ipt2 = intersect.GetPoint(0), intersect.GetPoint(1)
                    wallCheckORing = wallO.GetGeometryRef(0)
                    ptO1, ptO2 = wallCheckORing.GetPoint(1), wallCheckORing.GetPoint(2)
                    wallCheckPRing = wallP.GetGeometryRef(0)
                    ptP1, ptP2 = wallCheckPRing.GetPoint(1), wallCheckPRing.GetPoint(2)

                    # Wenn Verschneidung = Wand: Wand entfernen
                    if (ipt1[0] == ptO1[0] and ipt1[1] == ptO1[1] and ipt2[0] == ptO2[0] and ipt2[1] == ptO2[1]) or (
                            ipt1[0] == ptO2[0] and ipt1[1] == ptO2[1] and ipt2[0] == ptO1[0] and ipt2[1] == ptO1[1]):
                        walls.remove(wallO)

                    # Wenn Verschneidung teilweise Wand: Entsprechenden Wandteil entfernen
                    elif (ipt1[0] == ptO1[0] and ipt1[1] == ptO1[1]) or (ipt1[0] == ptO2[0] and ipt1[1] == ptO2[1]) or (
                            ipt2[0] == ptO1[0] and ipt2[1] == ptO1[1]) or (ipt2[0] == ptO2[0] and ipt2[1] == ptO2[1]):
                        diffIPt = np.sqrt(np.square(ipt2[0] - ipt1[0]) + np.square(ipt2[1] - ipt1[1]))
                        diffOPt = np.sqrt(np.square(ptO2[0] - ptO1[0]) + np.square(ptO2[1] - ptO1[1]))
                        if diffIPt > diffOPt:
                            walls.remove(wallO)
                        else:
                            geomWallCut = ogr.Geometry(ogr.wkbPolygon)
                            ringWallCut = ogr.Geometry(ogr.wkbLinearRing)
                            if (ptP1[0] == ipt1[0] and ptP1[1] == ipt1[1]) or (
                                    ptP1[0] == ipt2[0] and ptP1[1] == ipt2[1]):
                                zU, zO = wallCheckPRing.GetPoint(0)[2], ptP1[2]
                            else:
                                zU, zO = wallCheckPRing.GetPoint(3)[2], ptP2[2]
                            if ptO1[0] == ipt1[0] and ptO1[1] == ipt1[1]:
                                ringWallCut.AddPoint(ipt2[0], ipt2[1], zU)
                                ringWallCut.AddPoint(ipt2[0], ipt2[1], zO)
                                ringWallCut.AddPoint(ptO2[0], ptO2[1], ptO2[2])
                                ringWallCut.AddPoint(ptO2[0], ptO2[1], wallCheckORing.GetPoint(3)[2])
                            elif ptO1[0] == ipt2[0] and ptO1[1] == ipt2[1]:
                                ringWallCut.AddPoint(ipt1[0], ipt1[1], zU)
                                ringWallCut.AddPoint(ipt1[0], ipt1[1], zO)
                                ringWallCut.AddPoint(ptO2[0], ptO2[1], ptO2[2])
                                ringWallCut.AddPoint(ptO2[0], ptO2[1], wallCheckORing.GetPoint(3)[2])
                            else:
                                ringWallCut.AddPoint(ptO1[0], ptO1[1], ptO1[2])
                                ringWallCut.AddPoint(ptO1[0], ptO1[1], wallCheckORing.GetPoint(0)[2])
                                if ptO2[0] == ipt1[0] and ptO2[1] == ipt1[1]:
                                    ringWallCut.AddPoint(ipt2[0], ipt2[1], zO)
                                    ringWallCut.AddPoint(ipt2[0], ipt2[1], zU)
                                elif ptO2[0] == ipt2[0] and ptO2[1] == ipt2[1]:
                                    ringWallCut.AddPoint(ipt1[0], ipt1[1], zO)
                                    ringWallCut.AddPoint(ipt1[0], ipt1[1], zU)
                            ringWallCut.CloseRings()
                            geomWallCut.AddGeometry(ringWallCut)

                            wallsMod[str(o)] = geomWallCut
                            ix = walls.index(wallO)
                            walls[ix] = geomWallCut

                    # Wenn Verschneidung = Wand: Wand entfernen
                    if (ipt1[0] == ptP1[0] and ipt1[1] == ptP1[1] and ipt2[0] == ptP2[0] and ipt2[1] == ptP2[1]) or (
                            ipt1[0] == ptP2[0] and ipt1[1] == ptP2[1] and ipt2[0] == ptP1[0] and ipt2[1] == ptP1[1]):
                        walls.remove(wallP)

                    # Wenn Verschneidung teilweise Wand: Entsprechenden Wandteil entfernen
                    elif (ipt1[0] == ptP1[0] and ipt1[1] == ptP1[1]) or (ipt1[0] == ptP2[0] and ipt1[1] == ptP2[1]) or (
                            ipt2[0] == ptP1[0] and ipt2[1] == ptP1[1]) or (ipt2[0] == ptP2[0] and ipt2[1] == ptP2[1]):
                        diffIPt = np.sqrt(np.square(ipt2[0] - ipt1[0]) + np.square(ipt2[1] - ipt1[1]))
                        diffPPt = np.sqrt(np.square(ptP2[0] - ptP1[0]) + np.square(ptP2[1] - ptP1[1]))
                        if diffIPt > diffPPt:
                            walls.remove(wallP)
                        else:
                            geomWallCut = ogr.Geometry(ogr.wkbPolygon)
                            ringWallCut = ogr.Geometry(ogr.wkbLinearRing)
                            if (ptO1[0] == ipt1[0] and ptO1[1] == ipt1[1]) or (
                                    ptO1[0] == ipt2[0] and ptO1[1] == ipt2[1]):
                                zU, zO = wallCheckORing.GetPoint(0)[2], ptO1[2]
                            else:
                                zU, zO = wallCheckORing.GetPoint(3)[2], ptO2[2]
                            if ptP1[0] == ipt1[0] and ptP1[1] == ipt1[1]:
                                ringWallCut.AddPoint(ipt2[0], ipt2[1], zU)
                                ringWallCut.AddPoint(ipt2[0], ipt2[1], zO)
                                ringWallCut.AddPoint(ptP2[0], ptP2[1], ptP2[2])
                                ringWallCut.AddPoint(ptP2[0], ptP2[1], wallCheckPRing.GetPoint(3)[2])
                            elif ptP1[0] == ipt2[0] and ptP1[1] == ipt2[1]:
                                ringWallCut.AddPoint(ipt1[0], ipt1[1], zU)
                                ringWallCut.AddPoint(ipt1[0], ipt1[1], zO)
                                ringWallCut.AddPoint(ptP2[0], ptP2[1], ptP2[2])
                                ringWallCut.AddPoint(ptP2[0], ptP2[1], wallCheckPRing.GetPoint(3)[2])
                            else:
                                ringWallCut.AddPoint(ptP1[0], ptP1[1], wallCheckPRing.GetPoint(0)[2])
                                ringWallCut.AddPoint(ptP1[0], ptP1[1], ptP1[2])
                                if ptP2[0] == ipt1[0] and ptP2[1] == ipt1[1]:
                                    ringWallCut.AddPoint(ipt2[0], ipt2[1], zO)
                                    ringWallCut.AddPoint(ipt2[0], ipt2[1], zU)
                                elif ptP2[0] == ipt2[0] and ptP2[1] == ipt2[1]:
                                    ringWallCut.AddPoint(ipt1[0], ipt1[1], zO)
                                    ringWallCut.AddPoint(ipt1[0], ipt1[1], zU)
                            ringWallCut.CloseRings()
                            geomWallCut.AddGeometry(ringWallCut)

                            wallsMod[str(p)] = geomWallCut
                            ix = walls.index(wallP)
                            walls[ix] = geomWallCut

                if self.task.isCanceled():
                    return False

            self.progress += (5 / self.bldgCount / len(wallsCheck))
            self.task.setProgress(self.progress)

        return walls, roofsOut

    def calcRoofs(self, roofsIn, base):
        """ Passt die Dächer, u.a. auf die Grundfläche und überschneidende Dächer, in Level of Detail (LoD) 2 an

        Args:
            roofsIn: Die Geometrien der Dächer mit den zugehörigen IFC-Elementen, als Liste
            base: Die Geometrie der Grundfläche mit dem zugehörigen IFC-Element

        Returns:
            Die berechneten Dächer, als Liste
        """
        roofs = []

        # Alle Dächer überprüfen
        for roofInElem in roofsIn:
            roofIn = roofInElem[1]
            if roofIn is None:
                continue

            # Mit Grundfläche verschneiden
            intersection = roofIn.Intersection(base[1])
            for intGeometry in intersection:
                if intersection.GetGeometryCount() == 1:
                    ringInt = intersection.GetGeometryRef(0)
                else:
                    ringInt = intGeometry.GetGeometryRef(0)
                    if ringInt is None:
                        continue

                # Neue Dach-Geometrie
                geomRoof = ogr.Geometry(ogr.wkbPolygon)
                ringRoof = ogr.Geometry(ogr.wkbLinearRing)

                # Schnittgeometrie nehmen und mit Z-Koordinaten versehen
                for i in range(ringInt.GetPointCount() - 1, -1, -1):
                    # Z-Koordinate über Ebenenschnitt
                    ptInt = ringInt.GetPoint(i)
                    ringIn = roofIn.GetGeometryRef(0)
                    rPlane = Plane(Point3D(ringIn.GetPoint(0)[0], ringIn.GetPoint(0)[1], ringIn.GetPoint(0)[2]),
                                   Point3D(ringIn.GetPoint(1)[0], ringIn.GetPoint(1)[1], ringIn.GetPoint(1)[2]),
                                   Point3D(ringIn.GetPoint(2)[0], ringIn.GetPoint(2)[1], ringIn.GetPoint(2)[2]))
                    wLine = Line(Point3D(ptInt[0], ptInt[1], 0), Point3D(ptInt[0], ptInt[1], 100))
                    sPoint = rPlane.intersection(wLine)[0]
                    z = float(sPoint[2])

                    ringRoof.AddPoint(ptInt[0], ptInt[1], z)

                # Abschließen und Hinzufügen der Geometrie
                ringRoof.CloseRings()
                geomRoof.AddGeometry(ringRoof)
                if geomRoof is not None:
                    roofs.append([roofInElem[0], geomRoof])

                if self.task.isCanceled():
                    return False

            self.progress += (10 / self.bldgCount / len(roofsIn))
            self.task.setProgress(self.progress)

        return roofs

    def checkRoofWalls(self, wallsIn, roofs):
        """ Überprüft die neu erstellten Wand-Geometrien und sortiert sie ggf. aus

        Args:
            wallsIn: Die Wand-Geometrien, die überprüft werden sollen, als Liste
            roofs: Die Dach-Geometrien mit den zugehörigen IFC-Elementen, als Liste

        Returns:
            Die überprüften Wand-Geometrien, als Liste
        """
        wallsChecked = []

        # Wände mit Dächern verschneiden
        for wall in wallsIn:
            anyInt = False
            for roof in roofs:
                roofGeom = roof[1]
                intersect = wall.Intersection(roofGeom)
                if not intersect.IsEmpty():

                    # Wenn MultiPolygon/MultiLineString als Schnitt: Zusammenführen
                    if intersect.GetGeometryCount() > 1:
                        startPt = intersect.GetGeometryRef(0).GetPoint(0)
                        endPt = intersect.GetGeometryRef(intersect.GetGeometryCount() - 1).GetPoint(1)
                        intersect2 = ogr.Geometry(ogr.wkbLineString)
                        intersect2.AddPoint(startPt[0], startPt[1], startPt[2])
                        intersect2.AddPoint(endPt[0], endPt[1], endPt[2])
                        intersect = intersect2
                    wallRing = wall.GetGeometryRef(0)

                    # Prüfen, ob Wand insgesamt unter Dächern
                    pt1Check, pt2Check = False, False
                    for i in range(0, wallRing.GetPointCount()):
                        pt = wallRing.GetPoint(i)
                        if pt[0] == intersect.GetPoint(0)[0] and pt[1] == intersect.GetPoint(0)[1]:
                            pt1Check = True
                        elif pt[0] == intersect.GetPoint(1)[0] and pt[1] == intersect.GetPoint(1)[1]:
                            pt2Check = True
                    if pt1Check and pt2Check:
                        anyInt = True

                if self.task.isCanceled():
                    return False

            if anyInt:
                wall = UtilitiesGeom.simplify(wall, 0.01, 0.05)
                wallsChecked.append(wall)

            if self.task.isCanceled():
                return False

            self.progress += (8 / self.bldgCount / len(wallsIn))
            self.task.setProgress(self.progress)

        wallsOut = UtilitiesGeom.union3D(wallsChecked)
        return wallsOut

    def setElement(self, chBldg, geometry, type, lod):
        """ Setzt ein CityGML-Objekts

        Args:
            chBldg: XML-Element, an dem das Objekt angefügt werden soll
            geometry: Die Geometrie des Objekts
            type: Der Typ des Objekts
            lod: Level of Detail (LoD)

        Returns:
            Die Poly-ID der Geometrie
            Die GML-ID des Objekts
        """
        self.geom.AddGeometry(geometry)
        self.bldgGeom.AddGeometry(geometry)

        # XML-Struktur
        chBldgBB = etree.SubElement(chBldg, QName(XmlNs.bldg, "boundedBy"))
        chBldgS = etree.SubElement(chBldgBB, QName(XmlNs.bldg, type))
        gmlId = "GML_" + str(uuid.uuid4())
        chBldgS.set(QName(XmlNs.gml, "id"), gmlId)
        chBldgSurfSMS = etree.SubElement(chBldgS, QName(XmlNs.bldg, "lod" + str(lod) + "MultiSurface"))
        chBldgMS = etree.SubElement(chBldgSurfSMS, QName(XmlNs.bldg, "MultiSurface"))
        chBldgSM = etree.SubElement(chBldgMS, QName(XmlNs.bldg, "surfaceMember"))

        # Geometrie
        geomXML = UtilitiesGeom.geomToGml(geometry)
        chBldgSM.append(geomXML)

        # GML-ID
        chBldgPol = chBldgSM[0]
        polyId = "PolyID" + str(uuid.uuid4())
        chBldgPol.set(QName(XmlNs.gml, "id"), polyId)

        return polyId, gmlId
