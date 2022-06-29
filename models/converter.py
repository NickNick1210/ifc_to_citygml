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
from datetime import datetime

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

# Plugin
from .xmlns import XmlNs
from .transformer import Transformer
from .utilities import Utilities


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
        self.ifc = None
        self.trans = None

    def run(self, lod, eade, integr):
        """ Ausführen der Konvertierung

        Args:
            lod: Gewähltes Level of Detail (LoD) als Integer
            eade: Ob die EnergyADE gewählt wurde als Boolean
            integr: Ob die QGIS-Integration gewählt wurde als Boolean
        """
        # Initialisieren von IFC und CityGML
        self.ifc = self.readIfc(self.inPath)
        root = self.createSchema()

        # Initialisieren vom Transformer
        self.trans = Transformer(self.ifc)

        # Eigentliche Konvertierung: Unterscheidung nach den LoD
        if lod == 0:
            root = self.convertLoD0(root, eade)
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

    def convertLoD0(self, root, eade):
        """ Konvertieren von IFC zu CityGML im Level of Detail (LoD) 0

        Args:
            root: Das vorbereitete XML-Schema
            eade: Ob die EnergyADE gewählt wurde als Boolean
        """
        chName = etree.SubElement(root, QName(XmlNs.gml, "name"))
        chName.text = self.outPath[self.outPath.rindex("\\") + 1:-4]

        ifcProject = self.ifc.by_type("IfcProject")[0]
        ifcSite = self.ifc.by_type("IfcSite")[0]
        ifcBuilding = self.ifc.by_type("IfcBuilding")[0]

        # BoundedBy
        chBound = etree.SubElement(root, QName(XmlNs.gml, "boundedBy"))
        chBoundEnv = etree.SubElement(chBound, QName(XmlNs.gml, "Envelope"))
        chBoundEnv.set("srsDimension", "3")
        chBoundEnv.set("srsName", "EPSG:" + str(self.trans.epsg))
        chBoundEnvLC = etree.SubElement(chBoundEnv, QName(XmlNs.gml, "lowerCorner"))
        chBoundEnvLC.set("srsDimension", "3")
        chBoundEnvUC = etree.SubElement(chBoundEnv, QName(XmlNs.gml, "upperCorner"))
        chBoundEnvUC.set("srsDimension", "3")
        # TODO: Envelope

        # Building
        chCOM = etree.SubElement(root, QName(XmlNs.core, "cityObjectMember"))
        chBldg = etree.SubElement(chCOM, QName(XmlNs.bldg, "Building"))

        self.convertBldgAttr(ifcBuilding, chBldg)
        self.convertFootPrint(ifcBuilding, chBldg)
        self.convertRoofEdge(ifcBuilding, chBldg)
        self.convertAddress(ifcBuilding, ifcSite, chBldg)

        # EnergyADE
        if eade:
            # TODO: EnergyADE
            pass

        return root

    def convertBldgAttr(self, ifcBuilding, chBldg):

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
        chBldgFunc.text = element.get_psets(ifcBuilding)["Pset_BuildingCommon"]["OccupancyType"]

        chBldgUsage = etree.SubElement(chBldg, QName(XmlNs.bldg, "usage"))
        chBldgUsage.set("codeSpace",
                        "http://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_usage.xml")
        chBldgUsage.text = element.get_psets(ifcBuilding)["Pset_BuildingCommon"]["OccupancyType"]
        # TODO: Mapping zwischen IFC-Freitext und CityGML-Code

        chBldgYearConstr = etree.SubElement(chBldg, QName(XmlNs.bldg, "yearOfConstruction"))
        chBldgYearConstr.text = element.get_psets(ifcBuilding)["Pset_BuildingCommon"][
            "YearOfConstruction"]

        chBldgRoofType = etree.SubElement(chBldg, QName(XmlNs.bldg, "roofType"))
        chBldgRoofType.set("codeSpace",
                           "http://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_roofType.xml")
        chBldgRoofType.text = ""

        chBldgHeight = etree.SubElement(chBldg, QName(XmlNs.bldg, "measuredHeight"))
        chBldgHeight.set("uom", "m")
        if Utilities.findPset(self.ifc, ifcBuilding, "Qto_BuildingBaseQuantities") is not None:
            chBldgHeight.text = element.get_psets(ifcBuilding)["Qto_BuildingBaseQuantities"]["Height"]

        chBldgStoreysAG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysAboveGround"))
        chBldgStoreysAG.text = str(element.get_psets(ifcBuilding)["Pset_BuildingCommon"]["NumberOfStoreys"])

        chBldgStoreysBG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysBelowGround"))
        chBldgStoreysBG.text = ""

        chBldgStoreysHeightAG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysHeightsAboveGround"))
        chBldgStoreysHeightAG.text = ""

        chBldgStoreysHeightBG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysHeightsBelowGround"))
        chBldgStoreysHeightBG.text = ""
        # TODO

    def convertFootPrint(self, ifcBuilding, chBldg):
        """ Konvertieren der Grundfläche von IFC zu CityGML

        Args:
            ifcBuilding: Das Gebäude, aus dem die Grundfläche entnommen werden soll
            chBldg: XML-Element an dem die Grundfläche angefügt werden soll
        """
        # XML-Struktur
        chBldgFootPrint = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod0FootPrint"))
        chBldgFootPrintMS = etree.SubElement(chBldgFootPrint, QName(XmlNs.gml, "MultiSurface"))
        chBldgFootPrintSM = etree.SubElement(chBldgFootPrintMS, QName(XmlNs.gml, "surfaceMember"))

        # Geometrie
        ifcSlabs = Utilities.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="BASESLAB")
        geomXML = self.calcPlane(ifcSlabs, True)
        chBldgFootPrintSM.append(geomXML)

    def convertRoofEdge(self, ifcBuilding, chBldg):
        """ Konvertieren der Dachkantenfläche von IFC zu CityGML

        Args:
            ifcBuilding: Das Gebäude, aus dem die Dachkantenfläche entnommen werden soll
            chBldg: XML-Element an dem die Dachkantenfläche angefügt werden soll
        """
        # XML-Struktur
        chBldgRoofEdge = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod0RoofEdge"))
        chBldgRoofEdgeMS = etree.SubElement(chBldgRoofEdge, QName(XmlNs.gml, "MultiSurface"))
        chBldgRoofEdgeSM = etree.SubElement(chBldgRoofEdgeMS, QName(XmlNs.gml, "surfaceMember"))

        # Geometrie
        ifcSlabs = Utilities.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="ROOF")
        geomXML = self.calcPlane(ifcSlabs, False)
        chBldgRoofEdgeSM.append(geomXML)

    def calcPlane(self, ifcElements, mode):
        """ Berechnung einer planen Flächengeometrie

        Args:
            ifcElements: Elemente, aus denen die Fläche berechnet werden soll
            mode: Ob die höchste oder geringste Höhe zählt als Boolean

        Returns:
            chBldg: Erzeugte GML-Geometrie
        """
        # Vertizes aus den Elementen entnehmen
        grVerts = []
        for ifcElement in ifcElements:
            settings = ifcopenshell.geom.settings()
            shape = ifcopenshell.geom.create_shape(settings, ifcElement)
            verts = shape.geometry.verts
            grVertsCurr = [[verts[i], verts[i + 1], verts[i + 2]] for i in range(0, len(verts), 3)]
            points = self.trans.placePoints(ifcElement, grVertsCurr)
            grVerts += points

        # Höhe berechnen, abhängig vom Modus
        height = -sys.maxsize if mode else sys.maxsize
        for grVert in grVerts:
            if (mode and grVert[2] > height) or (not mode and grVert[2] < height):
                height = grVert[2]

        #
        ring = ogr.Geometry(ogr.wkbLinearRing)
        grVertsCheck = []
        for grVert in grVerts:
            grVert[2] = height
            if grVert not in grVertsCheck:
                grVertsCheck.append(grVert)
                ring.AddPoint(grVert[0], grVert[1], grVert[2])

        geom1 = ogr.Geometry(ogr.wkbPolygon)
        geom1.AddGeometry(ring)
        geomXML = Utilities.geomToGml(geom1)
        return geomXML

    def convertAddress(self, ifcBuilding, ifcSite, chBldg):
        """ Konvertieren der Adresse von IFC zu CityGML

        Args:
            ifc: Das IFC-Objekt
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
