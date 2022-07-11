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
import numpy as np

# IFC-Bibliotheken
import ifcopenshell
import ifcopenshell.util.pset
import sympy
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

# Plugin
from sympy import Point3D, Plane, Line

from .xmlns import XmlNs
from .mapper import Mapper
from .transformer import Transformer
from .utilities import Utilities


#####


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
        self.inPath, self.outPath = inPath, outPath
        self.lod, self.eade, self.integr = lod, eade, integr
        self.ifc = None
        self.trans = None
        self.geom = ogr.Geometry(ogr.wkbGeometryCollection)

    @staticmethod
    def tr(msg):
        """ Übersetzen

        Args:
            msg: zu übersetzender Text

        Returns:
            Übersetzter Text
        """
        return QCoreApplication.translate('Converter', msg)

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
            root = self.convertLoD1(root, self.eade)
        elif self.lod == 2:
            root = self.convertLoD2(root, self.eade)
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
        """ EventListener, wenn die Konvertierung abgeschlossen wurde

        Args:
            result: Ob die Konvertierung erfolgreich war als Boolean
        """
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
            self.convertLoD0FootPrint(ifcBuilding, chBldg)
            self.convertLoD0RoofEdge(ifcBuilding, chBldg)
            self.convertAddress(ifcBuilding, ifcSite, chBldg)
            self.convertBound(self.geom, chBound)

            # EnergyADE
            if eade:
                # TODO: EnergyADE
                pass

        return root

    def convertLoD1(self, root, eade):
        """ Konvertieren von IFC zu CityGML im Level of Detail (LoD) 1

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
            height = self.convertBldgAttr(ifcBuilding, chBldg)
            self.convertLoD1Solid(ifcBuilding, chBldg, height)
            self.convertAddress(ifcBuilding, ifcSite, chBldg)
            self.convertBound(self.geom, chBound)

            # EnergyADE
            if eade:
                # TODO: EnergyADE
                pass

        return root

    def convertLoD2(self, root, eade):
        """ Konvertieren von IFC zu CityGML im Level of Detail (LoD) 2

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
            height = self.convertBldgAttr(ifcBuilding, chBldg)
            links = self.convertBldgBound(ifcBuilding, chBldg, height)
            self.convertLoD2Solid(chBldg, links)
            self.convertAddress(ifcBuilding, ifcSite, chBldg)
            self.convertBound(self.geom, chBound)

            # EnergyADE
            if eade:
                # TODO: EnergyADE
                pass

        return root

    def convertBound(self, geometry, chBound):
        """ Konvertierung der Bounding Box

        Args:
            geometry: Die konvertierten Geometrien
            chBound: XML-Objekt, an das die Bounding Box angehängt werden soll
        """
        # Prüfung, ob Geometrien vorhanden
        if geometry.GetGeometryCount() == 0:
            self.parent.dlg.log(self.tr(u'Due to the missing geometries, no bounding box can be calculated'))
            return

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
        """ Konvertierung der Gebäudeattribute

        Args:
            ifcBuilding: IFC-Gebäude, aus dem die Attribute entnommen werden sollen
            chBldg: XML-Objekt, an das die Gebäudeattribute angehängt werden soll
        """
        # ID
        chBldg.set(QName(XmlNs.gml, "id"), "UUID_" + str(uuid.uuid4()))

        # Name
        if ifcBuilding.Name is not None:
            chBldgName = etree.SubElement(chBldg, QName(XmlNs.gml, "name"))
            chBldgName.text = ifcBuilding.Name

        # Beschreibung
        if ifcBuilding.Description is not None:
            chBldgDescr = etree.SubElement(chBldg, QName(XmlNs.gml, "description"))
            chBldgDescr.text = ifcBuilding.Description

        # Erstellungsdatum
        chBldgCrDate = etree.SubElement(chBldg, QName(XmlNs.core, "creationDate"))
        chBldgCrDate.text = datetime.now().strftime("%Y-%m-%d")

        # Klasse, Typ und Funktion
        # Prüfung des OccupancyType im PropertySet BuildingCommon
        if Utilities.findPset(ifcBuilding, "Pset_BuildingCommon", "OccupancyType") is not None:
            occType = element.get_psets(ifcBuilding)["Pset_BuildingCommon"]["OccupancyType"]
            type = self.convertFunctionUsage(occType)
            if type is None:
                type = self.convertFunctionUsage(ifcBuilding.ObjectType)
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

        # Baujahr
        if Utilities.findPset(ifcBuilding, "Pset_BuildingCommon", "YearOfConstruction") is not None:
            chBldgYearConstr = etree.SubElement(chBldg, QName(XmlNs.bldg, "yearOfConstruction"))
            chBldgYearConstr.text = element.get_psets(ifcBuilding)["Pset_BuildingCommon"]["YearOfConstruction"]

        # Dachtyp
        ifcRoofs = Utilities.findElement(self.ifc, ifcBuilding, "IfcRoof", result=[])
        if ifcRoofs is not None:
            roofTypes = []
            for ifcRoof in ifcRoofs:
                if ifcRoof.PredefinedType is not None and ifcRoof.PredefinedType != "NOTDEFINED":
                    roofTypes.append(ifcRoof.PredefinedType)
            if len(roofTypes) > 0:
                # XML-Struktur
                chBldgRoofType = etree.SubElement(chBldg, QName(XmlNs.bldg, "roofType"))
                chBldgRoofType.set("codeSpace",
                                   "http://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_roofType.xml")
                # Mapping
                roofType = max(set(roofTypes), key=roofTypes.count)
                roofCode = Mapper.roofTypeDict[roofType]
                chBldgRoofType.text = str(roofCode)

        # Höhen und Geschosse
        ifcBldgStoreys = Utilities.findElement(self.ifc, ifcBuilding, "IfcBuildingStorey", result=[])
        storeysAG, storeysBG = 0, 0
        storeysHeightsAG, storeysHeightsBG = 0, 0
        missingAG, missingBG = 0, 0
        # über alle Geschosse iterieren
        for ifcBldgStorey in ifcBldgStoreys:
            # Herausfinden, ob über oder unter Grund
            if Utilities.findPset(ifcBldgStorey, "Pset_BuildingStoreyCommon") is not None and \
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
            if Utilities.findPset(ifcBldgStorey, "BaseQuantities", "GrossHeight") is not None:
                height = element.get_psets(ifcBldgStorey)["BaseQuantities"]["GrossHeight"]
            elif Utilities.findPset(ifcBldgStorey, "Qto_BuildingStoreyBaseQuantities",
                                    "GrossHeight") is not None:
                height = element.get_psets(ifcBldgStorey)["Qto_BuildingStoreyBaseQuantities"]["GrossHeight"]
            elif Utilities.findPset(ifcBldgStorey, "BaseQuantities", "Height") is not None:
                height = element.get_psets(ifcBldgStorey)["BaseQuantities"]["Height"]
            elif Utilities.findPset(ifcBldgStorey, "Qto_BuildingStoreyBaseQuantities", "Height") is not None:
                height = element.get_psets(ifcBldgStorey)["Qto_BuildingStoreyBaseQuantities"]["Height"]
            elif Utilities.findPset(ifcBldgStorey, "BaseQuantities", "NetHeight") is not None:
                height = element.get_psets(ifcBldgStorey)["BaseQuantities"]["NetHeight"]
            elif Utilities.findPset(ifcBldgStorey, "Qto_BuildingStoreyBaseQuantities",
                                    "NetHeight") is not None:
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
        if storeysBG == 0:
            chBldgRelTerr.text = "entirelyAboveTerrain"
        elif storeysAG == 0:
            chBldgRelTerr.text = "entirelyBelowTerrain"
        elif storeysBG == storeysAG:
            chBldgRelTerr.text = "substaintiallyAboveAndBelowTerrain"
        elif storeysAG > storeysBG:
            chBldgRelTerr.text = "substaintiallyAboveTerrain"
        else:
            chBldgRelTerr.text = "substaintiallyBelowTerrain"

        # Gebäudehöhe
        height = self.calcHeight(ifcBuilding)
        if height is not None:
            pass
        elif Utilities.findPset(ifcBuilding, "BaseQuantities", "GrossHeight") is not None:
            height = element.get_psets(ifcBuilding)["BaseQuantities"]["GrossHeight"]
        elif Utilities.findPset(ifcBuilding, "Qto_BuildingBaseQuantities", "GrossHeight") is not None:
            height = element.get_psets(ifcBuilding)["Qto_BuildingBaseQuantities"]["GrossHeight"]
        elif Utilities.findPset(ifcBuilding, "BaseQuantities", "Height") is not None:
            height = element.get_psets(ifcBuilding)["BaseQuantities"]["Height"]
        elif Utilities.findPset(ifcBuilding, "Qto_BuildingBaseQuantities", "Height") is not None:
            height = element.get_psets(ifcBuilding)["Qto_BuildingBaseQuantities"]["Height"]
        elif Utilities.findPset(ifcBuilding, "BaseQuantities", "NetHeight") is not None:
            height = element.get_psets(ifcBuilding)["BaseQuantities"]["NetHeight"]
        elif Utilities.findPset(ifcBuilding, "Qto_BuildingBaseQuantities", "NetHeight") is not None:
            height = element.get_psets(ifcBuilding)["Qto_BuildingBaseQuantities"]["NetHeight"]
        elif storeysHeightsAG > 0 or storeysHeightsBG > 0:
            if storeysAG == 0 and storeysBG != 0:
                height = storeysHeightsBG + missingBG * (storeysHeightsBG / storeysBG)
            elif storeysBG == 0 and storeysAG != 0:
                height = storeysHeightsAG + missingAG * (storeysHeightsAG / storeysAG)
            else:
                height = (storeysHeightsAG + missingAG * (
                        storeysHeightsAG / storeysAG) + storeysHeightsBG + missingBG * (
                                  storeysHeightsBG / storeysBG))

        if height != 0 and height is not None:
            chBldgHeight = etree.SubElement(chBldg, QName(XmlNs.bldg, "measuredHeight"))
            chBldgHeight.set("uom", "m")
            chBldgHeight.text = str(round(height, 5))

        # Geschossangaben
        chBldgStoreysAG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysAboveGround"))
        chBldgStoreysAG.text = str(storeysAG)
        chBldgStoreysBG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysBelowGround"))
        chBldgStoreysBG.text = str(storeysBG)
        if (storeysAG - missingAG) > 0:
            chBldgStoreysHeightAG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysHeightsAboveGround"))
            chBldgStoreysHeightAG.text = str(round(storeysHeightsAG / (storeysAG - missingAG), 5))
        if (storeysBG - missingBG) > 0:
            chBldgStoreysHeightBG = etree.SubElement(chBldg, QName(XmlNs.bldg, "storeysHeightsBelowGround"))
            chBldgStoreysHeightBG.text = str(round(storeysHeightsBG / (storeysBG - missingBG), 5))

        return height

    @staticmethod
    def convertFunctionUsage(typeIn):
        """ Konvertieren den Eingabetypen in einen standardisierten Code

        Args:
            typeIn: Bezeichnung eines Typen, der konvertiert werden soll

        Returns:
            Den standardisierten Code bzw. None, wenn nicht zuzuordnen
        """
        type = None
        if typeIn is not None:
            typeIn = typeIn.lower()

            # Prüfung, ob Angabe bereits als Code geschieht
            if any(char.isdigit() for char in typeIn):
                number = ""
                for char in typeIn:
                    if char.isdigit():
                        number += char
                    elif len(number) == 4:
                        break
                    else:
                        number = ""
                numberNr = int(number)
                if 2700 >= numberNr >= 1000 and numberNr % 10 == 0:
                    type = number

            # Prüfung, ob Angabe in Mapping vorhanden
            if type is None and typeIn in Mapper.functionUsageDict:
                type = Mapper.functionUsageDict[typeIn]

            # Prüfung, ob Teile der Angabe in Mapping vorhanden
            if type is None:
                occType = typeIn.replace("_", " ").replace("-", " ").replace(",", " ").replace(";", " ")
                for occTypeSub in occType.split():
                    if occTypeSub in Mapper.functionUsageDict:
                        type = Mapper.functionUsageDict[occTypeSub]
        return type

    def calcHeight(self, ifcBuilding):
        """ Berechnung der Gebäudehöhe als Differenz zwischen tiefstem und höchstem Punkt

        Args:
            ifcBuilding: IFC-Gebäude, dessen Höhe berechnet werden soll

        Returns:
            Die Gebäudehöhe bzw. None, wenn sie nicht berechnet werden kann
        """
        # Grundfläche
        ifcSlabs = Utilities.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="BASESLAB")
        if len(ifcSlabs) == 0:
            ifcSlabs = Utilities.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="FLOOR")
            # Wenn Grundfläche nicht vorhanden
            if len(ifcSlabs) == 0:
                self.parent.dlg.log(self.tr(
                    u"Due to the missing baseslab and building/storeys attributes, no building height can be calculated"))
                return None

        # Dächer
        ifcRoofs = Utilities.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="ROOF")
        if len(ifcRoofs) == 0:
            ifcRoofs = Utilities.findElement(self.ifc, ifcBuilding, "IfcRoof", result=[])
            # Wenn Dach nicht vorhanden
            if len(ifcRoofs) == 0:
                self.parent.dlg.log(self.tr(
                    u"Due to the missing roof and building/storeys attributes, no building height can be calculated"))
                return None

        # Berechnung der Minimalhöhe
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)
        minHeight = sys.maxsize
        for ifcSlab in ifcSlabs:
            shape = ifcopenshell.geom.create_shape(settings, ifcSlab)
            verts = shape.geometry.verts
            for i in range(2, len(verts), 3):
                if verts[2] < minHeight:
                    minHeight = verts[2]

        # Berechnung der Maximalhöhe
        maxHeight = -sys.maxsize
        for ifcRoof in ifcRoofs:
            shape = ifcopenshell.geom.create_shape(settings, ifcRoof)
            verts = shape.geometry.verts
            for i in range(2, len(verts), 3):
                if verts[i] > maxHeight:
                    maxHeight = verts[i]

        height = maxHeight - minHeight
        return height

    def convertLoD0FootPrint(self, ifcBuilding, chBldg):
        """ Konvertieren der Grundfläche von IFC zu CityGML

        Args:
            ifcBuilding: Das Gebäude, aus dem die Grundfläche entnommen werden soll
            chBldg: XML-Element an dem die Grundfläche angefügt werden soll
        """
        # IFC-Elemente
        ifcSlabs = Utilities.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="BASESLAB")
        if len(ifcSlabs) == 0:
            ifcSlabs = Utilities.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="FLOOR")
            # Wenn keine Grundfläche vorhanden
            if len(ifcSlabs) == 0:
                self.parent.dlg.log(self.tr(u"Due to the missing baseslab, no FootPrint geometry can be calculated"))
                return

        # Geometrie
        geometry = self.calcPlane(ifcSlabs)
        self.geom.AddGeometry(geometry)
        geomXML = Utilities.geomToGml(geometry)
        if geomXML is not None:
            # XML-Struktur
            chBldgFootPrint = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod0FootPrint"))
            chBldgFootPrintMS = etree.SubElement(chBldgFootPrint, QName(XmlNs.gml, "MultiSurface"))
            chBldgFootPrintSM = etree.SubElement(chBldgFootPrintMS, QName(XmlNs.gml, "surfaceMember"))
            chBldgFootPrintSM.append(geomXML)

    def convertLoD0RoofEdge(self, ifcBuilding, chBldg):
        """ Konvertieren der Dachkantenfläche von IFC zu CityGML

        Args:
            ifcBuilding: Das Gebäude, aus dem die Dachkantenfläche entnommen werden soll
            chBldg: XML-Element an dem die Dachkantenfläche angefügt werden soll
        """

        # IFC-Elemente
        ifcRoofs = Utilities.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="ROOF")
        if len(ifcRoofs) == 0:
            ifcRoofs = Utilities.findElement(self.ifc, ifcBuilding, "IfcRoof", result=[])
            # Wenn kein Dach vorhanden
            if len(ifcRoofs) == 0:
                self.parent.dlg.log(self.tr(u"Due to the missing roof, no RoofEdge geometry can be calculated"))
                return

        # Geometrie
        geometry = self.calcPlane(ifcRoofs)
        self.geom.AddGeometry(geometry)
        geomXML = Utilities.geomToGml(geometry)
        if geomXML is not None:
            # XML-Struktur
            chBldgRoofEdge = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod0RoofEdge"))
            chBldgRoofEdgeMS = etree.SubElement(chBldgRoofEdge, QName(XmlNs.gml, "MultiSurface"))
            chBldgRoofEdgeSM = etree.SubElement(chBldgRoofEdgeMS, QName(XmlNs.gml, "surfaceMember"))
            chBldgRoofEdgeSM.append(geomXML)

    def calcPlane(self, ifcElements):
        """ Berechnung einer planen Flächengeometrie

        Args:
            ifcElements: Elemente, aus denen die Fläche berechnet werden soll

        Returns:
            Erzeugte GML-Geometrie
        """
        # Vertizes aus den Elementen entnehmen und georeferenzieren
        grVertsList = []
        for ifcElement in ifcElements:
            settings = ifcopenshell.geom.settings()
            settings.set(settings.USE_WORLD_COORDS, True)
            shape = ifcopenshell.geom.create_shape(settings, ifcElement)
            # Vertizes
            verts = shape.geometry.verts
            grVertsCurr = [[round(verts[i], 5), round(verts[i + 1]), round(verts[i + 2])] for i in
                           range(0, len(verts), 3)]
            # Flächen
            faces = shape.geometry.faces
            grFacesCurr = [[faces[i], faces[i + 1], faces[i + 2]] for i in range(0, len(faces), 3)]
            # Vertizes der Flächen
            for face in grFacesCurr:
                facePoints = [grVertsCurr[face[0]], grVertsCurr[face[1]], grVertsCurr[face[2]]]
                points = []
                for facePoint in facePoints:
                    point = self.trans.georeferencePoint(facePoint)
                    points.append(point)
                grVertsList.append(points)

        # Minimalhöhe berechnen
        height = sys.maxsize
        for grVerts in grVertsList:
            for grVert in grVerts:
                if grVert[2] < height:
                    height = grVert[2]

        # Geometrien erstellen
        geometry = None
        geometries = ogr.Geometry(ogr.wkbMultiPolygon)
        for grVerts in grVertsList:
            # Polygon aus Ring aus Punkten erstellen
            geometry = ogr.Geometry(ogr.wkbPolygon)
            ring = ogr.Geometry(ogr.wkbLinearRing)
            for grVert in grVerts:
                ring.AddPoint(grVert[0], grVert[1], height)
            ring.CloseRings()
            geometry.AddGeometry(ring)

            # Geometrie testen und ggf. zur Liste hinzufügen
            if not geometry.IsValid():
                geomValid = geometry.MakeValid()
                if geomValid is not None:
                    geometry = geomValid
                geomNorm = geometry.Normalize()
                if geomNorm is not None:
                    geometry = geomNorm
            if geometry.GetGeometryName() == "POLYGON":
                geometries.AddGeometry(geometry)

        # Wenn mehr als eine Geometrie: Union
        if geometries.GetGeometryCount() > 1:
            geometry = geometries.UnionCascaded()

            # Wenn immer noch mehr als eine Geometrie: Buffer und dann Union
            if geometry.GetGeometryCount() > 1:
                geometriesBuffer = ogr.Geometry(ogr.wkbMultiPolygon)
                for i in range(0, geometries.GetGeometryCount()):
                    g = geometries.GetGeometryRef(i)
                    gBuffer = g.Buffer(0.1, quadsecs=2)
                    geometriesBuffer.AddGeometry(gBuffer)
                geometry = geometriesBuffer.UnionCascaded()

                # Wenn immer noch mehr als eine Geometrie: Fehlermeldung
                if geometry.GetGeometryName() != "POLYGON":
                    self.parent.dlg.log(self.tr(
                        u'Due to non-meter-metrics or the lack of topology, no lod0 geometry can be calculated'))
                    return None

                # Wenn nur noch eine Geometrie: Höhe wieder hinzufügen
                else:
                    geometry.Set3D(True)
                    wkt = geometry.ExportToWkt()
                    wkt = wkt.replace(" 0,", " " + str(height) + ",").replace(" 0)", " " + str(height) + ")")
                    geometry = ogr.CreateGeometryFromWkt(wkt)

        geometry = geometry.Simplify(0.0)
        return geometry

    def convertLoD1Solid(self, ifcBuilding, chBldg, height):
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
        ifcSlabs = Utilities.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="BASESLAB")
        if len(ifcSlabs) == 0:
            ifcSlabs = Utilities.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="FLOOR")
            # Wenn keine Grundfläche vorhanden
            if len(ifcSlabs) == 0:
                self.parent.dlg.log(self.tr(u"Due to the missing baseslab, no building geometry can be calculated"))
                return

        # Berechnung Grundfläche
        geomBase = self.calcPlane(ifcSlabs)

        # Berechnung Umriss
        geometries = self.extrude(geomBase, height)

        # Geometrie
        if geometries is not None and len(geometries) > 0:
            # XML-Struktur
            chBldgSolid = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod1Solid"))
            chBldgSolidSol = etree.SubElement(chBldgSolid, QName(XmlNs.gml, "Solid"))
            chBldgSolidExt = etree.SubElement(chBldgSolidSol, QName(XmlNs.gml, "exterior"))
            chBldgSolidCS = etree.SubElement(chBldgSolidExt, QName(XmlNs.gml, "CompositeSurface"))
            for geometry in geometries:
                self.geom.AddGeometry(geometry)
                chBldgSolidSM = etree.SubElement(chBldgSolidCS, QName(XmlNs.gml, "surfaceMember"))
                geomXML = Utilities.geomToGml(geometry)
                chBldgSolidSM.append(geomXML)

    @staticmethod
    def extrude(geomBase, height):
        """ Berechnung eines Körpers als Extrusion einer Grundfläche

        Args:
            geomBase: Grundfläche des Körpers als Polygon
            height: Höhe der Extrusion als float

        Returns:
            Liste der erzeugten Umriss-Polygone
        """
        # Grundfläche
        geometries = [geomBase]
        ringBase = geomBase.GetGeometryRef(0)

        # Dachfläche
        geomRoof = ogr.Geometry(ogr.wkbPolygon)
        ringRoof = ogr.Geometry(ogr.wkbLinearRing)
        for i in range(ringBase.GetPointCount() - 1, -1, -1):
            pt = ringBase.GetPoint(i)
            ringRoof.AddPoint(pt[0], pt[1], pt[2] + height)
        geomRoof.AddGeometry(ringRoof)
        geometries.append(geomRoof)

        # Wandflächen
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
            geometries.append(geomWall)

        return geometries

    def convertBldgBound(self, ifcBuilding, chBldg, height):
        """ Konvertieren des erweiterten Gebäudeumrisses von IFC zu CityGML

        Args:
            ifcBuilding: Das Gebäude, aus dem der Gebäudeumriss entnommen werden soll
            chBldg: XML-Element an dem der Gebäudeumriss angefügt werden soll
        """
        # Prüfung, ob die Höhe unbekannt ist
        if height is None or height == 0:
            self.parent.dlg.log(self.tr(u'Due to the missing height and roof, no building geometry can be calculated'))

        # IFC-Elemente der Grundfläche
        ifcSlabs = Utilities.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="BASESLAB")
        if len(ifcSlabs) == 0:
            ifcSlabs = Utilities.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="FLOOR")
            # Wenn keine Grundfläche vorhanden
            if len(ifcSlabs) == 0:
                self.parent.dlg.log(self.tr(u"Due to the missing baseslab, no building geometry can be calculated"))
                return

        # Berechnung Grundfläche
        geomBase = self.calcPlane(ifcSlabs)

        # IFC-Elemente des Daches
        ifcRoofs = Utilities.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="ROOF")
        ifcRoofs += Utilities.findElement(self.ifc, ifcBuilding, "IfcRoof", result=[])
        if len(ifcRoofs) == 0:
            self.parent.dlg.log(self.tr(
                u"Due to the missing roof, no building geometry can be calculated"))
            return None

        geomRoofs = self.extractRoofs(ifcRoofs)
        geomWalls, roofPoints = self.calcWalls(geomBase, geomRoofs, height)
        geomWallsR, geomRoofs = self.calcRoofWalls(geomRoofs)
        geomRoofs = self.calcRoofs(geomRoofs, geomBase, roofPoints)
        geomWalls += self.checkRoofWalls(geomWallsR, geomRoofs)

        # TODO: Löcher stopfen
        # TODO: Union von RoofWalls
        # TODO: Dach für Wände ohne Dach
        # TODO: Wände ohne Dach mit richtiger Höhe nach Dachschnitt

        # Geometrie
        links = []
        if geomWalls is not None and len(geomRoofs) > 0 and geomRoofs is not None and len(geomRoofs) > 0:
            link = self.setElement(chBldg, geomBase, "GroundSurface")
            links.append(link)
            for geomRoof in geomRoofs:
                link = self.setElement(chBldg, geomRoof, "RoofSurface")
                links.append(link)
            for geomWall in geomWalls:
                link = self.setElement(chBldg, geomWall, "WallSurface")
                links.append(link)
        return links

    def setElement(self, chBldg, geometry, type):
        self.geom.AddGeometry(geometry)
        chBldgBB = etree.SubElement(chBldg, QName(XmlNs.bldg, "boundedBy"))
        chBldgS = etree.SubElement(chBldgBB, QName(XmlNs.bldg, type))
        chBldgS.set(QName(XmlNs.gml, "id"), "GML_" + str(uuid.uuid4()))
        chBldgSurfSMS = etree.SubElement(chBldgS, QName(XmlNs.bldg, "lod2MultiSurface"))
        chBldgMS = etree.SubElement(chBldgSurfSMS, QName(XmlNs.bldg, "MultiSurface"))
        chBldgSM = etree.SubElement(chBldgMS, QName(XmlNs.bldg, "surfaceMember"))
        geomXML = Utilities.geomToGml(geometry)
        chBldgSM.append(geomXML)
        chBldgPol = chBldgSM[0]
        gmlId = "PolyID" + str(uuid.uuid4())
        chBldgPol.set(QName(XmlNs.gml, "id"), gmlId)
        return gmlId

    def extractRoofs(self, ifcRoofs):
        roofs = []
        for ifcRoof in ifcRoofs:
            settings = ifcopenshell.geom.settings()
            settings.set(settings.USE_WORLD_COORDS, True)
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

            geometriesRefList = []
            checkList = []
            for i in range(0, geometries.GetGeometryCount()):
                if i not in checkList:
                    geometry = geometries.GetGeometryRef(i)
                    geometriesRef = ogr.Geometry(ogr.wkbMultiPolygon)
                    geometriesRef.AddGeometry(geometry)
                    ring = geometry.GetGeometryRef(0)
                    apv = np.array(ring.GetPoint(0))
                    r1 = np.array(ring.GetPoint(1)) - np.array(ring.GetPoint(0))
                    r2 = np.array(ring.GetPoint(2)) - np.array(ring.GetPoint(0))
                    nv = np.cross(r1, r2)
                    checkList.append(i)

                    for j in range(i + 1, geometries.GetGeometryCount()):
                        ogeometry = geometries.GetGeometryRef(j)
                        oring = ogeometry.GetGeometryRef(0)
                        oapv = np.array(oring.GetPoint(0))
                        or1 = np.array(oring.GetPoint(1)) - np.array(oring.GetPoint(0))
                        or2 = np.array(oring.GetPoint(2)) - np.array(oring.GetPoint(0))
                        onv = np.cross(or1, or2)
                        cos = np.linalg.norm(np.dot(nv, onv)) / (np.linalg.norm(nv) * np.linalg.norm(onv))
                        angle = np.arccos(cos)

                        if angle < 0.001 or math.isnan(angle):
                            dist = (np.linalg.norm(np.dot(oapv - apv, nv))) / (np.linalg.norm(nv))
                            if dist < 0.001:
                                geometriesRef.AddGeometry(ogeometry)
                                checkList.append(j)
                    geometriesRefList.append(geometriesRef)

            heights = []
            areas = []
            geometriesRefUnionList = []
            for geometriesRef in geometriesRefList:
                geometriesRefUnion = geometriesRef.UnionCascaded()
                area = geometriesRefUnion.GetArea()
                ring = geometriesRefUnion.GetGeometryRef(0)
                minHeight = sys.maxsize
                maxHeight = -sys.maxsize
                for i in range(0, ring.GetPointCount()):
                    point = ring.GetPoint(i)
                    if point[2] > maxHeight:
                        maxHeight = point[2]
                    if point[2] < minHeight:
                        minHeight = point[2]
                height = maxHeight - minHeight
                area3d = height * height + area
                heights.append(maxHeight)
                areas.append(area3d)
                geometriesRefUnionList.append(geometriesRefUnion)

            finalRoof = None
            for i in range(0, len(areas)):
                if areas[i] > 0.9 * max(areas) and round(heights[i], 2) >= round(max(heights) - 0.01, 2):
                    finalRoof = geometriesRefUnionList[i]
            roofs.append(finalRoof)

        return roofs

    def calcWalls(self, base, roofs, height):
        walls = []
        roofPoints = []
        wallsWORoof = []

        ringBase = base.GetGeometryRef(0)
        for i in range(0, ringBase.GetPointCount() - 1):

            # Wand ohne Dachbegrenzung
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

            intPoints = []
            intLines = []
            for roof in roofs:
                # 2D-Schnitt
                intersect = geomWall.Intersection(roof)
                if not intersect.IsEmpty():

                    # Schnittlinie
                    ipt1 = intersect.GetPoint(0)
                    ipt2 = intersect.GetPoint(1)

                    # Dachgeometrie
                    rring = roof.GetGeometryRef(0)

                    # Ebenen
                    wPlane = Plane(Point3D(pt1[0], pt1[1], pt1[2]), Point3D(pt1[0], pt1[1], pt1[2] + 1),
                                   Point3D(pt2[0], pt2[1], pt2[2]))
                    rPlane = Plane(Point3D(rring.GetPoint(0)[0], rring.GetPoint(0)[1], rring.GetPoint(0)[2]),
                                   Point3D(rring.GetPoint(1)[0], rring.GetPoint(1)[1], rring.GetPoint(1)[2]),
                                   Point3D(rring.GetPoint(2)[0], rring.GetPoint(2)[1], rring.GetPoint(2)[2]))

                    # Ebenenschnitt: Schnittgerade
                    sLine = wPlane.intersection(rPlane)[0]

                    # Einsetzen in Schnittgerade
                    r1x = (ipt1[0] - sLine.p1[0]) / (sLine.p2[0] - sLine.p1[0])
                    r2x = (ipt2[0] - sLine.p1[0]) / (sLine.p2[0] - sLine.p1[0])
                    r1y = (ipt1[1] - sLine.p1[1]) / (sLine.p2[1] - sLine.p1[1])
                    r2y = (ipt2[1] - sLine.p1[1]) / (sLine.p2[1] - sLine.p1[1])
                    z1x = sLine.p1[2] + r1x * (sLine.p2[2] - sLine.p1[2])
                    z2x = sLine.p1[2] + r2x * (sLine.p2[2] - sLine.p1[2])
                    z1y = sLine.p1[2] + r1y * (sLine.p2[2] - sLine.p1[2])
                    z2y = sLine.p1[2] + r2y * (sLine.p2[2] - sLine.p1[2])

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
                    ipt1 = [ipt1[0], ipt1[1], z1]
                    ipt2 = [ipt2[0], ipt2[1], z2]

                    # Merken der Schnittpunkte
                    if ipt1 not in intPoints:
                        intPoints.append(ipt1)
                    if ipt2 not in intPoints:
                        intPoints.append(ipt2)
                    intLines.append([ipt1, ipt2])

            # Wand mit Dachbegrenzung
            geomWall = ogr.Geometry(ogr.wkbPolygon)
            ringWall = ogr.Geometry(ogr.wkbLinearRing)
            pt1 = ringBase.GetPoint(i)
            pt2 = ringBase.GetPoint(i + 1)
            intPoints = self.sortPoints(intPoints, pt1, pt2)
            intLines = self.sortLines(intLines, pt1, pt2)

            ringWall.AddPoint(pt1[0], pt1[1], pt1[2])
            lastIx1, lastIx2 = None, None
            for intLine in intLines:
                sortIntLine = self.sortPoints(intLine, pt1, pt2)
                ipt1 = sortIntLine[0]
                ipt2 = sortIntLine[1]
                ix1 = intPoints.index(ipt1)
                ix2 = intPoints.index(ipt2)

                if not (lastIx2 is not None and ix1 < lastIx2 and ix2 < lastIx2):
                    if lastIx2 is not None and ix1 < lastIx2:
                        if ix2 > lastIx2:
                            if abs(ipt2[0] - ipt1[0]) > abs(ipt2[1] - ipt1[1]):
                                xDiff = ipt2[0] - ipt1[0]
                                xPart = intPoints[lastIx2][0] - ipt1[0]
                                proz = xPart / xDiff
                            else:
                                yDiff = ipt2[1] - ipt1[1]
                                yPart = intPoints[lastIx2][1] - ipt1[1]
                                proz = yPart / yDiff
                            zDiff = ipt2[2] - ipt1[2]
                            z = ipt1[2] + proz * zDiff
                            ringWall.AddPoint(intPoints[lastIx2][0], intPoints[lastIx2][1], z)
                            roofPoints.append([intPoints[lastIx2][0], intPoints[lastIx2][1], z])
                    else:
                        if ix1 == 0 and (ipt1[0] != pt1[0] or ipt1[1] != pt1[1]):
                            self.parent.dlg.log(self.tr(u'Due to a missing roof, a wall height can\'t be calculated!'))
                            ringWall.AddPoint(pt1[0], pt1[1], ipt1[2])
                            roofPoints.append([pt1[0], pt1[1], ipt1[2]])
                        ringWall.AddPoint(ipt1[0], ipt1[1], ipt1[2])

                    if ix2 - ix1 > 2 or (ix2 - ix1 == 2 and ix1 + 1 != lastIx2):
                        for j in range(ix1 + 1, ix2):
                            if j != lastIx2:
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
                    else:
                        ringWall.AddPoint(ipt2[0], ipt2[1], ipt2[2])
                    lastIx2 = ix2

            lastPoint = ringWall.GetPoint(ringWall.GetPointCount() - 1)
            if lastPoint[0] != pt2[0] or lastPoint[1] != pt2[1]:
                self.parent.dlg.log(self.tr(u'Due to a missing roof, a wall height can\'t be calculated!'))
                ringWall.AddPoint(pt2[0], pt2[1], lastPoint[2])
                roofPoints.append([pt2[0], pt2[1], lastPoint[2]])

            if len(intLines) == 0:
                wallsWORoof.append([pt1, pt2])

            ringWall.AddPoint(pt2[0], pt2[1], pt2[2])
            ringWall.CloseRings()
            geomWall.AddGeometry(ringWall)

            walls.append(geomWall)

            for k in range(0, len(intPoints)):
                if intPoints[k] not in roofPoints:
                    roofPoints.append(intPoints[k])

        # Wenn über keinen Teil der Wand ein Dach ist
        for wall in wallsWORoof:
            self.parent.dlg.log(self.tr(u'Due to a missing roof, a wall height can\'t be calculated!'))
            geomWall = ogr.Geometry(ogr.wkbPolygon)
            ringWall = ogr.Geometry(ogr.wkbLinearRing)
            pt1 = wall[0]
            pt2 = wall[1]
            ringWall.AddPoint(pt1[0], pt1[1], pt1[2])
            z1, z2 = height, height
            for roofPoint in roofPoints:
                if roofPoint[0] == pt1[0] and roofPoint[1] == pt1[1]:
                    z1 = roofPoint[2]
                if roofPoint[0] == pt2[0] and roofPoint[1] == pt2[1]:
                    z2 = roofPoint[2]
            ringWall.AddPoint(pt1[0], pt1[1], z1)
            roofPoints.append([pt1[0], pt1[1], z1])
            ringWall.AddPoint(pt2[0], pt2[1], z2)
            roofPoints.append([pt2[0], pt2[1], z2])
            ringWall.AddPoint(pt2[0], pt2[1], pt2[2])
            ringWall.CloseRings()
            geomWall.AddGeometry(ringWall)
            walls.append(geomWall)

        return walls, roofPoints

    def sortPoints(self, points, fromPoint, toPoint):
        if toPoint[0] > fromPoint[0]:
            if toPoint[1] > fromPoint[1]:
                points.sort(key=lambda elem: (elem[0], elem[1], elem[2]))
            else:
                points.sort(key=lambda elem: (elem[0], -elem[1], elem[2]))
        elif toPoint[0] < fromPoint[0]:
            if toPoint[1] > fromPoint[1]:
                points.sort(key=lambda elem: (-elem[0], elem[1], elem[2]))
            else:
                points.sort(key=lambda elem: (-elem[0], -elem[1], elem[2]))
        else:
            if toPoint[1] > fromPoint[1]:
                points.sort(key=lambda elem: (elem[1], elem[2]))
            else:
                points.sort(key=lambda elem: (-elem[1], elem[2]))
        return points

    def sortLines(self, lines, fromPoint, toPoint):
        if toPoint[0] > fromPoint[0]:
            if toPoint[1] > fromPoint[1]:
                lines.sort(key=lambda elem: (
                    min(elem[0][0], elem[1][0]), min(elem[0][1], elem[1][1]), min(elem[0][2], elem[1][2])))
            else:
                lines.sort(key=lambda elem: (
                    min(elem[0][0], elem[1][0]), -max(elem[0][1], elem[1][1]), min(elem[0][2], elem[1][2])))
        elif toPoint[0] < fromPoint[0]:
            if toPoint[1] > fromPoint[1]:
                lines.sort(key=lambda elem: (
                    -max(elem[0][0], elem[1][0]), min(elem[0][1], elem[1][1]), min(elem[0][2], elem[1][2])))
            else:
                lines.sort(key=lambda elem: (
                    -max(elem[0][0], elem[1][0]), -max(elem[0][1], elem[1][1]), min(elem[0][2], elem[1][2])))
        else:
            if toPoint[1] > fromPoint[1]:
                lines.sort(key=lambda elem: (min(elem[0][1], elem[1][1]), min(elem[0][2], elem[1][2])))
            else:
                lines.sort(key=lambda elem: (-max(elem[0][1], elem[1][1]), min(elem[0][2], elem[1][2])))
        return lines

    def calcRoofs(self, roofsIn, base, roofPoints):
        roofs = []

        for roofIn in roofsIn:
            intersection = roofIn.Intersection(base)

            for intGeometry in intersection:
                if intersection.GetGeometryCount() == 1:
                    ringInt = intersection.GetGeometryRef(0)
                else:
                    ringInt = intGeometry.GetGeometryRef(0)
                    if ringInt is None:
                        continue

                # Dachfläche
                geomRoof = ogr.Geometry(ogr.wkbPolygon)
                ringRoof = ogr.Geometry(ogr.wkbLinearRing)
                for i in range(ringInt.GetPointCount() - 1, -1, -1):
                    ptInt = ringInt.GetPoint(i)
                    zList = []
                    for roofPoint in roofPoints:
                        if ptInt[0] == roofPoint[0] and ptInt[1] == roofPoint[1]:
                            zList.append(roofPoint[2])
                    if len(zList) == 0:
                        ringIn = roofIn.GetGeometryRef(0)
                        for j in range(0, ringIn.GetPointCount()):
                            ptIn = ringIn.GetPoint(j)
                            if ptInt[0] == ptIn[0] and ptInt[1] == ptIn[1]:
                                z = ptIn[2]
                    elif len(zList) > 1:
                        ringIn = roofIn.GetGeometryRef(0)
                        rPlane = Plane(Point3D(ringIn.GetPoint(0)[0], ringIn.GetPoint(0)[1],
                                               ringIn.GetPoint(0)[2]),
                                       Point3D(ringIn.GetPoint(1)[0], ringIn.GetPoint(1)[1],
                                               ringIn.GetPoint(1)[2]),
                                       Point3D(ringIn.GetPoint(2)[0], ringIn.GetPoint(2)[1],
                                               ringIn.GetPoint(2)[2]))
                        wLine = Line(Point3D(ptInt[0], ptInt[1], 0), Point3D(ptInt[0], ptInt[1], 100))
                        sPoint = rPlane.intersection(wLine)[0]
                        z = float(sPoint[2])
                    else:
                        z = zList[0]

                    ringRoof.AddPoint(ptInt[0], ptInt[1], z)
                ringRoof.CloseRings()
                geomRoof.AddGeometry(ringRoof)

                roofs.append(geomRoof)
        return roofs

    def calcRoofWalls(self, roofs):
        roofsOut = roofs.copy()
        walls = []
        for i in range(0, len(roofs)):
            roof1 = roofs[i]
            for j in range(i + 1, len(roofs)):
                roof2 = roofs[j]
                if roof1.Intersects(roof2):
                    intersect = roof1.Intersection(roof2)
                    if intersect.GetGeometryName() == "POLYGON":
                        ringInt = intersect.GetGeometryRef(0)
                        ringRoof1 = roof1.GetGeometryRef(0)
                        ringRoof2 = roof2.GetGeometryRef(0)
                        z1, z2 = None, None
                        pt1, pt2 = [], []
                        for k in range(0, ringInt.GetPointCount() - 1):
                            point = ogr.Geometry(ogr.wkbPoint)
                            point.AddPoint(ringInt.GetPoint(k)[0], ringInt.GetPoint(k)[1])
                            if roof1.Contains(point):
                                for l in range(0, ringRoof2.GetPointCount()):
                                    if (ringRoof2.GetPoint(l)[0] - 0.001 <= ringInt.GetPoint(k)[0] <=
                                        ringRoof2.GetPoint(l)[0] + 0.001) and (
                                            ringRoof2.GetPoint(l)[1] - 0.001 <= ringInt.GetPoint(k)[1] <= \
                                            ringRoof2.GetPoint(l)[1] + 0.001):
                                        z2 = ringRoof2.GetPoint(l)[2]
                                        ptz2 = [ringRoof2.GetPoint(l)[0], ringRoof2.GetPoint(l)[1]]
                                        pt1.append([point.GetPoint(0)[0], point.GetPoint(0)[1]])
                            elif roof2.Contains(point):
                                for m in range(0, ringRoof1.GetPointCount()):
                                    if ringRoof1.GetPoint(m)[0] - 0.001 <= ringInt.GetPoint(k)[0] <= \
                                            ringRoof1.GetPoint(m)[0] + 0.001 and ringRoof1.GetPoint(m)[1] - 0.001 <= \
                                            ringInt.GetPoint(k)[1] <= \
                                            ringRoof1.GetPoint(m)[1] + 0.001:
                                        z1 = ringRoof1.GetPoint(m)[2]
                                        ptz1 = [ringRoof1.GetPoint(m)[0], ringRoof1.GetPoint(m)[1]]
                                        pt2.append([point.GetPoint(0)[0], point.GetPoint(0)[1]])
                        if z1 is None:
                            rPlane = Plane(Point3D(ringRoof1.GetPoint(0)[0], ringRoof1.GetPoint(0)[1],
                                                   ringRoof1.GetPoint(0)[2]),
                                           Point3D(ringRoof1.GetPoint(1)[0], ringRoof1.GetPoint(1)[1],
                                                   ringRoof1.GetPoint(1)[2]),
                                           Point3D(ringRoof1.GetPoint(2)[0], ringRoof1.GetPoint(2)[1],
                                                   ringRoof1.GetPoint(2)[2]))
                            wLine = Line(Point3D(ptz2[0], ptz2[1], 0), Point3D(ptz2[0], ptz2[1], 100))
                            sPoint = rPlane.intersection(wLine)[0]
                            z1 = float(sPoint[2])
                        if z2 is None:
                            rPlane = Plane(Point3D(ringRoof2.GetPoint(0)[0], ringRoof2.GetPoint(0)[1],
                                                   ringRoof2.GetPoint(0)[2]),
                                           Point3D(ringRoof2.GetPoint(1)[0], ringRoof2.GetPoint(1)[1],
                                                   ringRoof2.GetPoint(1)[2]),
                                           Point3D(ringRoof2.GetPoint(2)[0], ringRoof2.GetPoint(2)[1],
                                                   ringRoof2.GetPoint(2)[2]))
                            wLine = Line(Point3D(ptz1[0], ptz1[1], 0), Point3D(ptz1[0], ptz1[1], 100))
                            sPoint = rPlane.intersection(wLine)[0]
                            z2 = float(sPoint[2])

                        last = None
                        wallsInt = []
                        for n in range(0, ringInt.GetPointCount()):
                            point = [ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1]]
                            if z1 <= z2 and point not in pt1:
                                if last is not None:
                                    geomWall = ogr.Geometry(ogr.wkbPolygon)
                                    ringWall = ogr.Geometry(ogr.wkbLinearRing)
                                    p1, p2, p3, p4 = None, None, None, None
                                    if p1 is None:
                                        rPlane = Plane(Point3D(ringRoof1.GetPoint(0)[0], ringRoof1.GetPoint(0)[1],
                                                               ringRoof1.GetPoint(0)[2]),
                                                       Point3D(ringRoof1.GetPoint(1)[0], ringRoof1.GetPoint(1)[1],
                                                               ringRoof1.GetPoint(1)[2]),
                                                       Point3D(ringRoof1.GetPoint(2)[0], ringRoof1.GetPoint(2)[1],
                                                               ringRoof1.GetPoint(2)[2]))
                                        wLine = Line(Point3D(last[0], last[1], 0), Point3D(last[0], last[1], 100))
                                        sPoint = rPlane.intersection(wLine)[0]
                                        p1 = [last[0], last[1], float(sPoint[2])]
                                    if p2 is None:
                                        rPlane = Plane(Point3D(ringRoof2.GetPoint(0)[0], ringRoof2.GetPoint(0)[1],
                                                               ringRoof2.GetPoint(0)[2]),
                                                       Point3D(ringRoof2.GetPoint(1)[0], ringRoof2.GetPoint(1)[1],
                                                               ringRoof2.GetPoint(1)[2]),
                                                       Point3D(ringRoof2.GetPoint(2)[0], ringRoof2.GetPoint(2)[1],
                                                               ringRoof2.GetPoint(2)[2]))
                                        wLine = Line(Point3D(last[0], last[1], 0), Point3D(last[0], last[1], 100))
                                        sPoint = rPlane.intersection(wLine)[0]
                                        p2 = [last[0], last[1], float(sPoint[2])]
                                    if p3 is None:
                                        rPlane = Plane(Point3D(ringRoof2.GetPoint(0)[0], ringRoof2.GetPoint(0)[1],
                                                               ringRoof2.GetPoint(0)[2]),
                                                       Point3D(ringRoof2.GetPoint(1)[0], ringRoof2.GetPoint(1)[1],
                                                               ringRoof2.GetPoint(1)[2]),
                                                       Point3D(ringRoof2.GetPoint(2)[0], ringRoof2.GetPoint(2)[1],
                                                               ringRoof2.GetPoint(2)[2]))
                                        wLine = Line(Point3D(ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1], 0),
                                                     Point3D(ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1], 100))
                                        sPoint = rPlane.intersection(wLine)[0]
                                        p3 = [ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1], float(sPoint[2])]
                                    if p4 is None:
                                        rPlane = Plane(Point3D(ringRoof1.GetPoint(0)[0], ringRoof1.GetPoint(0)[1],
                                                               ringRoof1.GetPoint(0)[2]),
                                                       Point3D(ringRoof1.GetPoint(1)[0], ringRoof1.GetPoint(1)[1],
                                                               ringRoof1.GetPoint(1)[2]),
                                                       Point3D(ringRoof1.GetPoint(2)[0], ringRoof1.GetPoint(2)[1],
                                                               ringRoof1.GetPoint(2)[2]))
                                        wLine = Line(Point3D(ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1], 0),
                                                     Point3D(ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1], 100))
                                        sPoint = rPlane.intersection(wLine)[0]
                                        p4 = [ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1], float(sPoint[2])]

                                    ringWall.AddPoint(p4[0], p4[1], p4[2])
                                    ringWall.AddPoint(p3[0], p3[1], p3[2])
                                    ringWall.AddPoint(p2[0], p2[1], p2[2])
                                    ringWall.AddPoint(p1[0], p1[1], p1[2])
                                    ringWall.CloseRings()
                                    geomWall.AddGeometry(ringWall)
                                    wallsInt.append(geomWall)
                                last = [ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1]]
                            elif z2 < z1 and point not in pt2:
                                if last is not None:
                                    geomWall = ogr.Geometry(ogr.wkbPolygon)
                                    ringWall = ogr.Geometry(ogr.wkbLinearRing)
                                    p1, p2, p3, p4 = None, None, None, None
                                    if p1 is None:
                                        rPlane = Plane(Point3D(ringRoof2.GetPoint(0)[0], ringRoof2.GetPoint(0)[1],
                                                               ringRoof2.GetPoint(0)[2]),
                                                       Point3D(ringRoof2.GetPoint(1)[0], ringRoof2.GetPoint(1)[1],
                                                               ringRoof2.GetPoint(1)[2]),
                                                       Point3D(ringRoof2.GetPoint(2)[0], ringRoof2.GetPoint(2)[1],
                                                               ringRoof2.GetPoint(2)[2]))
                                        wLine = Line(Point3D(last[0], last[1], 0), Point3D(last[0], last[1], 100))
                                        sPoint = rPlane.intersection(wLine)[0]
                                        p1 = [last[0], last[1], float(sPoint[2])]
                                    if p2 is None:
                                        rPlane = Plane(Point3D(ringRoof1.GetPoint(0)[0], ringRoof1.GetPoint(0)[1],
                                                               ringRoof1.GetPoint(0)[2]),
                                                       Point3D(ringRoof1.GetPoint(1)[0], ringRoof1.GetPoint(1)[1],
                                                               ringRoof1.GetPoint(1)[2]),
                                                       Point3D(ringRoof1.GetPoint(2)[0], ringRoof1.GetPoint(2)[1],
                                                               ringRoof1.GetPoint(2)[2]))
                                        wLine = Line(Point3D(last[0], last[1], 0), Point3D(last[0], last[1], 100))
                                        sPoint = rPlane.intersection(wLine)[0]
                                        p2 = [last[0], last[1], float(sPoint[2])]
                                    if p3 is None:
                                        rPlane = Plane(Point3D(ringRoof1.GetPoint(0)[0], ringRoof1.GetPoint(0)[1],
                                                               ringRoof1.GetPoint(0)[2]),
                                                       Point3D(ringRoof1.GetPoint(1)[0], ringRoof1.GetPoint(1)[1],
                                                               ringRoof1.GetPoint(1)[2]),
                                                       Point3D(ringRoof1.GetPoint(2)[0], ringRoof1.GetPoint(2)[1],
                                                               ringRoof1.GetPoint(2)[2]))
                                        wLine = Line(Point3D(ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1], 0),
                                                     Point3D(ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1], 100))
                                        sPoint = rPlane.intersection(wLine)[0]
                                        p3 = [ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1], float(sPoint[2])]
                                    if p4 is None:
                                        rPlane = Plane(Point3D(ringRoof2.GetPoint(0)[0], ringRoof2.GetPoint(0)[1],
                                                               ringRoof2.GetPoint(0)[2]),
                                                       Point3D(ringRoof2.GetPoint(1)[0], ringRoof2.GetPoint(1)[1],
                                                               ringRoof2.GetPoint(1)[2]),
                                                       Point3D(ringRoof2.GetPoint(2)[0], ringRoof2.GetPoint(2)[1],
                                                               ringRoof2.GetPoint(2)[2]))
                                        wLine = Line(Point3D(ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1], 0),
                                                     Point3D(ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1], 100))
                                        sPoint = rPlane.intersection(wLine)[0]
                                        p4 = [ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1], float(sPoint[2])]
                                    ringWall.AddPoint(p4[0], p4[1], p4[2])
                                    ringWall.AddPoint(p3[0], p3[1], p3[2])
                                    ringWall.AddPoint(p2[0], p2[1], p2[2])
                                    ringWall.AddPoint(p1[0], p1[1], p1[2])
                                    ringWall.CloseRings()
                                    geomWall.AddGeometry(ringWall)
                                    wallsInt.append(geomWall)
                                last = [ringInt.GetPoint(n)[0], ringInt.GetPoint(n)[1]]
                            else:
                                last = None
                        walls += wallsInt

                        if z1 <= z2:
                            roofInt = roofsOut[j].Difference(intersect).Simplify(0.0)
                            ringInt = roofInt.GetGeometryRef(0)
                            ringRoof = roofsOut[j].GetGeometryRef(0)
                            rPlane = Plane(Point3D(ringRoof.GetPoint(0)[0], ringRoof.GetPoint(0)[1],
                                                   ringRoof.GetPoint(0)[2]),
                                           Point3D(ringRoof.GetPoint(1)[0], ringRoof.GetPoint(1)[1],
                                                   ringRoof.GetPoint(1)[2]),
                                           Point3D(ringRoof.GetPoint(2)[0], ringRoof.GetPoint(2)[1],
                                                   ringRoof.GetPoint(2)[2]))
                            geomRoofOut = ogr.Geometry(ogr.wkbPolygon)
                            ringRoofOut = ogr.Geometry(ogr.wkbLinearRing)
                            for o in range(0, ringInt.GetPointCount()):
                                rLine = Line(Point3D(ringInt.GetPoint(o)[0], ringInt.GetPoint(o)[1], 0),
                                             Point3D(ringInt.GetPoint(o)[0], ringInt.GetPoint(o)[1], 100))
                                z = None
                                for p in range(0, ringRoof.GetPointCount() - 1):
                                    if ringInt.GetPoint(o)[0] == ringRoof.GetPoint(p)[0] and ringInt.GetPoint(o)[1] == ringRoof.GetPoint(p)[1]:
                                        z = ringRoof.GetPoint(p)[2]
                                        break
                                if z is None:
                                    sPoint = rPlane.intersection(rLine)[0]
                                    z = float(sPoint[2])
                                ringRoofOut.AddPoint(ringInt.GetPoint(o)[0], ringInt.GetPoint(o)[1], z)
                            ringRoofOut.CloseRings()
                            geomRoofOut.AddGeometry(ringRoofOut)

                            roofsOut[j] = geomRoofOut
                        else:
                            roofInt = roofsOut[i].Difference(intersect).Simplify(0.0)
                            ringInt = roofInt.GetGeometryRef(0)
                            ringRoof = roofsOut[i].GetGeometryRef(0)
                            rPlane = Plane(Point3D(ringRoof.GetPoint(0)[0], ringRoof.GetPoint(0)[1],
                                                   ringRoof.GetPoint(0)[2]),
                                           Point3D(ringRoof.GetPoint(1)[0], ringRoof.GetPoint(1)[1],
                                                   ringRoof.GetPoint(1)[2]),
                                           Point3D(ringRoof.GetPoint(2)[0], ringRoof.GetPoint(2)[1],
                                                   ringRoof.GetPoint(2)[2]))
                            geomRoofOut = ogr.Geometry(ogr.wkbPolygon)
                            ringRoofOut = ogr.Geometry(ogr.wkbLinearRing)
                            for o in range(0, ringInt.GetPointCount()):
                                rLine = Line(Point3D(ringInt.GetPoint(o)[0], ringInt.GetPoint(o)[1], 0),
                                             Point3D(ringInt.GetPoint(o)[0], ringInt.GetPoint(o)[1], 100))
                                z = None
                                for p in range(0, ringRoof.GetPointCount() - 1):
                                    if ringInt.GetPoint(o)[0] == ringRoof.GetPoint(p)[0] and ringInt.GetPoint(o)[1] == ringRoof.GetPoint(p)[1]:
                                        z = ringRoof.GetPoint(p)[2]
                                        break
                                if z is None:
                                    sPoint = rPlane.intersection(rLine)[0]
                                    z = float(sPoint[2])
                                ringRoofOut.AddPoint(ringInt.GetPoint(o)[0], ringInt.GetPoint(o)[1], z)
                            ringRoofOut.CloseRings()
                            geomRoofOut.AddGeometry(ringRoofOut)

                            roofsOut[i] = geomRoofOut

        wallsCheck = walls.copy()
        for o in range(0, len(wallsCheck)):
            for p in range(o+1, len(wallsCheck)):
                intersect = wallsCheck[o].Intersection(wallsCheck[p])
                if not intersect.IsEmpty():
                    walls.remove(wallsCheck[o])
                    walls.remove(wallsCheck[p])

        return walls, roofsOut

    def checkRoofWalls(self, wallsIn, roofs):
        wallsOut = []
        for wall in wallsIn:
            anyInt = False
            for roof in roofs:
                intersect = wall.Intersection(roof)
                if not intersect.IsEmpty():
                    print(intersect)
                    print(wallsIn)
                    print("----------")
                    anyInt = True
            if anyInt:
                wallsOut.append(wall)
        return wallsOut

    def convertLoD2Solid(self, chBldg, links):
        """ Angabe der Gebäudegeometrie als XLinks zu den Bounds

        Args:
            chBldg: XML-Element an dem der Gebäudeumriss angefügt werden soll
            links: Zu nutzende XLinks
        """
        if links is not None and len(links) > 0:
            # XML-Struktur
            chBldgSolid = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod2Solid"))
            chBldgSolidSol = etree.SubElement(chBldgSolid, QName(XmlNs.gml, "Solid"))
            chBldgSolidExt = etree.SubElement(chBldgSolidSol, QName(XmlNs.gml, "exterior"))
            chBldgSolidCS = etree.SubElement(chBldgSolidExt, QName(XmlNs.gml, "CompositeSurface"))
            for link in links:
                chBldgSolidSM = etree.SubElement(chBldgSolidCS, QName(XmlNs.gml, "surfaceMember"))
                chBldgSolidSM.set(QName(XmlNs.xlink, "href"), link)

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
        elif Utilities.findPset(ifcBuilding, "Pset_Address") is not None:
            ifcAddress = Utilities.findPset(ifcBuilding, "Pset_Address")
        elif ifcSite.SiteAddress is not None:
            ifcAddress = ifcSite.SiteAddress
        elif Utilities.findPset(ifcSite, "Pset_Address") is not None:
            ifcAddress = Utilities.findPset(ifcSite, "Pset_Address")
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

        # Stadt
        if ifcAddress.Town is not None and ifcAddress.Town != "":
            chBldgAdrLocName = etree.SubElement(chBldgAdrLoc, QName(XmlNs.xAL, "LocalityName"))
            chBldgAdrLocName.text = ifcAddress.Town

        # Straße und Hausnummer
        if ifcAddress.AddressLines is not None and ifcAddress.AddressLines != "":
            chBldgAdrLocTh = etree.SubElement(chBldgAdrLoc, QName(XmlNs.xAL, "Thoroughfare"))
            chBldgAdrLocTh.set("Type", "Street")
            chBldgAdrLocThNr = etree.SubElement(chBldgAdrLocTh, QName(XmlNs.xAL, "ThoroughfareNumber"))
            chBldgAdrLocThName = etree.SubElement(chBldgAdrLocTh, QName(XmlNs.xAL, "ThoroughfareName"))

            address = ifcAddress.AddressLines[0]
            # Format heraussuchen
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

        # Postleitzahl
        if ifcAddress.PostalCode is not None and ifcAddress.PostalCode != "":
            chBldgAdrLocPC = etree.SubElement(chBldgAdrLoc, QName(XmlNs.xAL, "PostalCode"))
            chBldgAdrLocPCNr = etree.SubElement(chBldgAdrLocPC, QName(XmlNs.xAL, "PostalCodeNumber"))
            chBldgAdrLocPCNr.text = ifcAddress.PostalCode
