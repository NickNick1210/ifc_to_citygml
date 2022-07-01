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
from datetime import datetime
import re

# IFC-Bibliotheken
import ifcopenshell
import ifcopenshell.util.pset
from ifcopenshell.util import element

# XML-Bibliotheken
from lxml import etree
# noinspection PyUnresolvedReferences
from lxml.etree import QName

# QGIS-Bibliotheken
from osgeo import ogr
import processing

# Plugin
from qgis.core import QgsTask

from .xmlns import XmlNs
from .mapper import Mapper
from .transformer import Transformer
from .utilities import Utilities


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
        self.inPath = inPath
        self.outPath = outPath
        self.lod = lod
        self.eade = eade
        self.integr = integr
        self.ifc = None
        self.trans = None
        self.geom = ogr.Geometry(ogr.wkbGeometryCollection)

    def run(self):
        """ Ausführen der Konvertierung """
        # Initialisieren von IFC und CityGML
        self.ifc = self.readIfc(self.inPath)
        root = self.createSchema()

        # Initialisieren vom Transformer
        self.trans = Transformer(self.ifc)

        # Eigentliche Konvertierung: Unterscheidung nach den LoD
        if self.lod == 0:
            root = self.convertLoD0(root, self.eade)
        elif self.lod == 1:
            # TODO LoD1
            pass
        elif self.lod == 2:
            # TODO LoD2
            pass
        elif self.lod == 3:
            # TODO LoD3
            pass
        elif self.lod == 4:
            # TODO LoD4
            pass

        # Schreiben der CityGML in eine Datei
        self.writeCGML(root)

        # Integration der CityGML in QGIS
        if self.integr:
            # TODO QGIS-Integration
            pass

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
                                    'xlink': XmlNs.xlink, 'xsi': XmlNs.xsi})

    def writeCGML(self, root):
        """ Schreiben der XML-Struktur in eine GML-Datei

        Args:
            root: XML-Element
        """
        etree.ElementTree(root).write(self.outPath, xml_declaration=True, encoding="UTF-8", pretty_print=True)

    def finished(self, result):
        self.parent.completed(result)

    def convertLoD0(self, root, eade):
        """ Konvertieren von IFC zu CityGML im Level of Detail (LoD) 0

        Args:
            root: Das vorbereitete XML-Schema
            eade: Ob die EnergyADE gewählt wurde als Boolean
        """
        # IFC-Grundelemente
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
            self.convertBldgAttr(ifcBuilding, chBldg)
            self.convertFootPrint(ifcBuilding, chBldg)
            self.convertRoofEdge(ifcBuilding, chBldg)
            self.convertAddress(ifcBuilding, ifcSite, chBldg)
            self.convertBound(self.geom, chBound)

            # EnergyADE
            if eade:
                # TODO: EnergyADE
                pass

        return root

    def convertBound(self, geometry, chBound):
        # XML-Struktur
        chBoundEnv = etree.SubElement(chBound, QName(XmlNs.gml, "Envelope"))
        chBoundEnv.set("srsDimension", "3")
        chBoundEnv.set("srsName", "EPSG:" + str(self.trans.epsg))
        chBoundEnvLC = etree.SubElement(chBoundEnv, QName(XmlNs.gml, "lowerCorner"))
        chBoundEnvLC.set("srsDimension", "3")
        chBoundEnvUC = etree.SubElement(chBoundEnv, QName(XmlNs.gml, "upperCorner"))
        chBoundEnvUC.set("srsDimension", "3")

        # Envelope-Berechnung
        env = self.geom.GetEnvelope3D()
        chBoundEnvLC.text = str(env[0]) + " " + str(env[2]) + " " + str(env[4])
        chBoundEnvUC.text = str(env[1]) + " " + str(env[3]) + " " + str(env[5])

    def convertBldgAttr(self, ifcBuilding, chBldg):
        # Allgemeines
        chBldg.set("id", "UUID_" + str(uuid.uuid4()))
        if ifcBuilding.Name is not None:
            chBldgName = etree.SubElement(chBldg, QName(XmlNs.gml, "name"))
            chBldgName.text = ifcBuilding.Name
        if ifcBuilding.Description is not None:
            chBldgDescr = etree.SubElement(chBldg, QName(XmlNs.gml, "description"))
            chBldgDescr.text = ifcBuilding.Description
        chBldgCrDate = etree.SubElement(chBldg, QName(XmlNs.core, "creationDate"))
        chBldgCrDate.text = datetime.now().strftime("%Y-%m-%d")

        # Typ & Funktion
        if Utilities.findPset(self.ifc, ifcBuilding, "Pset_BuildingCommon", "OccupancyType") is not None:
            occType = element.get_psets(ifcBuilding)["Pset_BuildingCommon"]["OccupancyType"].lower()
            if any(char.isdigit() for char in occType):
                number = ""
                for char in occType:
                    if char.isdigit():
                        number += char
                    elif len(number) != 4:
                        number = ""
                numberNr = int(number)
                if 2700 >= numberNr >= 1000 and numberNr % 10 == 0:
                    type = number
            elif occType in Mapper.functionUsageDict:
                type = Mapper.functionUsageDict[occType]
            else:
                occType = occType.replace("_", " ").replace("-", " ").replace(",", " ").replace(";", " ")
                for occTypeSub in occType.split():
                    if occTypeSub in Mapper.functionUsageDict:
                        type = Mapper.functionUsageDict[occTypeSub]

            if type is None:
                if ifcBuilding.ObjectType is not None:
                    objType = ifcBuilding.ObjectType.lower()
                    if any(char.isdigit() for char in objType):
                        number = ""
                        for char in objType:
                            if char.isdigit():
                                number += char
                            elif len(number) != 4:
                                number = ""
                        numberNr = int(number)
                        if 2700 >= numberNr >= 1000 and numberNr % 10 == 0:
                            type = number
                    elif objType in Mapper.functionUsageDict:
                        type = Mapper.functionUsageDict[objType]
                    else:
                        objType = objType.replace("_", " ").replace("-", " ").replace(",", " ").replace(";", " ")
                        for objTypeSub in objType.split():
                            if objTypeSub in Mapper.functionUsageDict:
                                type = Mapper.functionUsageDict[objTypeSub]

            if type is not None:
                # XML-Struktur + Eintragen
                chBldgClass = etree.SubElement(chBldg, QName(XmlNs.bldg, "class"))
                chBldgClass.set("codeSpace",
                                "http://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_class.xml")
                chBldgClass.text = str(Mapper.classFunctionUsage[int(type)])
                chBldgFunc = etree.SubElement(chBldg, QName(XmlNs.bldg, "function"))
                chBldgFunc.set("codeSpace",
                               "http://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_function.xml")
                chBldgFunc.text = str(type)
                chBldgUsage = etree.SubElement(chBldg, QName(XmlNs.bldg, "usage"))
                chBldgUsage.set("codeSpace",
                                "http://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_usage.xml")
                chBldgUsage.text = str(type)

        # Eigenschaften
        if Utilities.findPset(self.ifc, ifcBuilding, "Pset_BuildingCommon", "YearOfConstruction") is not None:
            chBldgYearConstr = etree.SubElement(chBldg, QName(XmlNs.bldg, "yearOfConstruction"))
            chBldgYearConstr.text = element.get_psets(ifcBuilding)["Pset_BuildingCommon"]["YearOfConstruction"]
        ifcRoofs = Utilities.findElement(self.ifc, ifcBuilding, "IfcRoof", result=[])
        roofTypes = []
        if ifcRoofs is not None:
            for ifcRoof in ifcRoofs:
                if ifcRoof.PredefinedType is not None and ifcRoof.PredefinedType != "NOTDEFINED":
                    roofTypes.append(ifcRoof.PredefinedType)
        if len(roofTypes) > 0:
            roofType = max(set(roofTypes), key=roofTypes.count)
            chBldgRoofType = etree.SubElement(chBldg, QName(XmlNs.bldg, "roofType"))
            chBldgRoofType.set("codeSpace",
                               "http://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_roofType.xml")
            chBldgRoofType.text = str(Mapper.roofTypeDict[roofType])

        # Höhen und Geschosse
        ifcBldgStoreys = Utilities.findElement(self.ifc, ifcBuilding, "IfcBuildingStorey", result=[])
        storeysAG, storeysBG = 0, 0
        storeysHeightsAG, storeysHeightsBG = 0, 0
        missingAG, missingBG = 0, 0
        # über alle Geschosse iterieren
        for ifcBldgStorey in ifcBldgStoreys:
            # Herausfinden, ob über oder unter Grund
            if Utilities.findPset(self.ifc, ifcBldgStorey, "Pset_BuildingStoreyCommon") is not None and \
                    element.get_psets(ifcBldgStorey)["Pset_BuildingStoreyCommon"]["AboveGround"] is not None:
                ag = element.get_psets(ifcBldgStorey)["Pset_BuildingStoreyCommon"]["AboveGround"]
            elif ifcBldgStorey.Elevation is not None:
                ag = True if ifcBldgStorey.Elevation >= -1 else False
            else:
                ag = True
            if ag:
                storeysAG += 1
            else:
                storeysBG += 1

            # Herausfinden der Geschosshöhe
            height = 0
            if Utilities.findPset(self.ifc, ifcBldgStorey, "BaseQuantities", "GrossHeight") is not None:
                height = element.get_psets(ifcBldgStorey)["BaseQuantities"]["GrossHeight"]
            elif Utilities.findPset(self.ifc, ifcBldgStorey, "Qto_BuildingStoreyBaseQuantities", "GrossHeight") is not None:
                height = element.get_psets(ifcBldgStorey)["Qto_BuildingStoreyBaseQuantities"]["GrossHeight"]
            elif Utilities.findPset(self.ifc, ifcBldgStorey, "BaseQuantities", "Height") is not None:
                height = element.get_psets(ifcBldgStorey)["BaseQuantities"]["Height"]
            elif Utilities.findPset(self.ifc, ifcBldgStorey, "Qto_BuildingStoreyBaseQuantities", "Height") is not None:
                height = element.get_psets(ifcBldgStorey)["Qto_BuildingStoreyBaseQuantities"]["Height"]
            elif Utilities.findPset(self.ifc, ifcBldgStorey, "BaseQuantities", "NetHeight") is not None:
                height = element.get_psets(ifcBldgStorey)["BaseQuantities"]["NetHeight"]
            elif Utilities.findPset(self.ifc, ifcBldgStorey, "Qto_BuildingStoreyBaseQuantities", "NetHeight") is not None:
                height = element.get_psets(ifcBldgStorey)["Qto_BuildingStoreyBaseQuantities"]["NetHeight"]
            else:
                if ag:
                    missingAG += 1
                else:
                    missingBG += 1
            if ag:
                storeysHeightsAG += height
            else:
                storeysHeightsBG += height

        # Relative
        chBldgRelTerr = etree.SubElement(chBldg, QName(XmlNs.core, "relativeToTerrain"))
        if missingBG == 0:
            chBldgRelTerr.text = "entirelyAboveTerrain"
        elif missingAG == 0:
            chBldgRelTerr.text = "entirelyBelowTerrain"
        elif missingAG == missingBG:
            chBldgRelTerr.text = "substaintiallyAboveAndBelowTerrain"
        elif missingAG > missingBG:
            chBldgRelTerr.text = "substaintiallyAboveTerrain"
        else:
            chBldgRelTerr.text = "substaintiallyBelowTerrain"

        # Gebäudehöhe
        if Utilities.findPset(self.ifc, ifcBuilding, "BaseQuantities", "GrossHeight") is not None:
            height = element.get_psets(ifcBuilding)["BaseQuantities"]["GrossHeight"]
        elif Utilities.findPset(self.ifc, ifcBuilding, "Qto_BuildingBaseQuantities", "GrossHeight") is not None:
            height = element.get_psets(ifcBuilding)["Qto_BuildingBaseQuantities"]["GrossHeight"]
        elif Utilities.findPset(self.ifc, ifcBuilding, "BaseQuantities", "Height") is not None:
            height = element.get_psets(ifcBuilding)["BaseQuantities"]["Height"]
        elif Utilities.findPset(self.ifc, ifcBuilding, "Qto_BuildingBaseQuantities", "Height") is not None:
            height = element.get_psets(ifcBuilding)["Qto_BuildingBaseQuantities"]["Height"]
        elif Utilities.findPset(self.ifc, ifcBuilding, "BaseQuantities", "NetHeight") is not None:
            height = element.get_psets(ifcBuilding)["BaseQuantities"]["NetHeight"]
        elif Utilities.findPset(self.ifc, ifcBuilding, "Qto_BuildingBaseQuantities", "NetHeight") is not None:
            height = element.get_psets(ifcBuilding)["Qto_BuildingBaseQuantities"]["NetHeight"]
        else:
            if missingAG > 0 or missingBG > 0:
                height = (storeysHeightsAG + missingAG*(storeysHeightsAG/storeysAG) + storeysHeightsBG + missingBG*(storeysHeightsBG/storeysBG))
            else:
                height = storeysHeightsAG + storeysHeightsBG
        if height != 0:
            chBldgHeight = etree.SubElement(chBldg, QName(XmlNs.bldg, "measuredHeight"))
            chBldgHeight.set("uom", "m")
            chBldgHeight.text = str(height)

        # Geschossangaben
        chBldgStoreysAG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysAboveGround"))
        chBldgStoreysAG.text = str(storeysAG)
        chBldgStoreysBG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysBelowGround"))
        chBldgStoreysBG.text = str(storeysBG)
        if (storeysAG-missingAG) > 0:
            chBldgStoreysHeightAG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysHeightsAboveGround"))
            chBldgStoreysHeightAG.text = str(storeysHeightsAG/(storeysAG-missingAG))
        if (storeysBG-missingBG) > 0:
            chBldgStoreysHeightBG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysHeightsBelowGround"))
            chBldgStoreysHeightBG.text = str(storeysHeightsBG/(storeysBG-missingBG))

    def convertFootPrint(self, ifcBuilding, chBldg):
        """ Konvertieren der Grundfläche von IFC zu CityGML

        Args:
            ifcBuilding: Das Gebäude, aus dem die Grundfläche entnommen werden soll
            chBldg: XML-Element an dem die Grundfläche angefügt werden soll
        """

        ifcSlabs = Utilities.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="BASESLAB")
        if len(ifcSlabs) == 0:
            ifcSlabs = Utilities.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="FLOOR")
            if len(ifcSlabs) == 0:
                self.parent.dlg.log(u"Due to the missing baseslab, no FootPrint geometry can to be calculated")
                return

        # Geometrie
        geomXML = self.calcPlane(ifcSlabs, True)
        if geomXML is not None:
            # XML-Struktur
            chBldgFootPrint = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod0FootPrint"))
            chBldgFootPrintMS = etree.SubElement(chBldgFootPrint, QName(XmlNs.gml, "MultiSurface"))
            chBldgFootPrintSM = etree.SubElement(chBldgFootPrintMS, QName(XmlNs.gml, "surfaceMember"))
            chBldgFootPrintSM.append(geomXML)

    def convertRoofEdge(self, ifcBuilding, chBldg):
        """ Konvertieren der Dachkantenfläche von IFC zu CityGML

        Args:
            ifcBuilding: Das Gebäude, aus dem die Dachkantenfläche entnommen werden soll
            chBldg: XML-Element an dem die Dachkantenfläche angefügt werden soll
        """

        ifcSlabs = Utilities.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="ROOF")
        if len(ifcSlabs) == 0:
            self.parent.dlg.log(u"Due to the missing roof, no RoofEdge geometry can to be calculated")
            return

        # Geometrie
        ifcSlabs = Utilities.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="ROOF")
        geomXML = self.calcPlane(ifcSlabs, False)
        if geomXML is not None:
            # XML-Struktur
            chBldgRoofEdge = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod0RoofEdge"))
            chBldgRoofEdgeMS = etree.SubElement(chBldgRoofEdge, QName(XmlNs.gml, "MultiSurface"))
            chBldgRoofEdgeSM = etree.SubElement(chBldgRoofEdgeMS, QName(XmlNs.gml, "surfaceMember"))
            chBldgRoofEdgeSM.append(geomXML)

    def calcPlane(self, ifcElements, mode):
        """ Berechnung einer planen Flächengeometrie

        Args:
            ifcElements: Elemente, aus denen die Fläche berechnet werden soll
            mode: Ob die höchste oder geringste Höhe zählt als Boolean

        Returns:
            chBldg: Erzeugte GML-Geometrie
        """
        # Vertizes aus den Elementen entnehmen und transformieren/georeferenzieren
        grVertsList = []
        for ifcElement in ifcElements:
            settings = ifcopenshell.geom.settings()
            shape = ifcopenshell.geom.create_shape(settings, ifcElement)
            verts = shape.geometry.verts
            grVertsCurr = [[verts[i], verts[i + 1], verts[i + 2]] for i in range(0, len(verts), 3)]
            points = self.trans.placePoints(ifcElement, grVertsCurr)
            grVertsList.append(points)

        # Höhe berechnen
        height = sys.maxsize
        for grVerts in grVertsList:
            for grVert in grVerts:
                if grVert[2] < height:
                    height = grVert[2]

        # Ring aus Punkten erstellen

        geometries = ogr.Geometry(ogr.wkbMultiPolygon)
        for grVerts in grVertsList:
            grVertsCheck = []
            geometry = ogr.Geometry(ogr.wkbPolygon)
            ring = ogr.Geometry(ogr.wkbLinearRing)
            for grVert in grVerts:
                grVert[2] = height
                if grVert not in grVertsCheck:
                    grVertsCheck.append(grVert)
                    ring.AddPoint(grVert[0], grVert[1], grVert[2])
            ring.AddPoint(grVerts[0][0], grVerts[0][1], height)

            geometry.AddGeometry(ring)
            if not geometry.IsValid():
                geomValid = geometry.MakeValid()
                if geomValid is not None:
                    geometry = geomValid
                geomNorm = geometry.Normalize()
                if geomNorm is not None:
                    geometry = geomNorm

            geometries.AddGeometry(geometry)

        if len(grVertsList) != 1:
            geometry = geometries.UnionCascaded()
            if geometry.GetGeometryCount() > 1:
                geometriesBuffer = ogr.Geometry(ogr.wkbMultiPolygon)
                for i in range(0, geometry.GetGeometryCount()):
                    g = geometry.GetGeometryRef(i)
                    geometriesBuffer.AddGeometry(g.Buffer(0.1, quadsecs=2))
                geometry = geometriesBuffer.UnionCascaded()

                if geometry.GetGeometryCount() > 1:
                    self.parent.dlg.log(
                        u'Can\'t calculate lod0 geometry due to the lack of topology or non-meter-metrics')
                    return None
                else:
                    geometry.Set3D(True)
                    wkt = geometry.ExportToWkt()
                    geometry = ogr.CreateGeometryFromWkt(wkt)
                    geometry = geometry.UnionCascaded()

        self.geom.AddGeometry(geometry)
        geomXML = Utilities.geomToGml(geometry)
        return geomXML

    def convertAddress(self, ifcBuilding, ifcSite, chBldg):
        """ Konvertieren der Adresse von IFC zu CityGML

        Args:
            ifcBuilding: Das Gebäude, aus dem die Adresse entnommen werden soll
            ifcSite: Das Grundstück, auf dem das Gebäude steht
            chBldg: XML-Element an dem die Adresse angefügt werden soll
        """
        # Prüfen, wo Addresse vorhanden
        if ifcBuilding.BuildingAddress is not None:
            ifcAddress = ifcBuilding.BuildingAddress
        elif Utilities.findPset(self.ifc, ifcBuilding, "Pset_Address") is not None:
            ifcAddress = Utilities.findPset(self.ifc, ifcBuilding, "Pset_Address")
        elif ifcSite.SiteAddress is not None:
            ifcAddress = ifcSite.SiteAddress
        elif Utilities.findPset(self.ifc, ifcSite, "Pset_Address") is not None:
            ifcAddress = Utilities.findPset(self.ifc, ifcSite, "Pset_Address")
        else:
            self.parent.dlg.log(u'No address details existing')
            return

        # XML-Struktur
        chBldgAdr = etree.SubElement(chBldg, QName(XmlNs.bldg, "address"))
        chBldgAdrObj = etree.SubElement(chBldgAdr, QName(XmlNs.core, "Address"))
        chBldgAdrXal = etree.SubElement(chBldgAdrObj, QName(XmlNs.core, "xalAddress"))
        chBldgAdrDetails = etree.SubElement(chBldgAdrXal, QName(XmlNs.xAL, "AddressDetails"))
        chBldgAdrLoc = etree.SubElement(chBldgAdrDetails, QName(XmlNs.xAL, "Locality"))
        chBldgAdrLoc.set("Type", "Town")

        # Eintragen der Adresse
        if ifcAddress.Town is not None:
            chBldgAdrLocName = etree.SubElement(chBldgAdrLoc, QName(XmlNs.xAL, "LocalityName"))
            chBldgAdrLocName.text = ifcAddress.Town

        if ifcAddress.AddressLines is not None:
            chBldgAdrLocTh = etree.SubElement(chBldgAdrLoc, QName(XmlNs.xAL, "Thoroughfare"))
            chBldgAdrLocTh.set("Type", "Street")
            chBldgAdrLocThNr = etree.SubElement(chBldgAdrLocTh, QName(XmlNs.xAL, "ThoroughfareNumber"))
            chBldgAdrLocThName = etree.SubElement(chBldgAdrLocTh, QName(XmlNs.xAL, "ThoroughfareName"))

            address = ifcAddress.AddressLines[0]
            if address[0].isdigit():
                sep = address.find(" ")
                street = address[sep + 1:]
                nr = address[0:sep]
            elif address[len(address) - 1].isdigit():
                sep = address.rfind(" ")
                street = address[0:sep]
                nr = address[sep + 1:]
            else:
                street = address
                nr = ""
            chBldgAdrLocThName.text = street
            chBldgAdrLocThNr.text = nr

        if ifcAddress.PostalCode is not None:
            chBldgAdrLocPC = etree.SubElement(chBldgAdrLoc, QName(XmlNs.xAL, "PostalCode"))
            chBldgAdrLocPCNr = etree.SubElement(chBldgAdrLocPC, QName(XmlNs.xAL, "PostalCodeNumber"))
            chBldgAdrLocPCNr.text = ifcAddress.PostalCode
