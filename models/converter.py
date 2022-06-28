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
import numpy as np
from datetime import datetime

# IFC-Bibliotheken
import ifcopenshell
from ifcopenshell import geom
from ifcopenshell import util
import ifcopenshell.util.pset

# XML-Bibliotheken
from lxml import etree
# noinspection PyUnresolvedReferences
from lxml.etree import QName

# QGIS-Bibliotheken
import osgeo.osr as osr
from osgeo import ogr

# Plugin
from .xmlns import XmlNs
from .transformer import Transformer


class Converter:
    """ Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien """

    def __init__(self, parent, inPath, outPath):
        """ Konstruktor der Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien

        Args:
            parent: Die zugrunde liegende zentrale Model-Klasse
            inPath: Pfad zur IFC-Datei
            outPath: Pfad zur CityGML-Datei
        """

        # Initialisierung von Attributen
        self.parent = parent
        self.inPath = inPath
        self.outPath = outPath

    def run(self, lod, eade, integr):
        """ Ausführen der Konvertierung

        Args:
            lod: Gewähltes Level of Detail (LoD) als Integer
            eade: Ob die EnergyADE gewählt wurde als Boolean
            integr: Ob die QGIS-Integration gewählt wurde als Boolean
        """

        # Initialisieren von IFC und CityGML
        ifc = self.readIfc(self.inPath)
        root = self.createSchema()

        # Eigentliche Konvertierung: Unterscheidung nach den LoD
        if lod == 0:
            root = self.convertLoD0(ifc, root, eade)
        elif lod == 1:
            # TODO
            pass
        elif lod == 2:
            # TODO
            pass
        elif lod == 3:
            # TODO
            pass
        elif lod == 4:
            # TODO
            pass

        # Schreiben der CityGML in eine Datei
        self.writeCGML(root)

        # Integration der CityGML in QGIS
        if integr:
            # TODO
            pass

        # Fertigstellung
        self.parent.completed()

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

    def convertLoD0(self, ifc, root, eade):
        chName = etree.SubElement(root, QName(XmlNs.gml, "name"))
        chName.text = self.outPath[self.outPath.rindex("\\") + 1:-4]

        ifcProject = ifc.by_type("IfcProject")[0]
        ifcSite = ifc.by_type("IfcSite")[0]
        ifcBuilding = ifc.by_type("IfcBuilding")[0]

        epsg = Transformer.getCRS(ifcSite)
        self.originShift = Transformer.getOriginShift(ifcSite, epsg)
        self.trans = Transformer.getTransformMatrix(ifcProject)

        # BoundedBy
        chBound = etree.SubElement(root, QName(XmlNs.gml, "boundedBy"))
        chBoundEnv = etree.SubElement(chBound, QName(XmlNs.gml, "Envelope"))
        chBoundEnv.set("srsDimension", "3")
        chBoundEnv.set("srsName", "EPSG:" + str(epsg))
        chBoundEnvLC = etree.SubElement(chBoundEnv, QName(XmlNs.gml, "lowerCorner"))
        chBoundEnvLC.set("srsDimension", "3")
        chBoundEnvUC = etree.SubElement(chBoundEnv, QName(XmlNs.gml, "upperCorner"))
        chBoundEnvUC.set("srsDimension", "3")
        # TODO: Envelope

        # Building
        chCOM = etree.SubElement(root, QName(XmlNs.core, "cityObjectMember"))
        chBldg = etree.SubElement(chCOM, QName(XmlNs.bldg, "Building"))

        # Attribute
        # GML
        chBldg.set("id", "UUID_" + str(uuid.uuid4()))
        chBldgName = etree.SubElement(chBldg, QName(XmlNs.gml, "name"))
        chBldgName.text = ifcBuilding.Name
        chBldgDescr = etree.SubElement(chBldg, QName(XmlNs.gml, "description"))
        chBldgDescr.text = ifcBuilding.Description

        # Core
        chBldgCrDate = etree.SubElement(chBldg, QName(XmlNs.core, "creationDate"))
        chBldgCrDate.text = datetime.now().strftime("%Y-%m-%d")

        chBldgRelTerr = etree.SubElement(chBldg, QName(XmlNs.core, "relativeToTerrain"))
        chBldgRelTerr.text = ""

        chBldgRelWater = etree.SubElement(chBldg, QName(XmlNs.core, "relativeToWater"))
        chBldgRelWater.text = ""

        # Building
        chBldgClass = etree.SubElement(chBldg, QName(XmlNs.bldg, "class"))
        chBldgClass.set("codeSpace",
                        "http://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_class.xml")
        chBldgClass.text = ifcBuilding.ObjectType

        chBldgFunc = etree.SubElement(chBldg, QName(XmlNs.bldg, "function"))
        chBldgFunc.set("codeSpace",
                       "http://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_function.xml")
        chBldgFunc.text = ifcopenshell.util.element.get_psets(ifcBuilding)["Pset_BuildingCommon"]["OccupancyType"]

        chBldgUsage = etree.SubElement(chBldg, QName(XmlNs.bldg, "usage"))
        chBldgUsage.set("codeSpace",
                        "http://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_usage.xml")
        chBldgUsage.text = ifcopenshell.util.element.get_psets(ifcBuilding)["Pset_BuildingCommon"]["OccupancyType"]
        # TODO: Mapping zwischen IFC-Freitext und CityGML-Code

        chBldgYearConstr = etree.SubElement(chBldg, QName(XmlNs.bldg, "yearOfConstruction"))
        chBldgYearConstr.text = ifcopenshell.util.element.get_psets(ifcBuilding)["Pset_BuildingCommon"][
            "YearOfConstruction"]

        chBldgRoofType = etree.SubElement(chBldg, QName(XmlNs.bldg, "roofType"))
        chBldgRoofType.set("codeSpace",
                           "http://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_roofType.xml")
        chBldgRoofType.text = ""

        chBldgHeight = etree.SubElement(chBldg, QName(XmlNs.bldg, "measuredHeight"))
        chBldgHeight.set("uom", "m")
        if self.findPset(ifc, ifcBuilding, "Qto_BuildingBaseQuantities") is not None:
            chBldgHeight.text = ifcopenshell.util.element.get_psets(ifcBuilding)["Qto_BuildingBaseQuantities"]["Height"]

        chBldgStoreysAG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysAboveGround"))
        chBldgStoreysAG.text = str(
            ifcopenshell.util.element.get_psets(ifcBuilding)["Pset_BuildingCommon"]["NumberOfStoreys"])

        chBldgStoreysBG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysBelowGround"))
        chBldgStoreysBG.text = ""

        chBldgStoreysHeightAG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysHeightsAboveGround"))
        chBldgStoreysHeightAG.text = ""

        chBldgStoreysHeightBG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysHeightsBelowGround"))
        chBldgStoreysHeightBG.text = ""
        # TODO

        # FootPrint
        chBldgFootPrint = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod0FootPrint"))
        chBldgFootPrintMS = etree.SubElement(chBldgFootPrint, QName(XmlNs.gml, "MultiSurface"))
        chBldgFootPrintSM = etree.SubElement(chBldgFootPrintMS, QName(XmlNs.gml, "surfaceMember"))

        ifcSlab = self.findElement(ifc, ifcBuilding, "IfcSlab", type="BASESLAB")[0]
        settings = ifcopenshell.geom.settings()
        shape = ifcopenshell.geom.create_shape(settings, ifcSlab)
        verts = shape.geometry.verts
        grVerts = [[verts[i], verts[i + 1], verts[i + 2]] for i in range(0, len(verts), 3)]
        maxHeight = -sys.maxsize
        for grVert in grVerts:
            if grVert[2] > maxHeight:
                maxHeight = grVert[2]

        grVertsNew = []
        for grVert in grVerts:
            grVert[2] = maxHeight
            if grVert not in grVertsNew:
                grVertsNew.append(grVert)

        ring = ogr.Geometry(ogr.wkbLinearRing)
        for grVert in grVertsNew:
            grVertTr = Transformer.georeferencePoint(self.trans, self.originShift, grVert)
            ring.AddPoint(grVertTr[0], grVertTr[1], grVertTr[2])
        geom1 = ogr.Geometry(ogr.wkbPolygon)
        geom1.AddGeometry(ring)
        cgml = geom1.ExportToGML()

        cgml = cgml[0:cgml.find(">")] + " xmlns:gml='http://www.opengis.net/gml'" + cgml[cgml.find(">"):]

        geomXML = etree.XML(cgml)
        chBldgFootPrintSM.append(geomXML)

        # RoofEdge
        chBldgRoofEdge = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod0RoofEdge"))
        # TODO: RoofEdge-Geometrie

        # Adresse
        self.convertAddress(ifc, ifcBuilding, ifcSite, chBldg)

        # EnergyADE
        if eade:
            # TODO: EnergyADE
            pass

        return root

    def convertAddress(self, ifc, ifcBuilding, ifcSite, chBldg):
        # Prüfen, wo Addresse vorhanden
        if ifcBuilding.BuildingAddress is not None:
            ifcAddress = ifcBuilding.BuildingAddress
        elif self.findAttribute(ifc, ifcBuilding, "Pset_Address") is not None:
            ifcAddress = self.findAttribute(ifc, ifcBuilding, "Pset_Address")
        elif ifcSite.SiteAddress is not None:
            ifcAddress = ifcSite.SiteAddress
        elif self.findAttribute(ifc, ifcSite, "Pset_Address") is not None:
            ifcAddress = self.findAttribute(ifc, ifcSite, "Pset_Address")
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
        chBldgAdrLocName = etree.SubElement(chBldgAdrLoc, QName(XmlNs.xAL, "LocalityName"))
        chBldgAdrLocTh = etree.SubElement(chBldgAdrLoc, QName(XmlNs.xAL, "Thoroughfare"))
        chBldgAdrLocTh.set("Type", "Street")
        chBldgAdrLocThNr = etree.SubElement(chBldgAdrLocTh, QName(XmlNs.xAL, "ThoroughfareNumber"))
        chBldgAdrLocThName = etree.SubElement(chBldgAdrLocTh, QName(XmlNs.xAL, "ThoroughfareName"))
        chBldgAdrLocPC = etree.SubElement(chBldgAdrLoc, QName(XmlNs.xAL, "PostalCode"))
        chBldgAdrLocPCNr = etree.SubElement(chBldgAdrLocPC, QName(XmlNs.xAL, "PostalCodeNumber"))

        # Eintragen der Adresse
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
        chBldgAdrLocPCNr.text = ifcAddress.PostalCode
        chBldgAdrLocName.text = ifcAddress.Town

    @staticmethod
    def findPset(ifc, ifcElement, psetName):
        psets = ifcopenshell.util.element.get_psets(ifcElement)
        if psetName in psets:
            return psets[psetName]
        else:
            return None

    def findElement(self, ifc, inElement, outElement, result=[], type=None):
        rels = ifc.get_inverse(inElement)
        for rel in rels:
            if rel.is_a('IfcRelAggregates'):
                if rel.RelatingObject == inElement:
                    for obj in rel.RelatedObjects:
                        if obj.is_a(outElement):
                            if type is not None:
                                if obj.PredefinedType == type:
                                    if obj not in result:
                                        result.append(obj)
                            else:
                                if obj not in result:
                                    result.append(obj)
                        else:
                            self.findElement(ifc, obj, outElement, result, type)
            elif rel.is_a("IfcRelSpaceBoundary"):
                if rel.RelatingSpace == inElement:
                    obj = rel.RelatedBuildingElement
                    if obj is not None:
                        if obj.is_a(outElement):
                            if type is not None:
                                if obj.PredefinedType == type:
                                    if obj not in result:
                                        result.append(obj)
                            else:
                                if obj not in result:
                                    result.append(obj)
                        else:
                            self.findElement(ifc, obj, outElement, result, type)
        return result
