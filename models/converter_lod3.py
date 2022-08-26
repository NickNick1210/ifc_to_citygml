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
from copy import deepcopy

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
from sympy import Point3D, Line

# Plugin
from .xmlns import XmlNs
from .utilitiesGeom import UtilitiesGeom
from .utilitiesIfc import UtilitiesIfc
from .converter_gen import GenConverter
from .converter_eade import EADEConverter


#####


class LoD3Converter:
    """ Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien in LoD3 """

    def __init__(self, parent, ifc, name, trans, eade):
        """ Konstruktor der Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien in LoD3

        Args:
            parent: Die zugrunde liegende zentrale Converter-Klasse
            ifc: IFC-Datei
            name: Name des Modells
            trans: Transformer-Objekt
            eade: Ob die EnergyADE gewählt wurde als Boolean
        """

        # Initialisierung von Attributen
        self.parent = parent
        self.ifc = ifc
        self.name = name
        self.trans = trans
        self.eade = eade
        self.geom, self.bldgGeom = ogr.Geometry(ogr.wkbGeometryCollection), ogr.Geometry(ogr.wkbGeometryCollection)

    @staticmethod
    def tr(msg):
        """ Übersetzt den gegebenen Text

        Args:
            msg: zu übersetzender Text

        Returns:
            Übersetzter Text
        """
        return QCoreApplication.translate('LoD3Converter', msg)

    def convert(self, root):
        """ Konvertiert von IFC zu CityGML im Level of Detail (LoD) 3

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
            chCOM = etree.SubElement(root, QName(XmlNs.core, "cityObjectMember"))
            chBldg = etree.SubElement(chCOM, QName(XmlNs.bldg, "Building"))

            # Konvertierung
            self.parent.dlg.log(self.tr(u'Building attributes are extracted'))
            GenConverter.convertBldgAttr(self.ifc, ifcBuilding, chBldg)
            links, footPrint, surfaces = self.convertBldgBound(ifcBuilding, chBldg)
            GenConverter.convertLoDSolid(chBldg, links, 3)
            self.parent.dlg.log(self.tr(u'Building address is extracted'))
            GenConverter.convertAddress(ifcBuilding, ifcSite, chBldg)
            self.parent.dlg.log(self.tr(u'Building bound is calculated'))
            bbox = GenConverter.convertBound(self.geom, chBound, self.trans)

            # EnergyADE
            if self.eade:
                self.parent.dlg.log(self.tr(u'Energy ADE is calculated'))
                self.parent.dlg.log(self.tr(u'Energy ADE: weather data is extracted'))
                EADEConverter.convertWeatherData(ifcProject, ifcSite, chBldg, bbox)
                self.parent.dlg.log(self.tr(u'Energy ADE: building attributes are extracted'))
                EADEConverter.convertBldgAttr(self.ifc, ifcBuilding, chBldg, bbox, footPrint)
                self.parent.dlg.log(self.tr(u'Energy ADE: thermal zone is calculated'))
                linkUZ, chBldgTZ, constructions = EADEConverter.calcThermalZone(self.ifc, ifcBuilding, chBldg, root,
                                                                                surfaces, 3)
                self.parent.dlg.log(self.tr(u'Energy ADE: usage zone is calculated'))
                EADEConverter.calcUsageZone(self.ifc, ifcProject, ifcBuilding, chBldg, linkUZ, chBldgTZ)
                self.parent.dlg.log(self.tr(u'Energy ADE: construction is calculated'))
                materials = EADEConverter.convertConstructions(root, constructions)
                self.parent.dlg.log(self.tr(u'Energy ADE: material is calculated'))
                EADEConverter.convertMaterials(root, materials)

        return root

    def convertBldgBound(self, ifcBuilding, chBldg):
        """ Konvertiert den erweiterten Gebäudeumriss von IFC zu CityGML in Level of Detail (LoD) 3

        Args:
            ifcBuilding: Das IFC-Gebäude, aus dem der Gebäudeumriss entnommen werden soll
            chBldg: XML-Element, an dem der Gebäudeumriss angefügt werden soll

        Returns:
            GML-IDs der Bestandteile des erweiterten Gebäudeumrisses, als Liste
            Die Grundflächengeometrie
            Die GML-IDs der Bestandteile mit zugehörigen IFC-Elementen, als Liste
        """
        # Berechnung
        self.parent.dlg.log(self.tr(u'Building geometry: base surfaces are calculated'))
        bases, basesOrig, floors = self.calcBases(ifcBuilding)
        self.parent.dlg.log(self.tr(u'Building geometry: roof surfaces are calculated'))
        roofs, roofsOrig = self.calcRoofs(ifcBuilding)
        self.parent.dlg.log(self.tr(u'Building geometry: wall surfaces are calculated'))
        walls = self.calcWalls(ifcBuilding)
        self.parent.dlg.log(self.tr(u'Building geometry: door surfaces are calculated'))
        openings = self.calcOpenings(ifcBuilding, "ifcDoor")
        self.parent.dlg.log(self.tr(u'Building geometry: window surfaces are calculated'))
        openings += self.calcOpenings(ifcBuilding, "ifcWindow")
        self.parent.dlg.log(self.tr(u'Building geometry: openings are assigned to walls'))
        walls = self.assignOpenings(openings, walls)
        self.parent.dlg.log(self.tr(u'Building geometry: wall and opening surfaces are adjusted to each other'))
        walls, wallMainCounts = self.adjustWallOpenings(walls)
        self.parent.dlg.log(self.tr(u'Building geometry: wall surfaces are adjusted in their height'))
        walls = self.adjustWallSize(walls, floors, roofs, basesOrig, roofsOrig, wallMainCounts)

        # Geometrie
        links, surfaces = [], []
        for base in bases:
            linksBase, gmlId, openSurf = self.setElementGroup(chBldg, base[0], "GroundSurface", 3, base[1], base[2])
            links += linksBase
            surfaces.append([gmlId, base[3]])
            surfaces += openSurf
        for roof in roofs:
            linksRoof, gmlId, openSurf = self.setElementGroup(chBldg, roof[0], "RoofSurface", 3, roof[1], roof[2])
            links += linksRoof
            surfaces.append([gmlId, roof[3]])
            surfaces += openSurf
        for wall in walls:
            linksWall, gmlId, openSurf = self.setElementGroup(chBldg, wall[0], "WallSurface", 3, wall[1], wall[2])
            links += linksWall
            surfaces.append([gmlId, wall[3]])
            surfaces += openSurf
        return links, bases[0][0][0], surfaces

    def calcBases(self, ifcBuilding):
        """ Berechnet die Grundfläche in Level of Detail (LoD) 3

        Args:
            ifcBuilding: Das Gebäude, aus dem die Grundflächen entnommen werden sollen

        Returns:
            Die berechneten Grundflächen-Geometrien, als Liste
        """
        bases, baseNames, basesOrig = [], [], []

        # IFC-Elemente der Grundfläche
        ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="BASESLAB")
        floor = False
        if len(ifcSlabs) == 0:
            ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="FLOOR")
            floor = True
            # Wenn keine Grundfläche vorhanden
            if len(ifcSlabs) == 0:
                self.parent.dlg.log(self.tr(u"Due to the missing baseslab, it will also be missing in CityGML"))
                return []

        # Namen der Grundflächen heraussuchen
        for ifcSlab in ifcSlabs:
            baseNames.append(ifcSlab.Name)

        for i in range(0, len(ifcSlabs)):
            ifcSlab = ifcSlabs[i]
            # noinspection PyUnresolvedReferences
            settings = ifcopenshell.geom.settings()
            settings.set(settings.USE_WORLD_COORDS, True)
            # noinspection PyUnresolvedReferences
            shape = ifcopenshell.geom.create_shape(settings, ifcSlab)
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
                points = []
                for facePoint in facePoints:
                    point = self.trans.georeferencePoint(facePoint)
                    points.append(point)
                grVertsList.append(points)

            # Geometrien erstellen
            geometries = []
            for grVerts in grVertsList:
                # Polygon aus Ring aus Punkten erstellen
                geometry = ogr.Geometry(ogr.wkbPolygon)
                ring = ogr.Geometry(ogr.wkbLinearRing)
                for grVert in grVerts:
                    ring.AddPoint(grVert[0], grVert[1], grVert[2])
                ring.CloseRings()
                geometry.AddGeometry(ring)
                geometries.append(geometry)

            # Alle Flächen in der gleichen Ebene vereinigen
            slabGeom = UtilitiesGeom.union3D(geometries)
            slabGeom = UtilitiesGeom.simplify(slabGeom, 0.001, 0.05)

            # Höhen und Flächen der einzelnen Oberflächen heraussuchen
            heights, areas = [], []
            for geom in slabGeom:
                ring = geom.GetGeometryRef(0)
                if ring is None:
                    heights.append(sys.maxsize)
                    areas.append(-sys.maxsize)
                    continue
                # Höhe herausfinden
                minHeight, maxHeight = sys.maxsize, -sys.maxsize
                for k in range(0, ring.GetPointCount()):
                    point = ring.GetPoint(k)
                    if point[2] > maxHeight:
                        maxHeight = point[2]
                    if point[2] < minHeight:
                        minHeight = point[2]
                height = maxHeight - minHeight
                heights.append(minHeight)

                # Ungefähre Fläche
                area = geom.GetArea()
                area3d = height * height + area
                areas.append(area3d)

            # Aus den vorhandenen Flächen die benötigten heraussuchen
            finalSlab = []
            for j in range(0, len(areas)):
                if areas[j] > 0.9 * max(areas) and heights[j] <= min(heights) + 0.01:
                    finalSlab.append(slabGeom[j])

            bases.append([finalSlab, baseNames[i], [], ifcSlab])
            basesOrig.append(slabGeom)

        floors = bases

        # Benötigte ifcSlabs heraussuchen, falls nur .FLOOR
        if floor:
            bases.sort(key=lambda elem: (elem[0][0].GetGeometryRef(0).GetPoint(0)[2]))
            minHeight = bases[0][0][0].GetGeometryRef(0).GetPoint(0)[2]
            finalBases, removedBases = deepcopy(bases), []
            for i in range(0, len(bases)):

                # Unterste Flächen ohne Prüfungs durchlassen
                currHeight = bases[i][0][0].GetGeometryRef(0).GetPoint(0)[2]
                gotDiff, diffGeom = False, None
                if not (minHeight - 0.01 < currHeight < minHeight + 0.01):

                    # Differenz zwischen Fläche und den vorherigen Flächen berechnen
                    base = bases[i][0][0]
                    for k in range(0, i):
                        if k not in removedBases:
                            baseLast = bases[k][0][0]
                            diff = base.Difference(baseLast)
                            bArea = base.Area()
                            diffArea = diff.Area()

                            # Differenzfläche muss bestimmte Größe haben,
                            # um relevant, aber nicht zu gleich zur Ausgangsfläche zu sein
                            if diff is not None and diffArea < bArea * 0.99:
                                gotDiff = True
                                if not diff.IsEmpty() and (bArea * 0.03 < diffArea or diffArea > 2) and diffArea > 0.1:

                                    # Diff-Geometrie unter Korrektur der Höhe übernehmen
                                    diffGeom = ogr.Geometry(ogr.wkbPolygon)
                                    diffRing = ogr.Geometry(ogr.wkbLinearRing)
                                    height = base.GetGeometryRef(0).GetPoint(0)[2]
                                    for n in range(0, diff.GetGeometryCount()):
                                        dRingOld = diff.GetGeometryRef(0)
                                        for m in range(0, dRingOld.GetPointCount()):
                                            diffRing.AddPoint(dRingOld.GetPoint(m)[0], dRingOld.GetPoint(m)[1], height)
                                        diffRing.CloseRings()
                                        if diffRing is not None and not diffRing.IsEmpty():
                                            diffGeom.AddGeometry(diffRing)

                # Letzte Differenz übernehmen.
                if diffGeom is not None:
                    finalBases[i][0][0] = diffGeom

                # Falls nur Differenzen stattgefunden haben, die der Ausgangsfläche entsprechen: Entfernen
                elif gotDiff:
                    removedBases.append(i)
            removedBases.sort(reverse=True)
            for removedBase in removedBases:
                finalBases.pop(removedBase)

        # Falls nur .BASE
        else:
            finalBases = bases

        return finalBases, basesOrig, floors

    def calcRoofs(self, ifcBuilding):
        """ Berechnet die Dächer in Level of Detail (LoD) 3

        Args:
            ifcBuilding: Das Gebäude, aus dem die Dächer entnommen werden sollen

        Returns:
            Die berechneten Dächer, als Liste
        """
        roofs, roofNames, roofsOrig = [], [], []

        # IFC-Elemente des Daches
        ifcRoofs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="ROOF")
        ifcRoofs += UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcRoof", result=[])
        if len(ifcRoofs) == 0:
            self.parent.dlg.log(self.tr(u"Due to the missing roofs, it will also be missing in CityGML"))
            return []

        # Namen der Dächer heraussuchen
        for ifcRoof in ifcRoofs:
            roofNames.append(ifcRoof.Name)

        # Geometrie
        for i in range(0, len(ifcRoofs)):
            ifcRoof = ifcRoofs[i]
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
                points = []
                for facePoint in facePoints:
                    point = self.trans.georeferencePoint(facePoint)
                    points.append(point)
                grVertsList.append(points)

            # Geometrien erstellen
            geometries = []
            for grVerts in grVertsList:
                # Polygon aus Ring aus Punkten erstellen
                geometry = ogr.Geometry(ogr.wkbPolygon)
                ring = ogr.Geometry(ogr.wkbLinearRing)
                for grVert in grVerts:
                    ring.AddPoint(grVert[0], grVert[1], grVert[2])
                ring.CloseRings()
                geometry.AddGeometry(ring)
                geometries.append(geometry)

            # Alle Flächen in der gleichen Ebene vereinigen
            roofGeom = UtilitiesGeom.union3D(geometries)
            roofGeom = UtilitiesGeom.simplify(roofGeom, 0.001, 0.05)

            # Höhen und Flächen der einzelnen Oberflächen heraussuchen
            heights, areas = [], []
            for geom in roofGeom:
                ring = geom.GetGeometryRef(0)
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
                area = geom.GetArea()
                area3d = height * height + area
                areas.append(area3d)

            # Aus den vorhandenen Flächen die benötigten heraussuchen
            finalRoof = []
            for j in range(0, len(areas)):
                if areas[j] > 0.9 * max(areas) and round(heights[j], 2) >= round(max(heights) - 0.01, 2):
                    finalRoof.append(roofGeom[j])

            roofs.append([finalRoof, roofNames[i], [], ifcRoof])
            roofsOrig.append(roofGeom)

        return roofs, roofsOrig

    def calcWalls(self, ifcBuilding):
        """ Berechnet die Außenwände in Level of Detail (LoD) 3

        Args:
            ifcBuilding: Das Gebäude, aus dem die Wände entnommen werden sollen

        Returns:
            Die berechneten Wand-Geometrien, als Liste
        """
        walls, wallNames = [], []

        # IFC-Elemente der Wände
        ifcWalls = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcWall", result=[])
        if len(ifcWalls) == 0:
            self.parent.dlg.log(self.tr(u"Due to the missing walls, it will also be missing in CityGML"))
            return []

        # Heraussuchen der Außenwände
        ifcWallsExt = []
        ifcRelSpaceBoundaries = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcRelSpaceBoundary", result=[])
        for ifcWall in ifcWalls:
            extCount, intCount = 0, 0
            for ifcRelSpaceBoundary in ifcRelSpaceBoundaries:
                relElem = ifcRelSpaceBoundary.RelatedBuildingElement
                if relElem == ifcWall:
                    if ifcRelSpaceBoundary.InternalOrExternalBoundary == "EXTERNAL":
                        extCount += 1
                    elif ifcRelSpaceBoundary.InternalOrExternalBoundary == "INTERNAL":
                        intCount += 1
            if extCount > 0:
                ifcWallsExt.append(ifcWall)
            elif intCount == 0 and UtilitiesIfc.findPset(ifcWall, "Pset_WallCommon", "IsExternal"):
                ifcWallsExt.append(ifcWall)

        # Namen der Wände heraussuchen
        for ifcWall in ifcWallsExt:
            wallNames.append(ifcWall.Name)

        # Geometrie
        for i in range(0, len(ifcWallsExt)):
            ifcWall = ifcWallsExt[i]
            # noinspection PyUnresolvedReferences
            settings = ifcopenshell.geom.settings()
            settings.set(settings.USE_WORLD_COORDS, True)
            # noinspection PyUnresolvedReferences
            shape = ifcopenshell.geom.create_shape(settings, ifcWall)
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
                points = []
                for facePoint in facePoints:
                    point = self.trans.georeferencePoint(facePoint)
                    points.append(point)
                grVertsList.append(points)

            # Geometrien erstellen
            geometries = []
            for grVerts in grVertsList:
                # Polygon aus Ring aus Punkten erstellen
                geometry = ogr.Geometry(ogr.wkbPolygon)
                ring = ogr.Geometry(ogr.wkbLinearRing)
                for grVert in grVerts:
                    ring.AddPoint(grVert[0], grVert[1], grVert[2])
                ring.CloseRings()
                geometry.AddGeometry(ring)
                geometries.append(geometry)

            # Vereinigen, Vereinfachen und Hinzufügen
            wallGeom = UtilitiesGeom.union3D(geometries)
            wallGeom = UtilitiesGeom.simplify(wallGeom, 0.001, 0.001)
            walls.append([wallGeom, wallNames[i], [], ifcWall])
        return walls

    def calcOpenings(self, ifcBuilding, type):
        """ Berechnet die Öffnungen (Türen und Fenster) in Level of Detail (LoD) 3

        Args:
            ifcBuilding: Das Gebäude, aus dem die Öffnungen entnommen werden sollen
            type: Öffnungs-Typ (ifcDoor oder IfcWindow)

        Returns:
            Die berechneten Öffnungen mit Geometrie, Name, Typ und Ifc-Element, als Liste
        """
        openings, openingNames = [], []

        # IFC-Elemente der Öffnungen
        ifcOpenings = UtilitiesIfc.findElement(self.ifc, ifcBuilding, type, result=[])

        # Heraussuchen der Außenöffnungen
        ifcOpeningsExt = []
        ifcRelSpaceBoundaries = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcRelSpaceBoundary", result=[])
        psetCommon = "Pset_DoorCommon" if type == "ifcDoor" else "Pset_WindowCommon"
        for ifcOpening in ifcOpenings:
            ext = UtilitiesIfc.findPset(ifcOpening, psetCommon, "IsExternal")
            if ext is None:
                ext = False
                for ifcRelSpaceBoundary in ifcRelSpaceBoundaries:
                    relElem = ifcRelSpaceBoundary.RelatedBuildingElement
                    if relElem == ifcOpening and ifcRelSpaceBoundary.InternalOrExternalBoundary == "EXTERNAL":
                        ext = True
                if ext:
                    ifcOpeningsExt.append(ifcOpening)
            elif ext:
                ifcOpeningsExt.append(ifcOpening)

        # Namen der Öffnungen heraussuchen
        for ifcOpening in ifcOpeningsExt:
            openingNames.append(ifcOpening.Name)

        # Geometrie
        for i in range(0, len(ifcOpeningsExt)):
            ifcOpening = ifcOpeningsExt[i]
            # noinspection PyUnresolvedReferences
            settings = ifcopenshell.geom.settings()
            settings.set(settings.USE_WORLD_COORDS, True)
            # noinspection PyUnresolvedReferences
            shape = ifcopenshell.geom.create_shape(settings, ifcOpening)
            # Vertizes
            verts = shape.geometry.verts
            grVertsCurr = [[round(verts[i], 5), round(verts[i + 1], 5), round(verts[i + 2], 5)] for i in
                           range(0, len(verts), 3)]
            grVertsList = []
            minHeight, maxHeight = sys.maxsize, -sys.maxsize

            # Nur wichtige Vertizes hinzufügen
            for grVertCurr in grVertsCurr:
                point = self.trans.georeferencePoint(grVertCurr)
                if point[2] <= minHeight:
                    minHeight = point[2]
                    grVertsList.append(point)
                if point[2] >= maxHeight:
                    maxHeight = point[2]
                    grVertsList.append(point)
            openings.append([grVertsList, openingNames[i], type, ifcOpening])

        return openings

    @staticmethod
    def assignOpenings(openings, walls):
        """ Fügt die Öffnungen (Fenster & Türen) an die zugehörigen Wände in Level of Detail (LoD) 3 an

        Args:
            openings: Die anzufügenden Öffnungen (Fenster & Türen), als Liste
            walls: Die Wände, an die die Öffnungen angefügt werden sollen, als Liste

        Returns:
            Die angepassten Wände, als Liste
        """
        for opening in openings:
            ptOp = opening[0][0]

            # Wand bzw. Dach mit geringstem Abstand zur Öffnung berechnen
            minDist, minDistElem = sys.maxsize, None
            for wall in walls:
                for geom in wall[0]:
                    for i in range(0, geom.GetGeometryCount()):
                        ring = geom.GetGeometryRef(i)
                        for j in range(0, ring.GetPointCount()):
                            pt = ring.GetPoint(j)
                            dist = math.sqrt((ptOp[0] - pt[0]) ** 2 + (ptOp[1] - pt[1]) ** 2 + (ptOp[2] - pt[2]) ** 2)
                            if dist < minDist:
                                minDist, minDistElem = dist, wall

            # Öffnung hinzufügen
            if minDistElem is not None:
                minDistElem[2].append(opening)
        return walls

    @staticmethod
    def adjustWallOpenings(walls):
        """ Passt die Wände auf Grundlage der Dächer, Grundflächen und Öffnungen in Level of Detail (LoD) 3 an

        Args:
            walls: Die anzupassenden Wände, als Liste

        Returns:
            Die angepassten Wände, als Liste
            Die Anzahl an Hauptflächen pro Wand, als Liste
        """
        wallMainCounts = []
        for wall in walls:
            delBounds = []
            # Maximale Durchmesser der einzelnen Oberflächen heraussuchen
            dists = []
            for wallGeom in wall[0]:
                maxDist = -sys.maxsize
                ring = wallGeom.GetGeometryRef(0)
                heightDiff = False
                for k in range(0, ring.GetPointCount()):
                    pt1 = ring.GetPoint(k)
                    for m in range(k + 1, ring.GetPointCount()):
                        pt2 = ring.GetPoint(m)
                        if pt1[2] != pt2[2]:
                            heightDiff = True
                        dist = math.sqrt((pt2[0] - pt1[0]) ** 2 + (pt2[1] - pt1[1]) ** 2 + (pt2[2] - pt1[2]) ** 2)
                        if dist > maxDist:
                            maxDist = dist
                if heightDiff:
                    dists.append(maxDist)
                else:
                    dists.append(0)

            # Größte Fläche als Außenfläche
            lastMaxDist, bigDists = None, []
            for k in range(0, len(dists)):
                if dists[k] > 0.95 * max(dists):
                    lastMaxDist = k
                if dists[k] > 0.5 * max(dists):
                    bigDists.append(k)
            finalWall = [wall[0][lastMaxDist]]

            # Ggf. weitere Flächen, sofern diese in einer Ebene nur Hauptfläche sind
            mainGeomCount = 1
            if len(bigDists) > 2:
                maxGeom = wall[0][lastMaxDist].GetGeometryRef(0)
                planeMax = UtilitiesGeom.getPlane(maxGeom.GetPoint(0), maxGeom.GetPoint(1), maxGeom.GetPoint(2))
                pointMax = Point3D(maxGeom.GetPoint(0)[0], maxGeom.GetPoint(0)[1], maxGeom.GetPoint(0)[2])
                for bigDist in bigDists:
                    if bigDist != lastMaxDist:
                        newGeom = wall[0][bigDist].GetGeometryRef(0)
                        planeNew = UtilitiesGeom.getPlane(newGeom.GetPoint(0), newGeom.GetPoint(1), newGeom.GetPoint(2))
                        angle = float(planeMax.angle_between(planeNew))
                        if 0 <= angle < 0.01 or math.pi - 0.01 < angle < math.pi + 0.01 \
                                or 2 * math.pi - 0.01 < angle < 2 * math.pi + 0.01:
                            planeDist = float(planeNew.distance(pointMax))
                            if planeDist < 0.01:
                                finalWall.append(wall[0][bigDist])
                                mainGeomCount += 1
            wallMainCounts.append(mainGeomCount)

            # Wenn Öffnungen vorhanden sind: Entsprechende Begrenzungsflächen heraussuchen
            if len(wall[2]) != 0:
                # noinspection PyUnusedLocal
                openBounds = [[] for x in range(len(wall[2]))]
                for h in range(0, len(wall[0])):
                    wallGeom = wall[0][h]
                    if wallGeom in finalWall:
                        continue
                    same = False
                    wallRing = wallGeom.GetGeometryRef(0)

                    # Auf Nähe mit den Öffnungen (Türen und Fenster) prüfen
                    for i in range(0, len(wall[2])):
                        if same:
                            break
                        opening = wall[2][i]
                        near = False
                        maxDist = -sys.maxsize
                        for o in range(0, wallRing.GetPointCount()):
                            ptO = wallRing.GetPoint(o)
                            minDistBound = sys.maxsize
                            for p in range(0, len(opening[0])):
                                ptP = opening[0][p]
                                dist = math.sqrt(
                                    (ptP[0] - ptO[0]) ** 2 + (ptP[1] - ptO[1]) ** 2 + (ptP[2] - ptO[2]) ** 2)
                                if dist < 0.2:
                                    near = True
                                if dist < minDistBound:
                                    minDistBound = dist
                            if minDistBound > maxDist:
                                maxDist = minDistBound
                        if near and maxDist < 0.5:
                            # Hinzufügen
                            openBounds[i].append([len(finalWall), wallGeom])
                            finalWall.append(wallGeom)

                # Öffnungen durch eine gesamte Fläche darstellen
                # über alle Öffnungen der Wand iterieren
                for j in range(0, len(wall[2])):
                    opening = wall[2][j]
                    verts = opening[0]
                    sPts, lastHeight = [], None

                    # Schnittpunkte zwischen Öffnung und Wand herausfinden
                    startHor = False
                    for openBound in openBounds[j]:
                        sPtsBound = []
                        geom = openBound[1]
                        ring = geom.GetGeometryRef(0)
                        plane = UtilitiesGeom.getPlane(ring.GetPoint(0), ring.GetPoint(1), ring.GetPoint(2))
                        for vert in verts:
                            point = Point3D(vert[0], vert[1], vert[2])
                            s = plane.intersection(point)
                            if len(s) == 1:
                                sPtsBound.append(vert)
                        if len(sPtsBound) == 0:
                            continue

                        # Durchschnittskoordinaten
                        allX, allY = 0, 0
                        minHeight, maxHeight = sys.maxsize, -sys.maxsize
                        for sPtBound in sPtsBound:
                            allX += sPtBound[0]
                            allY += sPtBound[1]
                            if sPtBound[2] < minHeight:
                                minHeight = sPtBound[2]
                            if sPtBound[2] > maxHeight:
                                maxHeight = sPtBound[2]
                        if minHeight != maxHeight:
                            meanX = allX / len(sPtsBound)
                            meanY = allY / len(sPtsBound)

                            # Schnittpunkte geordnet sammeln
                            if lastHeight is None or lastHeight == minHeight:
                                sPts.append([meanX, meanY, minHeight])
                                sPts.append([meanX, meanY, maxHeight])
                                lastHeight = maxHeight
                            else:
                                sPts.append([meanX, meanY, maxHeight])
                                sPts.append([meanX, meanY, minHeight])
                                lastHeight = minHeight
                        elif openBounds[j].index(openBound) == 0:
                            lastHeight = minHeight
                            startHor = True

                    # Wenn kein Intersect mit den Begrenzungen stattfindet
                    if len(sPts) == 0:
                        # Naheliegendstes Wand-Loch finden
                        wallGeom = finalWall[0]
                        minDist, minHole = sys.maxsize, None
                        for k in range(1, wallGeom.GetGeometryCount()):
                            wallHole = wallGeom.GetGeometryRef(k)
                            vert = verts[0]
                            for m in range(0, wallHole.GetPointCount()):
                                wallHolePt = wallHole.GetPoint(m)
                                dist = math.sqrt((wallHolePt[0] - vert[0]) ** 2 + (wallHolePt[1] - vert[1]) ** 2 + (
                                        wallHolePt[2] - vert[2]) ** 2)
                                if dist < minDist:
                                    minDist = dist
                                    minHole = wallHole

                        # Neue Geometrie aus dem Loch erstellen
                        newGeomOpen = ogr.Geometry(ogr.wkbPolygon)
                        newGeomRing = ogr.Geometry(ogr.wkbLinearRing)
                        if minHole is not None:
                            for o in range(minHole.GetPointCount() - 1, 0, -1):
                                holePt = minHole.GetPoint(o)
                                newGeomRing.AddPoint(holePt[0], holePt[1], holePt[2])

                        # Wenn kein Loch vorhanden: Hauptgeometrie nutzen
                        else:
                            openPts = []
                            wallMainGeom = wallGeom.GetGeometryRef(0)
                            tol = 0.001
                            for k in range(0, wallMainGeom.GetPointCount()):
                                wallPt = wallMainGeom.GetPoint(k)
                                found = False
                                for openBound in openBounds[j]:
                                    openBoundRing = openBound[1].GetGeometryRef(0)
                                    for o in range(0, openBoundRing.GetPointCount()):
                                        boundPt = openBoundRing.GetPoint(o)
                                        if wallPt[0] - tol < boundPt[0] < wallPt[0] + tol and wallPt[1] - tol < \
                                                boundPt[1] < wallPt[1] + tol and wallPt[2] - tol < boundPt[2] < \
                                                wallPt[2] + tol:
                                            if wallPt not in openPts:
                                                openPts.append(wallPt)
                                                found = True
                                                break
                                    if found:
                                        break
                            for openPt in openPts:
                                newGeomRing.AddPoint(openPt[0], openPt[1], openPt[2])

                        # Geometrie abschließen
                        newGeomRing.CloseRings()
                        newGeomOpen.AddGeometry(newGeomRing)
                        opening[0] = [newGeomOpen]

                        # Begrenzungen entfernen
                        for openBound in openBounds[j]:
                            delBounds.append(openBound[0])

                    # Wenn die Begrenzungen geschnitten werden
                    else:
                        # Neue Geometrie aus den Schnittpunkten
                        newGeomOpen = ogr.Geometry(ogr.wkbPolygon)
                        newGeomRing = ogr.Geometry(ogr.wkbLinearRing)
                        for o in range(0, len(sPts)):
                            newGeomRing.AddPoint(sPts[o][0], sPts[o][1], sPts[o][2])
                        newGeomRing.CloseRings()
                        newGeomOpen.AddGeometry(newGeomRing)
                        opening[0] = [newGeomOpen]

                        # Schnittpunkte, nach Wandstück geordnet
                        newSPts, q = [], 1
                        if startHor:
                            newSPts.append([sPts[-1], sPts[0]])
                        while q < len(sPts):
                            newSPts.append([sPts[q - 1], sPts[q]])
                            q += 1
                        if not startHor:
                            newSPts.append([sPts[-1], sPts[0]])
                        sPts = newSPts

                        # Wandflächen kürzen
                        for q in range(0, len(openBounds[j])):
                            wallNr, geom = openBounds[j][q][0], openBounds[j][q][1]
                            ring = geom.GetGeometryRef(0)
                            newGeomWall1, newRingWall1 = ogr.Geometry(ogr.wkbPolygon), ogr.Geometry(ogr.wkbLinearRing)
                            newGeomWall2, newRingWall2 = ogr.Geometry(ogr.wkbPolygon), ogr.Geometry(ogr.wkbLinearRing)

                            swap = False
                            for r in range(0, ring.GetPointCount()):
                                ptSt = ring.GetPoint(r)
                                nr = 0 if r == ring.GetPointCount() - 1 else r + 1
                                ptEnd = ring.GetPoint(nr)
                                if swap:
                                    newRingWall2.AddPoint(ptSt[0], ptSt[1], ptSt[2])
                                else:
                                    newRingWall1.AddPoint(ptSt[0], ptSt[1], ptSt[2])
                                for s in range(0, len(sPts[q])):
                                    ptMid = sPts[q][s]

                                    # Auf Punkt-Gleichheit prüfen
                                    tol = 0.001
                                    if (ptSt[0] - tol < ptMid[0] < ptSt[0] + tol) and (
                                            ptSt[1] - tol < ptMid[1] < ptSt[1] + tol) and (
                                            ptSt[2] - tol < ptMid[2] < ptSt[2] + tol):
                                        if swap:
                                            newRingWall1.AddPoint(ptMid[0], ptMid[1], ptMid[2])
                                        else:
                                            newRingWall2.AddPoint(ptMid[0], ptMid[1], ptMid[2])
                                        swap = not swap
                                        break

                                    # Parallelität der Linien von Start- zu Mittelpunkt und Mittel- zu Endpunkt prüfen
                                    tol = 0.01
                                    # Y-Steigung in Bezug auf X-Verlauf
                                    gradYSt = -1 if abs(ptMid[0] - ptSt[0]) < 0.0001 else (ptMid[1] - ptSt[1]) / abs(
                                        ptMid[0] - ptSt[0])
                                    gradYEnd = -1 if abs(ptEnd[0] - ptMid[0]) < 0.0001 else (ptEnd[1] - ptMid[1]) / abs(
                                        ptEnd[0] - ptMid[0])
                                    if gradYSt - tol < gradYEnd < gradYSt + tol:
                                        # Z-Steigung in Bezug auf X-Verlauf
                                        gradZSt = -1 if abs(ptMid[0] - ptSt[0]) < 0.0001 else (ptMid[2] - ptSt[
                                            2]) / abs(
                                            ptMid[0] - ptSt[0])
                                        gradZEnd = -1 if abs(ptEnd[0] - ptMid[0]) < 0.0001 else (ptEnd[2] - ptMid[
                                            2]) / abs(
                                            ptEnd[0] - ptMid[0])
                                        if gradZSt - tol < gradZEnd < gradZSt + tol:
                                            # Z-Steigung in Bezug auf Y-Verlauf
                                            gradYZSt = -1 if abs(ptMid[1] - ptSt[1]) < 0.0001 else (ptMid[2] - ptSt[
                                                2]) / abs(ptMid[1] - ptSt[1])
                                            gradYZEnd = -1 if abs(ptEnd[1] - ptMid[1]) < 0.0001 else (ptEnd[2] - ptMid[
                                                2]) / abs(ptEnd[1] - ptMid[1])
                                            if gradYZSt - tol < gradYZEnd < gradYZSt + tol:
                                                newRingWall1.AddPoint(ptMid[0], ptMid[1], ptMid[2])
                                                newRingWall2.AddPoint(ptMid[0], ptMid[1], ptMid[2])
                                                swap = not swap
                                                break

                            # Geometrien abschließen
                            newRingWall1.CloseRings()
                            newGeomWall1.AddGeometry(newRingWall1)
                            newRingWall2.CloseRings()
                            newGeomWall2.AddGeometry(newRingWall2)

                            # Prüfen, welche Hälfte zu nutzen ist: Näher an Hauptwand
                            minDist1, minDist2 = sys.maxsize, sys.maxsize
                            ring = finalWall[0].GetGeometryRef(0)
                            for t in range(0, ring.GetPointCount()):
                                ptRef = ring.GetPoint(t)
                                for u in range(0, newRingWall1.GetPointCount()):
                                    ptNew = newRingWall1.GetPoint(u)
                                    dist = math.sqrt((ptRef[0] - ptNew[0]) ** 2 + (ptRef[1] - ptNew[1]) ** 2 + (
                                            ptRef[2] - ptNew[2]) ** 2)
                                    if dist < minDist1:
                                        minDist1 = dist
                                for u in range(0, newRingWall2.GetPointCount()):
                                    ptNew = newRingWall2.GetPoint(u)
                                    dist = math.sqrt((ptRef[0] - ptNew[0]) ** 2 + (ptRef[1] - ptNew[1]) ** 2 + (
                                            ptRef[2] - ptNew[2]) ** 2)
                                    if dist < minDist2:
                                        minDist2 = dist

                            finalWall[wallNr] = newGeomWall1 if minDist1 < minDist2 else newGeomWall2

            # Überflüssige OpenBounds entfernen
            delBounds.sort(reverse=True)
            for v in range(0, len(delBounds)):
                finalWall.pop(delBounds[v])
            wall[0] = finalWall
        return walls, wallMainCounts

    @staticmethod
    def adjustWallSize(walls, bases, roofs, basesOrig, roofsOrig, wallMainCounts):
        """ Passt die Wände in Bezug auf die veränderten Grundflächen und Dächer in Level of Detail (LoD) 3 an

        Args:
            walls: Die anzupassenden Wände, als Liste
            bases: Die Grundflächen, an die die Wände angepasst werden sollen, als Liste
            roofs: Die Dächer, an die die Wände angepasst werden sollen, als Liste
            basesOrig: Die originalen Grundflächen als Liste
            roofsOrig: Die originalen Dächer als Liste
            wallMainCounts: Die Anzahl an Hauptflächen pro Wand, als Liste

        Returns:
            Die angepassten Wände, als Liste
        """

        # Alle Wände durchgehen
        newWallGeom, newWallRing = ogr.Geometry(ogr.wkbPolygon), ogr.Geometry(ogr.wkbLinearRing)
        lastPt, height, lastHeight = [], None, None
        for i in range(0, len(walls)):
            for h in range(0, wallMainCounts[i]):
                wallGeom = walls[i][0][h]
                wallRing = wallGeom.GetGeometryRef(0)
                wallGeomTemp, wallRingTemp = ogr.Geometry(ogr.wkbPolygon), ogr.Geometry(ogr.wkbLinearRing)
                wallHoles, inHole, newWalls = [], False, []

                # Startpunkt heraussuchen: Ohne Schnitt mit Nebenwänden
                startPt = 0
                for j in range(0, wallRing.GetPointCount()):
                    pt = wallRing.GetPoint(j)
                    intOp = False
                    for m in range(wallMainCounts[i], len(walls[i][0])):
                        wallOpGeom = walls[i][0][m]
                        wallOpRing = wallOpGeom.GetGeometryRef(0)
                        for n in range(0, wallOpRing.GetPointCount()):
                            wallOpPt = wallOpRing.GetPoint(n)
                            if wallOpPt == pt:
                                intOp = True
                                break
                        if intOp:
                            break
                    if not intOp:
                        startPt = j + 1
                        break
                endPt = wallRing.GetPointCount()

                # Alle Eckpunkte der Wände durchgehen
                intBase = False
                iteration = 0
                lastFound = None
                while iteration < 2:
                    iteration += 1
                    for j in range(startPt, endPt):
                        pt = wallRing.GetPoint(j)

                        # HÖHE #
                        # Gebufferte Punktgeometrie
                        tol = 0.001
                        ptPolGeom, ptPolRing = ogr.Geometry(ogr.wkbPolygon), ogr.Geometry(ogr.wkbLinearRing)
                        ptPolRing.AddPoint(pt[0] - tol, pt[1] - tol, pt[2])
                        ptPolRing.AddPoint(pt[0] - tol, pt[1] + tol, pt[2])
                        ptPolRing.AddPoint(pt[0] + tol, pt[1] + tol, pt[2])
                        ptPolRing.AddPoint(pt[0] + tol, pt[1] - tol, pt[2])
                        ptPolRing.CloseRings()
                        ptPolGeom.AddGeometry(ptPolRing)

                        # Mit allen originalen Grundflächen und Dächern abgleichen
                        found = False
                        origs = basesOrig + roofsOrig
                        anzBases = len(basesOrig)
                        for k in range(0, len(origs)):
                            for m in range(0, len(origs[k])):
                                origGeom = origs[k][m]
                                origRing = origGeom.GetGeometryRef(0)
                                geom = roofs[k - anzBases][0][0] if k >= anzBases else bases[k][0][0]
                                ring = geom.GetGeometryRef(0)

                                # Prüfen, ob Wandpunkt gleich zu Punkt von Grundfläche/Dach
                                for n in range(0, origRing.GetPointCount()):
                                    if origRing.GetPoint(n) == pt:
                                        # Bestimmen der neuen Höhe des Wandpunkts
                                        height = ring.GetPoint(0)[2]
                                        found = True
                                        break

                                # Prüfen, ob Wandpunkt einen 2D-Schnitt mit Grundfläche/Dach bildet
                                if not found:
                                    intersect = origGeom.Intersection(ptPolGeom)
                                    if intersect is not None and not intersect.IsEmpty():
                                        # Prüfen, ob die Wandhöhe und Höhe der orig. Grundfläche/Dach etwa gleich ist
                                        origPlane = UtilitiesGeom.getPlane(origRing.GetPoint(0), origRing.GetPoint(1),
                                                                           origRing.GetPoint(2))
                                        ptLine = Line(Point3D(pt[0], pt[1], pt[2] - 100),
                                                      Point3D(pt[0], pt[1], pt[2] + 100))
                                        sRes = origPlane.intersection(ptLine)
                                        if len(sRes) != 0 and isinstance(sRes[0], sympy.geometry.point.Point3D):
                                            sZ = float(sRes[0][2])
                                            if sZ - 0.01 < pt[2] < sZ + 0.01:
                                                # Bestimmen der neuen Höhe des Wandpunkts
                                                plane = UtilitiesGeom.getPlane(ring.GetPoint(0), ring.GetPoint(1),
                                                                               ring.GetPoint(2))
                                                sPoint = plane.intersection(ptLine)[0]
                                                height = float(sPoint[2])
                                                found = True
                                                break
                            if found:
                                intBase = True
                                break

                        # ÖFFNUNGEN und GEOMETRIE #
                        # Über alle Nebenwände und dessen Eckpunkte gehen
                        opBound, pts, nextPt = False, [], []
                        for m in range(wallMainCounts[i], len(walls[i][0])):
                            wallOpGeom = walls[i][0][m]
                            wallOpRing = wallOpGeom.GetGeometryRef(0)
                            for n in range(0, wallOpRing.GetPointCount()):
                                wallOpPt = wallOpRing.GetPoint(n)
                                if wallOpPt == pt:
                                    if not inHole or (lastFound and len(wallHoles) != 0 and len(wallHoles[-1]) > 1):
                                        nextPt = wallOpRing.GetPoint(n + 1)
                                    else:
                                        lastN = wallOpRing.GetPointCount() - 2 if n == 0 else n - 1
                                        lastPt = wallOpRing.GetPoint(lastN)
                                    opBound = True
                                    break
                            if opBound:
                                break

                        # Wenn Wandpunkt gleich zu einem Nebenwandpunkt
                        if opBound:
                            # Bereits Teil der Öffnung: Punkt merken
                            if inHole:
                                if lastFound and len(wallHoles[-1]) > 1:
                                    # Opening abschließend
                                    ptLast = wallRing.GetPoint(j - 1)
                                    newWallRing.AddPoint(ptLast[0], ptLast[1], ptLast[2])
                                    newWallRing.AddPoint(lastPt[0], lastPt[1], lastPt[2])
                                    newWallRing.CloseRings()
                                    newWallGeom.AddGeometry(newWallRing)
                                    newWalls.append(newWallGeom)
                                    wallRingTemp.AddPoint(ptLast[0], ptLast[1], lastHeight)

                                    # Neues Opening
                                    newWallGeom = ogr.Geometry(ogr.wkbPolygon)
                                    newWallRing = ogr.Geometry(ogr.wkbLinearRing)
                                    newWallRing.AddPoint(nextPt[0], nextPt[1], nextPt[2])
                                    newWallRing.AddPoint(pt[0], pt[1], pt[2])
                                    wallHoles.append([pt])
                                    if not found:
                                        height = pt[2]
                                    wallRingTemp.AddPoint(pt[0], pt[1], height)
                                    lastHeight = height
                                else:
                                    wallHoles[-1].append(pt)
                            # Anfang einer Öffnung: Neue Nebenwand beginnen, Punkt merken und setzen
                            else:
                                inHole = True
                                newWallGeom = ogr.Geometry(ogr.wkbPolygon)
                                newWallRing = ogr.Geometry(ogr.wkbLinearRing)
                                newWallRing.AddPoint(nextPt[0], nextPt[1], nextPt[2])
                                newWallRing.AddPoint(pt[0], pt[1], pt[2])
                                wallHoles.append([pt])
                                if not found:
                                    height = pt[2]
                                wallRingTemp.AddPoint(pt[0], pt[1], height)
                                lastHeight = height

                        # Wenn Wandpunkt gleich zu keinem Nebenwandpunkt
                        else:
                            # Nach Öffnungsende: Neue Nebenwand schließen, letzten Punkt merken und setzen
                            if inHole:
                                inHole = False
                                ptLast = wallRing.GetPoint(j - 1)
                                newWallRing.AddPoint(ptLast[0], ptLast[1], ptLast[2])
                                newWallRing.AddPoint(lastPt[0], lastPt[1], lastPt[2])
                                newWallRing.CloseRings()
                                newWallGeom.AddGeometry(newWallRing)
                                newWalls.append(newWallGeom)
                                wallRingTemp.AddPoint(ptLast[0], ptLast[1], lastHeight)

                            # Punkt setzen
                            if not found:
                                height = pt[2]
                            wallRingTemp.AddPoint(pt[0], pt[1], height)

                        lastFound = found

                    endPt = startPt
                    startPt = 1

                if intBase:
                    # Geometrie abschließen
                    wallRingTemp.CloseRings()
                    wallGeomTemp.AddGeometry(wallRingTemp)

                    # Alte Löcher übernehmen
                    for j in range(1, wallGeom.GetGeometryCount()):
                        wallGeomTemp.AddGeometry(wallGeom.GetGeometryRef(j))

                    # Neue Löcher hinzufügen
                    for j in range(0, len(wallHoles)):
                        wallHole = ogr.Geometry(ogr.wkbLinearRing)
                        for k in range(0, len(wallHoles[j])):
                            wallHole.AddPoint(wallHoles[j][k][0], wallHoles[j][k][1], wallHoles[j][k][2])
                        wallHole.CloseRings()
                        wallGeomTemp.AddGeometry(wallHole)

                    walls[i][0][h] = UtilitiesGeom.simplify(wallGeomTemp, 0.01, 0.01)

                    # Neue Nebenwand hinzufügen
                    for newWall in newWalls:
                        walls[i][0].append(newWall)

        return walls

    def setElementGroup(self, chBldg, geometries, type, lod, name, openings):
        """ Setzt ein CityGML-Objekt, bestehend aus mehreren Geometrien

        Args:
            chBldg: XML-Element, an dem das Objekt angefügt werden soll
            geometries: Die Geometrien des Objekts, als Liste
            type: Der Typ des Objekts
            lod: Level of Detail (LoD)
            name: Name der Oberfläche
            openings: Öffnungen des Objektes

        Returns:
            Die Poly-IDs der Geometrien, als Liste
            Die GML-ID des Objekts
        """
        for geometry in geometries:
            self.geom.AddGeometry(geometry)
            self.bldgGeom.AddGeometry(geometry)

        # XML-Struktur
        chBldgBB = etree.SubElement(chBldg, QName(XmlNs.bldg, "boundedBy"))
        chBldgS = etree.SubElement(chBldgBB, QName(XmlNs.bldg, type))
        gmlIdMain = "GML_" + str(uuid.uuid4())
        chBldgS.set(QName(XmlNs.gml, "id"), gmlIdMain)

        # Name
        if name is not None:
            chBldgSName = etree.SubElement(chBldgS, QName(XmlNs.gml, "name"))
            chBldgSName.text = name

        # MultiSurface
        chBldgSurfSMS = etree.SubElement(chBldgS, QName(XmlNs.bldg, "lod" + str(lod) + "MultiSurface"))
        chBldgMS = etree.SubElement(chBldgSurfSMS, QName(XmlNs.gml, "MultiSurface"))
        chBldgSM = etree.SubElement(chBldgMS, QName(XmlNs.gml, "surfaceMember"))
        chBldgCS = etree.SubElement(chBldgSM, QName(XmlNs.gml, "CompositeSurface"))
        polyId = "PolyID" + str(uuid.uuid4())
        chBldgCS.set(QName(XmlNs.gml, "id"), polyId)
        polyIds = [polyId]

        # Geometrie
        for geometry in geometries:
            chBldgCSSM = etree.SubElement(chBldgCS, QName(XmlNs.gml, "surfaceMember"))
            geomXML = UtilitiesGeom.geomToGml(geometry)
            chBldgCSSM.append(geomXML)

            # GML-ID
            chBldgPol = chBldgCSSM[0]
            gmlIdPoly = "PolyID" + str(uuid.uuid4())
            chBldgPol.set(QName(XmlNs.gml, "id"), gmlIdPoly)

        # Öffnungen
        openSurf = []
        for opening in openings:
            chBldgSurfSO = etree.SubElement(chBldgS, QName(XmlNs.bldg, "opening"))
            name = "Door" if opening[2] == "ifcDoor" else "Window"
            chBldgSurfSOE = etree.SubElement(chBldgSurfSO, QName(XmlNs.bldg, name))
            gmlId = "GML_" + str(uuid.uuid4())
            chBldgSurfSOE.set(QName(XmlNs.gml, "id"), gmlId)
            if opening[1] is not None:
                chBldgSurfSOName = etree.SubElement(chBldgSurfSOE, QName(XmlNs.gml, "name"))
                chBldgSurfSOName.text = opening[1]
            chBldgSurfSOMS = etree.SubElement(chBldgSurfSOE, QName(XmlNs.bldg, "lod" + str(lod) + "MultiSurface"))
            chBldgOMS = etree.SubElement(chBldgSurfSOMS, QName(XmlNs.gml, "MultiSurface"))
            chBldgOSM = etree.SubElement(chBldgOMS, QName(XmlNs.gml, "surfaceMember"))
            chBldgOCS = etree.SubElement(chBldgOSM, QName(XmlNs.gml, "CompositeSurface"))
            polyId = "GML_" + str(uuid.uuid4())
            chBldgOCS.set(QName(XmlNs.gml, "id"), polyId)
            polyIds.append(polyId)
            for geometry in opening[0]:
                chBldgOCSSM = etree.SubElement(chBldgOCS, QName(XmlNs.gml, "surfaceMember"))
                geomXML = UtilitiesGeom.geomToGml(geometry)
                chBldgOCSSM.append(geomXML)

                # GML-ID
                chBldgPol = chBldgOCSSM[0]
                gmlIdPoly = "PolyID" + str(uuid.uuid4())
                chBldgPol.set(QName(XmlNs.gml, "id"), gmlIdPoly)

            openSurf.append([gmlId, opening[3]])

        return polyIds, gmlIdMain, openSurf
