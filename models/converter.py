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
                             nsmap={'core': XmlNs.core, 'xmlns': XmlNs.xmlns, 'bdlg': XmlNs.bldg, 'gen': XmlNs.gen,
                                    'grp': XmlNs.grp, 'app': XmlNs.app, 'gml': XmlNs.gml, 'xAL': XmlNs.xAL,
                                    'xlink': XmlNs.xlink, 'xsi': XmlNs.xsi})

    def writeCGML(self, root):
        """ Schreiben der XML-Struktur in eine GML-Datei

        Args:
            root: XML-Element
        """
        etree.ElementTree(root).write(self.outPath, xml_declaration=True, encoding="UTF-8", pretty_print=True)

    @staticmethod
    def createGeom():
        # Test
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(1179091.1646903288, 712782.8838459781)
        ring.AddPoint(1161053.0218226474, 667456.2684348812)
        ring.AddPoint(1214704.933941905, 641092.8288590391)
        ring.AddPoint(1228580.428455506, 682719.3123998424)
        ring.AddPoint(1218405.0658121984, 721108.1805541387)
        ring.AddPoint(1179091.1646903288, 712782.8838459781)
        geom1 = ogr.Geometry(ogr.wkbPolygon)
        geom1.AddGeometry(ring)
        cgml = geom1.ExportToGML()
        print(cgml)

    @staticmethod
    def getTransformMatrix(project):
        def getModelContext(proj):
            for context in proj.RepresentationContexts:
                if context.ContextType == "Model":
                    return context
            print("No context for model was found in this project")

        contextForModel = getModelContext(project)
        a, b = contextForModel.TrueNorth.DirectionRatios
        transformMatrix = [[b, -a, 0], [a, b, 0], [0, 0, 1]]
        transformMatrix = np.mat(transformMatrix).I
        return transformMatrix

    @staticmethod
    def getOriginShift(site):
        def mergeDegrees(Degrees):
            if len(Degrees) == 4:
                degree = Degrees[0] + Degrees[1] / 60.0 + (Degrees[2] + Degrees[3] / 1000000.0) / 3600.0
            elif len(Degrees) == 3:
                degree = Degrees[0] + Degrees[1] / 60.0 + Degrees[2] / 3600.0
            else:
                print("Wrong input of degrees")
                degree = None
            return degree

        Lat, Lon = site.RefLatitude, site.RefLongitude
        a, b = mergeDegrees(Lat), mergeDegrees(Lon)

        source = osr.SpatialReference()
        source.ImportFromEPSG(4326)
        # Berechnung des EPSG-Codes des Zielkoordinatensystems
        # Die WGS84-Grenzen für die UTM-Zone 32N (EPSG-Code 32632) liegen
        # zwischen 6° und 12°
        # Die WGS84-Grenzen für die UTM-Zone 33N (EPSG-Code 32633) liegen
        # zwischen 12° und 18°
        if 18 > b >= 12:
            EPSG = 32633
        elif 6 <= b < 12:
            EPSG = 32632
        else:
            EPSG = -1
        target = osr.SpatialReference()
        target.ImportFromEPSG(EPSG)
        transform = osr.CoordinateTransformation(source, target)
        x, y, z = transform.TransformPoint(a, b)
        c = site.RefElevation
        return [x, y, c]

    @staticmethod
    def georeferencingPoint(transMatrix, originShift, inX, inY):
        a = [inX, inY, 0]
        result = np.mat(a) * np.mat(transMatrix) + np.mat(originShift)
        return result

    def convertLoD0(self, ifc, root, eade):
        root.set("name", "")

        # BoundedBy
        chBound = etree.SubElement(root, QName(XmlNs.core, "boundedBy"))
        chBoundEnv = etree.SubElement(chBound, QName(XmlNs.gml, "Envelope"))
        chBoundEnv.set("srsDimension", "3")
        chBoundEnv.set("srsName", "TODO!!!")
        chBoundEnvLC = etree.SubElement(chBoundEnv, QName(XmlNs.gml, "lowerCorner"))
        chBoundEnvLC.set("srsDimension", "3")
        chBoundEnvUC = etree.SubElement(chBoundEnv, QName(XmlNs.gml, "upperCorner"))
        chBoundEnvUC.set("srsDimension", "3")

        ifcProject = ifc.by_type("IfcProject")[0]
        ifcSite = ifc.by_type("IfcSite")[0]
        ifcBuilding = ifc.by_type("IfcBuilding")[0]

        originShift = self.getOriginShift(ifcSite)
        trans = self.getTransformMatrix(ifcProject)

        if ifcBuilding.Representation is not None:
            settings = geom.settings()
            settings.set(settings.INCLUDE_CURVES, True)
            settings.set(settings.USE_WORLD_COORDS, True)
            bldgShape = geom.create_shape(settings, ifcBuilding)
            verts = bldgShape.geometry.verts
            print(str(verts))

            grouped_verts = []
            for i in range(0, len(verts), 3):
                result = self.georeferencingPoint(trans, originShift, verts[i], verts[i + 1])
                array = np.array(result)
                grouped_verts.append((array[0][0], array[0][1]))
            print(str(grouped_verts))
        # TODO: BoundedBy

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
        chBldgClass.text = ""

        chBldgFunc = etree.SubElement(chBldg, QName(XmlNs.bldg, "function"))
        chBldgFunc.text = ""

        chBldgUsage = etree.SubElement(chBldg, QName(XmlNs.bldg, "usage"))
        chBldgUsage.text = ""

        chBldgYearConstr = etree.SubElement(chBldg, QName(XmlNs.bldg, "yearOfConstruction"))
        chBldgYearConstr.text = ""

        chBldgYearDem = etree.SubElement(chBldg, QName(XmlNs.bldg, "yearOfDemolition"))
        chBldgYearDem.text = ""

        chBldgRoofType = etree.SubElement(chBldg, QName(XmlNs.bldg, "roofType"))
        chBldgRoofType.text = ""

        chBldgHeight = etree.SubElement(chBldg, QName(XmlNs.bldg, "measuredHeight"))
        chBldgHeight.text = ""

        chBldgStoreysAG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysAboveGround"))
        chBldgStoreysAG.text = ""

        chBldgStoreysBG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysBelowGround"))
        chBldgStoreysBG.text = ""

        chBldgStoreysHeightAG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysHeightsAboveGround"))
        chBldgStoreysHeightAG.text = ""

        chBldgStoreysHeightBG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysHeightsBelowGround"))
        chBldgStoreysHeightBG.text = ""
        # TODO

        # FootPrint
        chBldgFootPrint = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod0FootPrint"))
        # TODO: FootPrint-Geometrie

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
        ifcAddress = None

        # Als Gebäudeattribut
        if ifcBuilding.BuildingAddress is not None:
            ifcAddress = ifcBuilding.BuildingAddress
        else:

            # Als Gebäude-Pset
            for element in ifc.get_inverse(ifcBuilding):
                if element.is_a('IfcPropertySet'):
                    if element.Name == "Pset_Address":
                        ifcAddress = element
            if ifcAddress is None:

                # Als Grundstücksattribut
                if ifcSite.SiteAddress is not None:
                    ifcAddress = ifcSite.SiteAddress
                else:

                    # Als Grundstücks-Pset
                    for element in ifc.get_inverse(ifcSite):
                        if element.is_a('IfcPropertySet'):
                            if element.Name == "Pset_Address":
                                ifcAddress = element

        if ifcAddress is not None:
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
                street = address[sep+1:]
                nr = address[0:sep]
            elif address[len(address) - 1].isdigit():
                sep = address.rfind(" ")
                street = address[0:sep]
                nr = address[sep+1:]
            else:
                street = address
                nr = ""
            chBldgAdrLocThName.text = street
            chBldgAdrLocThNr.text = nr
            chBldgAdrLocPCNr.text = ifcAddress.PostalCode
            chBldgAdrLocName.text = ifcAddress.Town

        # Addresse nicht vorhanden
        else:
            self.parent.dlg.log(u'No address details existing')