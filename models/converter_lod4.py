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
import sys
import uuid
from copy import deepcopy

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
from .converter_lod3 import LoD3Converter


#####


class LoD4Converter:
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
        return QCoreApplication.translate('LoD4Converter', msg)

    def convert(self, root, eade):
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
            GenConverter.convertLoDSolid(chBldg, links, 4)
            self.parent.dlg.log(self.tr(u'Rooms are calculated'))
            self.convertInterior(ifcBuilding, chBldg)
            self.parent.dlg.log(self.tr(u'Building address is extracted'))
            GenConverter.convertAddress(ifcBuilding, ifcSite, chBldg)
            self.parent.dlg.log(self.tr(u'Building bound is calculated'))
            bbox = GenConverter.convertBound(self.geom, chBound, self.trans)

            # EnergyADE
            if eade:
                self.parent.dlg.log(self.tr(u'Energy ADE is calculated'))
                self.parent.dlg.log(self.tr(u'Energy ADE: weather data is extracted'))
                EADEConverter.convertWeatherData(ifcProject, ifcSite, chBldg, bbox)
                self.parent.dlg.log(self.tr(u'Energy ADE: building attributes are extracted'))
                EADEConverter.convertBldgAttr(self.ifc, ifcBuilding, chBldg, bbox, footPrint)
                self.parent.dlg.log(self.tr(u'Energy ADE: thermal zone is calculated'))
                linkUZ, chBldgTZ, constructions = EADEConverter.calcThermalZone(self.ifc, ifcBuilding, chBldg, root,
                                                                                surfaces, 4)
                self.parent.dlg.log(self.tr(u'Energy ADE: usage zone is calculated'))
                EADEConverter.calcUsageZone(self.ifc, ifcProject, ifcBuilding, chBldg, linkUZ, chBldgTZ)
                self.parent.dlg.log(self.tr(u'Energy ADE: construction is calculated'))
                materials = EADEConverter.convertConstructions(root, constructions)
                self.parent.dlg.log(self.tr(u'Energy ADE: material is calculated'))
                EADEConverter.convertMaterials(root, materials)

        return root

    def convertBldgBound(self, ifcBuilding, chBldg):
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
        walls = LoD3Converter.assignOpenings(openings, walls)
        self.parent.dlg.log(self.tr(u'Building geometry: wall and opening surfaces are adjusted to each other'))
        walls, wallMainCounts = LoD3Converter.adjustWallOpenings(walls)
        self.parent.dlg.log(self.tr(u'Building geometry: wall surfaces are adjusted in their height'))
        walls = LoD3Converter.adjustWallSize(walls, floors, roofs, basesOrig, roofsOrig, wallMainCounts)

        # Geometrie
        links, surfaces = [], []
        for base in bases:
            linksBase, gmlId, openSurf = self.setElementGroup(chBldg, base[0], "GroundSurface", 4, base[1], base[2])
            links += linksBase
            surfaces.append([gmlId, base[3]])
            surfaces += openSurf
        for roof in roofs:
            linksRoof, gmlId, openSurf = self.setElementGroup(chBldg, roof[0], "RoofSurface", 4, roof[1], roof[2])
            links += linksRoof
            surfaces.append([gmlId, roof[3]])
            surfaces += openSurf
        for wall in walls:
            linksWall, gmlId, openSurf = self.setElementGroup(chBldg, wall[0], "WallSurface", 4, wall[1], wall[2])
            links += linksWall
            surfaces.append([gmlId, wall[3]])
            surfaces += openSurf
        return links, bases[0][0][0], surfaces

    def setElementGroup(self, chBldg, geometries, type, lod, name, openings):
        """ Setzen eines CityGML-Objekts, bestehend aus mehreren Geometrien

        Args:
            chBldg: XML-Element an dem das Objekt angefügt werden soll
            geometries: Die Geometrien des Objekts
            type: Der Typ des Objekts
            lod: Level of Detail (LoD)
            name: Name der Oberfläche
            openings: Öffnungen des Objektes

        Returns:
            Die Poly-IDs der Geometrien
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

    def calcBases(self, ifcBuilding):
        """ Berechnen der Grundfläche in Level of Detail (LoD) 3

        Args:
            ifcBuilding: Das Gebäude, aus dem die Grundflächen entnommen werden sollen

        Returns:
            Die berechneten Grundflächen-Geometrien als Liste
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
        """ Berechnen der Dächer in Level of Detail (LoD) 3

        Args:
            ifcBuilding: Das Gebäude, aus dem die Dächer entnommen werden sollen

        Returns:
            Die berechneten Dächer als Liste
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
        """ Berechnen der Außenwände in Level of Detail (LoD) 3

        Args:
            ifcBuilding: Das Gebäude, aus dem die Wände entnommen werden sollen

        Returns:
            Die berechneten Wand-Geometrien als Liste
        """
        walls = []
        wallNames = []

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

        # ifcWallsExt = ifcWallsExt[0:3]
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
        """ Berechnen der Öffnungen (Türen und Fenster) in Level of Detail (LoD) 3

        Args:
            ifcBuilding: Das Gebäude, aus dem die Öffnungen entnommen werden sollen
            type: Öffnungs-Typ (ifcDoor oder IfcWindow)

        Returns:
            Die berechneten Öffnungen mit Geometrie, Name, Typ und Ifc-Element als Liste
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

    def convertInterior(self, ifcBuilding, chBldg):
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

            links = self.convertRoomBound(ifcSpace, chRoom)
            GenConverter.convertLoDSolid(chRoom, links, 4)
            self.convertFurniture(ifcSpace, chRoom)
            self.convertInstallation(ifcSpace, chRoom)

    # noinspection PyUnusedLocal
    @staticmethod
    def convertRoomBound(ifcSpace, chRoom):
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

    @staticmethod
    def convertFurniture(ifcSpace, chRoom):
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

    @staticmethod
    def convertInstallation(ifcSpace, chRoom):
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
