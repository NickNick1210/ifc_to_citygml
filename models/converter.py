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
        elif self.lod == 3:
            root = self.convertLoD3(root, self.eade)
        elif self.lod == 4:
            # TODO LoD4
            pass

        # Schreiben der CityGML in eine Datei
        self.writeCGML(root)

        # Integration der CityGML in QGIS
        if self.integr:
            self.parent.gis.loadIntoGIS(self.outPath)

        # Abschließen
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
            links = self.convertLoD2BldgBound(ifcBuilding, chBldg, height)
            self.convertLoDSolid(chBldg, links, 2)
            self.convertAddress(ifcBuilding, ifcSite, chBldg)
            self.convertBound(self.geom, chBound)

            # EnergyADE
            if eade:
                # TODO: EnergyADE
                pass

        return root

    def convertLoD3(self, root, eade):
        """ Konvertieren von IFC zu CityGML im Level of Detail (LoD) 3

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
            links = self.convertLoD3BldgBound(ifcBuilding, chBldg)
            self.convertLoDSolid(chBldg, links, 3)
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
        if UtilitiesIfc.findPset(ifcBuilding, "Pset_BuildingCommon", "OccupancyType") is not None:
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
        if UtilitiesIfc.findPset(ifcBuilding, "Pset_BuildingCommon", "YearOfConstruction") is not None:
            chBldgYearConstr = etree.SubElement(chBldg, QName(XmlNs.bldg, "yearOfConstruction"))
            chBldgYearConstr.text = element.get_psets(ifcBuilding)["Pset_BuildingCommon"]["YearOfConstruction"]

        # Dachtyp
        ifcRoofs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcRoof", result=[])
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
        ifcBldgStoreys = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcBuildingStorey", result=[])
        storeysAG, storeysBG = 0, 0
        storeysHeightsAG, storeysHeightsBG = 0, 0
        missingAG, missingBG = 0, 0
        # über alle Geschosse iterieren
        for ifcBldgStorey in ifcBldgStoreys:
            # Herausfinden, ob über oder unter Grund
            if UtilitiesIfc.findPset(ifcBldgStorey, "Pset_BuildingStoreyCommon") is not None and \
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
            if UtilitiesIfc.findPset(ifcBldgStorey, "BaseQuantities", "GrossHeight") is not None:
                height = element.get_psets(ifcBldgStorey)["BaseQuantities"]["GrossHeight"]
            elif UtilitiesIfc.findPset(ifcBldgStorey, "Qto_BuildingStoreyBaseQuantities",
                                       "GrossHeight") is not None:
                height = element.get_psets(ifcBldgStorey)["Qto_BuildingStoreyBaseQuantities"]["GrossHeight"]
            elif UtilitiesIfc.findPset(ifcBldgStorey, "BaseQuantities", "Height") is not None:
                height = element.get_psets(ifcBldgStorey)["BaseQuantities"]["Height"]
            elif UtilitiesIfc.findPset(ifcBldgStorey, "Qto_BuildingStoreyBaseQuantities", "Height") is not None:
                height = element.get_psets(ifcBldgStorey)["Qto_BuildingStoreyBaseQuantities"]["Height"]
            elif UtilitiesIfc.findPset(ifcBldgStorey, "BaseQuantities", "NetHeight") is not None:
                height = element.get_psets(ifcBldgStorey)["BaseQuantities"]["NetHeight"]
            elif UtilitiesIfc.findPset(ifcBldgStorey, "Qto_BuildingStoreyBaseQuantities",
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
        elif UtilitiesIfc.findPset(ifcBuilding, "BaseQuantities", "GrossHeight") is not None:
            height = element.get_psets(ifcBuilding)["BaseQuantities"]["GrossHeight"]
        elif UtilitiesIfc.findPset(ifcBuilding, "Qto_BuildingBaseQuantities", "GrossHeight") is not None:
            height = element.get_psets(ifcBuilding)["Qto_BuildingBaseQuantities"]["GrossHeight"]
        elif UtilitiesIfc.findPset(ifcBuilding, "BaseQuantities", "Height") is not None:
            height = element.get_psets(ifcBuilding)["BaseQuantities"]["Height"]
        elif UtilitiesIfc.findPset(ifcBuilding, "Qto_BuildingBaseQuantities", "Height") is not None:
            height = element.get_psets(ifcBuilding)["Qto_BuildingBaseQuantities"]["Height"]
        elif UtilitiesIfc.findPset(ifcBuilding, "BaseQuantities", "NetHeight") is not None:
            height = element.get_psets(ifcBuilding)["BaseQuantities"]["NetHeight"]
        elif UtilitiesIfc.findPset(ifcBuilding, "Qto_BuildingBaseQuantities", "NetHeight") is not None:
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
        ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="BASESLAB")
        if len(ifcSlabs) == 0:
            ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="FLOOR")
            # Wenn Grundfläche nicht vorhanden
            if len(ifcSlabs) == 0:
                self.parent.dlg.log(self.tr(
                    u"Due to the missing baseslab and building/storeys attributes, no building height can be calculated"))
                return None

        # Dächer
        ifcRoofs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="ROOF")
        if len(ifcRoofs) == 0:
            ifcRoofs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcRoof", result=[])
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
        elif UtilitiesIfc.findPset(ifcBuilding, "Pset_Address") is not None:
            ifcAddress = UtilitiesIfc.findPset(ifcBuilding, "Pset_Address")
        elif ifcSite.SiteAddress is not None:
            ifcAddress = ifcSite.SiteAddress
        elif UtilitiesIfc.findPset(ifcSite, "Pset_Address") is not None:
            ifcAddress = UtilitiesIfc.findPset(ifcSite, "Pset_Address")
        else:
            self.parent.dlg.log(self.tr(u'No address details existing'))
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

    def convertLoD0FootPrint(self, ifcBuilding, chBldg):
        """ Konvertieren der Grundfläche von IFC zu CityGML

        Args:
            ifcBuilding: Das Gebäude, aus dem die Grundfläche entnommen werden soll
            chBldg: XML-Element an dem die Grundfläche angefügt werden soll
        """
        # IFC-Elemente
        ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="BASESLAB")
        if len(ifcSlabs) == 0:
            ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="FLOOR")
            # Wenn keine Grundfläche vorhanden
            if len(ifcSlabs) == 0:
                self.parent.dlg.log(self.tr(u"Due to the missing baseslab, no FootPrint geometry can be calculated"))
                return

        # Geometrie
        geometry = self.calcPlane(ifcSlabs)
        if geometry is not None:
            self.geom.AddGeometry(geometry)
            geomXML = UtilitiesGeom.geomToGml(geometry)
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
        ifcRoofs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="ROOF")
        if len(ifcRoofs) == 0:
            ifcRoofs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcRoof", result=[])
            # Wenn kein Dach vorhanden
            if len(ifcRoofs) == 0:
                self.parent.dlg.log(self.tr(u"Due to the missing roof, no RoofEdge geometry can be calculated"))
                return

        # Geometrie
        geometry = self.calcPlane(ifcRoofs)
        self.geom.AddGeometry(geometry)
        geomXML = UtilitiesGeom.geomToGml(geometry)
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
        if geometries.GetGeometryCount() > 1 or geometry.GetGeometryName() != "POLYGON":
            geometry = geometries.UnionCascaded()

            # Wenn immer noch mehr als eine Geometrie: Union auf Buffer
            if geometry.GetGeometryCount() > 1 or geometry.GetGeometryName() != "POLYGON":
                bufferList = [0.001, 0.005, 0.01, 0.05, 0.1]
                i = 0
                for i in range(0, len(bufferList)):
                    geometriesBuffer = ogr.Geometry(ogr.wkbMultiPolygon)
                    for j in range(0, geometries.GetGeometryCount()):
                        g = geometries.GetGeometryRef(j)
                        gBuffer = g.Buffer(bufferList[i], quadsecs=0)
                        geometriesBuffer.AddGeometry(gBuffer)
                    geometry = geometriesBuffer.UnionCascaded()
                    if geometry.GetGeometryCount() == 1 and geometry.GetGeometryName() == "POLYGON":
                        break

                # Wenn weiterhin mehr als eine Geometrie: Fehlermeldung und Abbruch
                if geometry.GetGeometryCount() > 1 or geometry.GetGeometryName() != "POLYGON":
                    self.parent.dlg.log(self.tr(
                        u'Due to non-meter-metrics or the lack of topology, no lod0 geometry can be calculated'))
                    return None

                # Wenn nur noch eine Geometrie: Höhe wieder hinzufügen
                else:
                    geometry.Set3D(True)
                    wkt = geometry.ExportToWkt()
                    wkt = wkt.replace(" 0,", " " + str(height) + ",").replace(" 0)", " " + str(height) + ")")
                    geometry = ogr.CreateGeometryFromWkt(wkt)
                    geometry = UtilitiesGeom.simplify(geometry, 0.1, 0.05)
                    geometry = UtilitiesGeom.buffer2D(geometry, -bufferList[i])

        geometry = UtilitiesGeom.simplify(geometry, 0.1, 0.05)
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
        ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="BASESLAB")
        if len(ifcSlabs) == 0:
            ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="FLOOR")
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
                geomXML = UtilitiesGeom.geomToGml(geometry)
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

    def convertLoD2BldgBound(self, ifcBuilding, chBldg, height):
        """ Konvertieren des erweiterten Gebäudeumrisses von IFC zu CityGML in Level of Detail (LoD) 2

        Args:
            ifcBuilding: Das Gebäude, aus dem der Gebäudeumriss entnommen werden soll
            chBldg: XML-Element an dem der Gebäudeumriss angefügt werden soll
            height: Gebäudehöhe
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

        # Berechnung Grundfläche
        geomBase = self.calcPlane(ifcSlabs)
        if geomBase is None:
            return []

        # IFC-Elemente des Daches
        ifcRoofs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="ROOF")
        ifcRoofs += UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcRoof", result=[])
        if len(ifcRoofs) == 0:
            self.parent.dlg.log(self.tr(
                u"Due to the missing roof, no building geometry can be calculated"))
            return None

        # Berechnung
        geomRoofs = self.extractRoofs(ifcRoofs)
        geomWalls, geomRoofsNew = self.calcLoD2Walls(geomBase, geomRoofs, height)
        geomWallsR, geomRoofs = self.calcLoD2RoofWalls(geomRoofs + geomRoofsNew)
        geomRoofs = self.calcLoD2Roofs(geomRoofs, geomBase)
        geomWalls += self.checkLoD2RoofWalls(geomWallsR, geomRoofs)
        geomRoofs = UtilitiesGeom.simplify(geomRoofs, 0.01, 0.05)

        # Geometrie
        links = []
        if geomWalls is not None and len(geomRoofs) > 0 and geomRoofs is not None and len(geomRoofs) > 0:
            link = self.setElement(chBldg, geomBase, "GroundSurface", 2)
            links.append(link)
            for geomRoof in geomRoofs:
                link = self.setElement(chBldg, geomRoof, "RoofSurface", 2)
                links.append(link)
            for geomWall in geomWalls:
                link = self.setElement(chBldg, geomWall, "WallSurface", 2)
                links.append(link)
        return links

    def setElement(self, chBldg, geometry, type, lod):
        """ Setzen eines CityGML-Objekts

        Args:
            chBldg: XML-Element an dem das Objekt angefügt werden soll
            geometry: Die Geometrie des Objekts
            type: Der Typ des Objekts
            lod: Level of Detail (LoD)
        """
        self.geom.AddGeometry(geometry)

        # XML-Struktur
        chBldgBB = etree.SubElement(chBldg, QName(XmlNs.bldg, "boundedBy"))
        chBldgS = etree.SubElement(chBldgBB, QName(XmlNs.bldg, type))
        chBldgS.set(QName(XmlNs.gml, "id"), "GML_" + str(uuid.uuid4()))
        chBldgSurfSMS = etree.SubElement(chBldgS, QName(XmlNs.bldg, "lod" + str(lod) + "MultiSurface"))
        chBldgMS = etree.SubElement(chBldgSurfSMS, QName(XmlNs.bldg, "MultiSurface"))
        chBldgSM = etree.SubElement(chBldgMS, QName(XmlNs.bldg, "surfaceMember"))

        # Geometrie
        geomXML = UtilitiesGeom.geomToGml(geometry)
        chBldgSM.append(geomXML)

        # GML-ID
        chBldgPol = chBldgSM[0]
        gmlId = "PolyID" + str(uuid.uuid4())
        chBldgPol.set(QName(XmlNs.gml, "id"), gmlId)

        return gmlId

    def extractRoofs(self, ifcRoofs):
        """ Extrahieren der Geometrien von Dächern aus IFC

        Args:
            ifcRoofs: Die IFC-Dächer

        Returns:
            Dächer-Geometrien als Liste
        """
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
            roofs.append(finalRoof)

        return roofs

    def calcLoD2Walls(self, base, roofs, height):
        """ Berechnen der Grundwände in Level of Detail (LoD) 2

        Args:
            base: Die Geometrie der Grundfläche
            roofs: Die Geometrien der Dächer als Liste
            height: Die Gebäudehöhe

        Returns:
            Die berechneten Wand-Geometrien als Liste
            Neu erstellte Dach-Geometrien als Liste
        """
        walls, roofPoints, wallsWORoof, missingRoof = [], [], [], []

        # Über die Eckpunkte der Grundfläche Wände hochziehen
        ringBase = base.GetGeometryRef(0)
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

                # 2D-Schnitt
                intersect = geomWall.Intersection(roof)
                if not intersect.IsEmpty():
                    ipt1, ipt2 = intersect.GetPoint(0), intersect.GetPoint(1)

                    # Schnittgerade über Ebenenschnitt (damit die Höhen korrekt sind)
                    rring = roof.GetGeometryRef(0)
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
                                self.parent.dlg.log(
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

                # Wenn der Endpunkt keinen Schnitt hat: Fehlendes Dach auf dem letzten Teil der Wand
                if lastPoint[0] != pt2[0] or lastPoint[1] != pt2[1]:
                    self.parent.dlg.log(self.tr(u'Due to a missing roof, a wall height can\'t be calculated!'))

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
                self.parent.dlg.log(self.tr(u'Due to a missing roof, a wall height can\'t be calculated!'))
                wallsWORoof.append([pt1, pt2])

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
                        roofsNew.append(geomRoof)

        return walls, roofsNew

    # noinspection PyMethodMayBeStatic
    def calcLoD2Roofs(self, roofsIn, base):
        """ Anpassen der Dächer, u.a. auf die Grundfläche und überschneidende Dächer in Level of Detail (LoD) 2

        Args:
            roofsIn: Die Geometrien der Dächer als Liste
            base: Die Geometrie der Grundfläche

        Returns:
            Die berechneten Wände als Liste
        """
        roofs = []

        # Alle Dächer überprüfen
        for roofIn in roofsIn:
            if roofIn is None:
                continue

            # Mit Grundfläche verschneiden
            intersection = roofIn.Intersection(base)
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
                    roofs.append(geomRoof)
        return roofs

    # noinspection PyMethodMayBeStatic
    def calcLoD2RoofWalls(self, roofs):
        """ Berechnen von Wänden zwischen zwei Dächern, die nicht bereits über die Grundfläche erstellt wurden

        Args:
            roofs: Die Geometrien der Dächer als Liste

        Returns:
            Die berechneten neuen Wände als Liste
            Die angepassten Dächer als Liste
        """
        roofsOut = roofs.copy()
        walls, wallsLine = [], []

        # Alle Dächer miteinander auf Schnitt prüfen
        for i in range(0, len(roofs)):
            roof1 = roofs[i]
            for j in range(i + 1, len(roofs)):
                roof2 = roofs[j]
                if roof1.Intersects(roof2):
                    intersect = roof1.Intersection(roof2)
                    if intersect is not None and intersect.GetGeometryName() == "LINESTRING" and not intersect.IsEmpty():
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
                            geomRoof = roofsOut[j]
                        else:
                            geomRoof = roofsOut[i]

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
                            roofsOut[j] = geomRoofOut
                        else:
                            roofsOut[i] = geomRoofOut

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

        return walls, roofsOut

    # noinspection PyMethodMayBeStatic
    def checkLoD2RoofWalls(self, wallsIn, roofs):
        """ Überprüfen und ggf. Aussortieren der neu erstellten Wand-Geometrien

        Args:
            wallsIn: Die Wand-Geometrien, die überprüft werden sollen, als Liste
            roofs: Die Dach-Geometrien als Liste

        Returns:
            Die überprüften Wand-Geometrien als Liste
        """
        wallsChecked = []

        # Wände mit Dächern verschneiden
        for wall in wallsIn:
            anyInt = False
            for roof in roofs:
                intersect = wall.Intersection(roof)
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
            if anyInt:
                wall = UtilitiesGeom.simplify(wall, 0.01, 0.05)
                wallsChecked.append(wall)

        wallsOut = UtilitiesGeom.union3D(wallsChecked)
        return wallsOut

    # noinspection PyMethodMayBeStatic
    def convertLoDSolid(self, chBldg, links, lod):
        """ Angabe der Gebäudegeometrie als XLinks zu den Bounds

        Args:
            chBldg: XML-Element an dem der Gebäudeumriss angefügt werden soll
            links: Zu nutzende XLinks
            lod: Level of Detail (LoD)
        """
        if links is not None and len(links) > 0:
            # XML-Struktur
            chBldgSolid = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod" + str(lod) + "Solid"))
            chBldgSolidSol = etree.SubElement(chBldgSolid, QName(XmlNs.gml, "Solid"))
            chBldgSolidExt = etree.SubElement(chBldgSolidSol, QName(XmlNs.gml, "exterior"))
            chBldgSolidCS = etree.SubElement(chBldgSolidExt, QName(XmlNs.gml, "CompositeSurface"))
            for link in links:
                chBldgSolidSM = etree.SubElement(chBldgSolidCS, QName(XmlNs.gml, "surfaceMember"))
                chBldgSolidSM.set(QName(XmlNs.xlink, "href"), link)

    def convertLoD3BldgBound(self, ifcBuilding, chBldg):
        """ Konvertieren des erweiterten Gebäudeumrisses von IFC zu CityGML in Level of Detail (LoD) 3

        Args:
            ifcBuilding: Das Gebäude, aus dem der Gebäudeumriss entnommen werden soll
            chBldg: XML-Element an dem der Gebäudeumriss angefügt werden soll
        """
        # Berechnung
        print("Start")
        bases, basesOrig = self.calcLoD3Bases(ifcBuilding)
        print("nach Bases")
        #roofs, roofsOrig = self.calcLoD3Roofs(ifcBuilding)
        #print("nach Roofs")
        #walls = self.calcLoD3Walls(ifcBuilding)
        #print("nach Walls")
        #openings = self.calcLoD3Openings(ifcBuilding, "ifcDoor")
        #openings += self.calcLoD3Openings(ifcBuilding, "ifcWindow")
        #roofs, walls = self.assignOpenings(openings, roofs, walls)
        #walls = self.adjustWallOpenings(walls)
        #walls = self.adjustWallSize(walls, bases, roofs, basesOrig, roofsOrig)

        # Geometrie
        links = []
        for base in bases:
            links += self.setElementGroup(chBldg, base[0], "GroundSurface", 3, name=base[1], openings=base[2])
        #for roof in roofs:
        #    links += self.setElementGroup(chBldg, roof[0], "RoofSurface", 3, name=roof[1], openings=roof[2])
        #for wall in walls:
        #    links += self.setElementGroup(chBldg, wall[0], "WallSurface", 3, name=wall[1], openings=wall[2])
        return links

    def setElementGroup(self, chBldg, geometries, type, lod, name, openings):
        """ Setzen eines CityGML-Objekts, bestehend aus mehreren Geometrien

        Args:
            chBldg: XML-Element an dem das Objekt angefügt werden soll
            geometries: Die Geometrien des Objekts
            type: Der Typ des Objekts
            lod: Level of Detail (LoD)
            name: Name der Oberfläche
                default: None
            openings: Öffnungen des Objektes
                default: []
        """
        for geometry in geometries:
            self.geom.AddGeometry(geometry)

        # XML-Struktur
        chBldgBB = etree.SubElement(chBldg, QName(XmlNs.bldg, "boundedBy"))
        chBldgS = etree.SubElement(chBldgBB, QName(XmlNs.bldg, type))
        chBldgS.set(QName(XmlNs.gml, "id"), "GML_" + str(uuid.uuid4()))

        # Name
        if name is not None:
            chBldgSName = etree.SubElement(chBldgS, QName(XmlNs.gml, "name"))
            chBldgSName.text = name

        # MultiSurface
        chBldgSurfSMS = etree.SubElement(chBldgS, QName(XmlNs.bldg, "lod" + str(lod) + "MultiSurface"))
        chBldgMS = etree.SubElement(chBldgSurfSMS, QName(XmlNs.gml, "MultiSurface"))
        chBldgSM = etree.SubElement(chBldgMS, QName(XmlNs.gml, "surfaceMember"))
        chBldgCS = etree.SubElement(chBldgSM, QName(XmlNs.gml, "CompositeSurface"))
        gmlId = "PolyID" + str(uuid.uuid4())
        chBldgCS.set(QName(XmlNs.gml, "id"), gmlId)
        gmlIds = [gmlId]

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
        for opening in openings:
            chBldgSurfSO = etree.SubElement(chBldgS, QName(XmlNs.bldg, "opening"))
            name = "Door" if opening[2] == "ifcDoor" else "Window"
            chBldgSurfSOE = etree.SubElement(chBldgSurfSO, QName(XmlNs.bldg, name))
            gmlId = "PolyID" + str(uuid.uuid4())
            chBldgSurfSOE.set(QName(XmlNs.gml, "id"), gmlId)
            if opening[1] is not None:
                chBldgSurfSOName = etree.SubElement(chBldgSurfSOE, QName(XmlNs.gml, "name"))
                chBldgSurfSOName.text = opening[1]
            chBldgSurfSOMS = etree.SubElement(chBldgSurfSOE, QName(XmlNs.bldg, "lod" + str(lod) + "MultiSurface"))
            chBldgOMS = etree.SubElement(chBldgSurfSOMS, QName(XmlNs.gml, "MultiSurface"))
            chBldgOSM = etree.SubElement(chBldgOMS, QName(XmlNs.gml, "surfaceMember"))
            chBldgOCS = etree.SubElement(chBldgOSM, QName(XmlNs.gml, "CompositeSurface"))
            gmlId = "PolyID" + str(uuid.uuid4())
            chBldgOCS.set(QName(XmlNs.gml, "id"), gmlId)
            gmlIds.append(gmlId)
            for geometry in opening[0]:
                chBldgOCSSM = etree.SubElement(chBldgOCS, QName(XmlNs.gml, "surfaceMember"))
                geomXML = UtilitiesGeom.geomToGml(geometry)
                chBldgOCSSM.append(geomXML)

                # GML-ID
                chBldgPol = chBldgOCSSM[0]
                gmlIdPoly = "PolyID" + str(uuid.uuid4())
                chBldgPol.set(QName(XmlNs.gml, "id"), gmlIdPoly)

        return gmlIds

    # noinspection PyMethodMayBeStatic
    def calcLoD3Bases(self, ifcBuilding):
        """ Berechnen der Grundfläche in Level of Detail (LoD) 3
        
        Args:
            ifcBuilding: Das Gebäude, aus dem die Grundflächen entnommen werden sollen

        Returns:
            Die berechneten Grundflächen-Geometrien als Liste
        """
        bases, baseNames, basesOrig = [], [], []

        # IFC-Elemente der Grundfläche
        ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="BASESLAB")
        if len(ifcSlabs) == 0:
            ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="FLOOR")
            # Wenn keine Grundfläche vorhanden
            if len(ifcSlabs) == 0:
                self.parent.dlg.log(self.tr(u"Due to the missing baseslab, it will also be missing in CityGML"))
                return []

        # Namen der Grundflächen heraussuchen
        for ifcSlab in ifcSlabs:
            baseNames.append(ifcSlab.Name)

        #ifcSlabs = [ifcSlabs[1]]

        for i in range(0, len(ifcSlabs)):
            ifcSlab = ifcSlabs[i]
            settings = ifcopenshell.geom.settings()
            settings.set(settings.USE_WORLD_COORDS, True)
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

            bases.append([finalSlab, baseNames[i], []])
            basesOrig.append(slabGeom)

        if len(bases) > 0:
            bases.sort(key=lambda elem: (elem[0][0].GetGeometryRef(0).GetPoint(0)[2]))

        for i in range(1, len(bases)):
            base = bases[i][0][0]
            baseLast = bases[i-1][0][0]
            print(base)
            print(baseLast)
            print(baseLast.Intersection(base))

        return bases, basesOrig

    # noinspection PyMethodMayBeStatic
    def calcLoD3Roofs(self, ifcBuilding):
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

            roofs.append([finalRoof, roofNames[i], []])
            roofsOrig.append(roofGeom)

        return roofs, roofsOrig

    # noinspection PyMethodMayBeStatic
    def calcLoD3Walls(self, ifcBuilding):
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

        # Geometrie
        for i in range(0, len(ifcWallsExt)):
            ifcWall = ifcWallsExt[i]
            settings = ifcopenshell.geom.settings()
            settings.set(settings.USE_WORLD_COORDS, True)
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
            # wallGeom = UtilitiesGeom.simplify(wallGeom, 0.001, 0.001)
            walls.append([wallGeom, wallNames[i], []])
        return walls

    def calcLoD3Openings(self, ifcBuilding, type):
        """ Berechnen der Öffnungen (Türen und Fenster) in Level of Detail (LoD) 3

        Args:
            ifcBuilding: Das Gebäude, aus dem die Öffnungen entnommen werden sollen
            type: Öffnungs-Typ (ifcDoor oder IfcWindow)

        Returns:
            Die berechneten Öffnungs-Geometrien als Liste
        """
        openings = []
        openingNames = []

        # IFC-Elemente der Öffnungen
        ifcOpenings = UtilitiesIfc.findElement(self.ifc, ifcBuilding, type, result=[])

        # Heraussuchen der Außenöffnungen
        ifcOpeningsExt = []
        ifcRelSpaceBoundaries = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcRelSpaceBoundary", result=[])
        psetCommon = "Pset_DoorCommon" if type == "ifcDoor" else "Pset_WindowCommon"
        for ifcOpening in ifcOpenings:
            extCount, intCount = 0, 0
            for ifcRelSpaceBoundary in ifcRelSpaceBoundaries:
                relElem = ifcRelSpaceBoundary.RelatedBuildingElement
                if relElem == ifcOpening:
                    if ifcRelSpaceBoundary.InternalOrExternalBoundary == "EXTERNAL":
                        extCount += 1
                    elif ifcRelSpaceBoundary.InternalOrExternalBoundary == "INTERNAL":
                        intCount += 1
            if extCount > 0:
                ifcOpeningsExt.append(ifcOpening)
            elif intCount == 0 and UtilitiesIfc.findPset(ifcOpening, psetCommon, "IsExternal"):
                ifcOpeningsExt.append(ifcOpening)

        # Namen der Öffnungen heraussuchen
        for ifcOpening in ifcOpeningsExt:
            openingNames.append(ifcOpening.Name)

        # Geometrie
        for i in range(0, len(ifcOpeningsExt)):
            ifcOpening = ifcOpeningsExt[i]
            settings = ifcopenshell.geom.settings()
            settings.set(settings.USE_WORLD_COORDS, True)
            shape = ifcopenshell.geom.create_shape(settings, ifcOpening)
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
            geometries, sizes = [], []
            for grVerts in grVertsList:
                # Polygon aus Ring aus Punkten erstellen
                geometry = ogr.Geometry(ogr.wkbPolygon)
                ring = ogr.Geometry(ogr.wkbLinearRing)
                for grVert in grVerts:
                    ring.AddPoint(grVert[0], grVert[1], grVert[2])
                # Seitenlängen merken
                r1 = math.sqrt((grVerts[1][0] - grVerts[0][0]) ** 2 + (grVerts[1][1] - grVerts[0][1]) ** 2 + (
                        grVerts[1][2] - grVerts[0][2]) ** 2)
                r2 = math.sqrt((grVerts[2][0] - grVerts[0][0]) ** 2 + (grVerts[2][1] - grVerts[0][1]) ** 2 + (
                        grVerts[2][2] - grVerts[0][2]) ** 2)
                sizes.append((r1 + r2))
                # Geometrie abschließen
                ring.CloseRings()
                geometry.AddGeometry(ring)
                geometries.append(geometry)

            # Herausfiltern von zu kleinen Flächen
            finalGeoms = []
            for j in range(0, len(geometries)):
                if sizes[j] > max(sizes) / 50:
                    finalGeoms.append(geometries[j])

            # Alle Flächen in der gleichen Ebene vereinigen
            openingGeom = UtilitiesGeom.union3D(finalGeoms)
            openings.append([openingGeom, openingNames[i], type])

        return openings

    # noinspection PyMethodMayBeStatic
    def assignOpenings(self, openings, roofs, walls):
        """ Anfügen der Öffnungen (Fenster & Türen) an die zugehörigen Wände oder Dächer in Level of Detail (LoD) 3

        Args:
            openings: Die anzufügenden Öffnungen (Fenster & Türen) als Liste
            roofs: Die Dächer, an die die Öffnungen angefügt werden sollen, als Liste
            walls: Die Wände, an die die Öffnungen angefügt werden sollen, als Liste

        Returns:
            Die angepassten Dächer als Liste
            Die angepassten Wände als Liste
        """
        for opening in openings:
            ptOp = opening[0][0].GetGeometryRef(0).GetPoint(0)

            # Wand bzw. Dach mit geringstem Abstand zur Öffnung berechnen
            minDist, minDistElem = sys.maxsize, None
            for roof in roofs:
                for geom in roof[0]:
                    for i in range(0, geom.GetGeometryCount()):
                        ring = geom.GetGeometryRef(i)
                        for j in range(0, ring.GetPointCount()):
                            pt = ring.GetPoint(j)
                            dist = math.sqrt((ptOp[0] - pt[0]) ** 2 + (ptOp[1] - pt[1]) ** 2 + (ptOp[2] - pt[2]) ** 2)
                            if dist < minDist:
                                minDist, minDistElem = dist, roof
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
            minDistElem[2].append(opening)
        return roofs, walls

    # noinspection PyMethodMayBeStatic
    def adjustWallOpenings(self, walls):
        """ Anpassen der Wände auf Grundlage der Dächer, Grundflächen und Öffnungen in Level of Detail (LoD) 3

        Args:
            walls: Die anzupassenden Wände als Liste

        Returns:
            Die angepassten Wände als Liste
        """
        for wall in walls:
            # Maximale Durchmesser der einzelnen Oberflächen heraussuchen
            dists = []
            for wallGeom in wall[0]:
                maxDist = -sys.maxsize
                ring = wallGeom.GetGeometryRef(0)
                for k in range(0, ring.GetPointCount()):
                    pt1 = ring.GetPoint(k)
                    for m in range(k + 1, ring.GetPointCount()):
                        pt2 = ring.GetPoint(m)
                        dist = math.sqrt((pt2[0] - pt1[0]) ** 2 + (pt2[1] - pt1[1]) ** 2 + (pt2[2] - pt1[2]) ** 2)
                        if dist > maxDist:
                            maxDist = dist
                dists.append(maxDist)

            # Größte Fläche als Außenfläche
            finalWall = [wall[0][dists.index(max(dists))]]

            # Wenn Öffnungen vorhanden sind: Entsprechende Begrenzungsflächen heraussuchen
            if len(wall[2]) != 0:
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
                        for k in range(0, len(opening[0])):
                            geomOpening = opening[0][k]
                            ringOpening = geomOpening.GetGeometryRef(0)

                            minDist = sys.maxsize
                            for o in range(0, wallRing.GetPointCount()):
                                ptO = wallRing.GetPoint(o)
                                for p in range(0, ringOpening.GetPointCount()):
                                    ptP = ringOpening.GetPoint(p)
                                    dist = math.sqrt(
                                        (ptP[0] - ptO[0]) ** 2 + (ptP[1] - ptO[1]) ** 2 + (ptP[2] - ptO[2]) ** 2)
                                    if dist < minDist:
                                        minDist = dist
                            if minDist <= 0.2:

                                # Höhen und Breiten der Öffnungen berechnen
                                maxZWall, minZWall, maxWidthWall = -sys.maxsize, sys.maxsize, -sys.maxsize
                                for m in range(0, wallRing.GetPointCount()):
                                    wallPt = wallRing.GetPoint(m)
                                    if wallPt[2] > maxZWall:
                                        maxZWall = wallPt[2]
                                    if wallPt[2] < minZWall:
                                        minZWall = wallPt[2]
                                    wallPtN = wallRing.GetPoint(
                                        m + 1) if m < wallRing.GetPointCount() - 1 else wallRing.GetPoint(0)
                                    width = math.sqrt((wallPtN[0] - wallPt[0]) ** 2 + (wallPtN[1] - wallPt[1]) ** 2)
                                    if width > maxWidthWall:
                                        maxWidthWall = width

                                # Höhen und Breiten der zu prüfenden Flächen berechnen
                                maxZOpen, minZOpen, maxWidthOpen = -sys.maxsize, sys.maxsize, -sys.maxsize
                                for n in range(0, len(opening[0])):
                                    geomOpen = opening[0][n]
                                    ringOpen = geomOpen.GetGeometryRef(0)
                                    for o in range(0, ringOpen.GetPointCount()):
                                        ptOpen = ringOpen.GetPoint(o)
                                        if ptOpen[2] > maxZOpen:
                                            maxZOpen = ptOpen[2]
                                        if ptOpen[2] < minZOpen:
                                            minZOpen = ptOpen[2]
                                        ptOpenN = ringOpen.GetPoint(
                                            o + 1) if o < ringOpen.GetPointCount() - 1 else ringOpen.GetPoint(0)
                                        width = math.sqrt((ptOpenN[0] - ptOpen[0]) ** 2 + (ptOpenN[1] - ptOpen[1]) ** 2)
                                        if width > maxWidthOpen:
                                            maxWidthOpen = width

                                # Übereinstimmung in Höhe und Breite prüfen
                                if minZWall > minZOpen - 0.01 and maxZWall < maxZOpen + 0.01 and maxWidthWall < maxWidthOpen + 0.01:
                                    openBounds[i].append([len(finalWall), wallGeom])
                                    finalWall.append(wallGeom)
                                    same = True
                                    break

                # Öffnungen durch eine gesamte Fläche darstellen
                # über alle Öffnungen der Wand iterieren
                for j in range(0, len(wall[2])):
                    opening = wall[2][j]

                    # Größte Fläche heraussuchen: Als Grundlage benutzen
                    maxArea, maxGeom = -sys.maxsize, None
                    minZG, maxZG = sys.maxsize, -sys.maxsize
                    for n in range(0, len(opening[0])):
                        geomOpen = opening[0][n]
                        ringOpen = geomOpen.GetGeometryRef(0)
                        minZ, maxZ, maxWidth = sys.maxsize, -sys.maxsize, -sys.maxsize
                        for o in range(0, ringOpen.GetPointCount()):
                            ptOpen = ringOpen.GetPoint(o)
                            if ptOpen[2] > maxZ:
                                maxZ = ptOpen[2]
                            if ptOpen[2] < minZ:
                                minZ = ptOpen[2]
                            ptOpenN = ringOpen.GetPoint(
                                o + 1) if o < ringOpen.GetPointCount() - 1 else ringOpen.GetPoint(0)
                            width = math.sqrt((ptOpenN[0] - ptOpen[0]) ** 2 + (ptOpenN[1] - ptOpen[1]) ** 2)
                            if width > maxWidth:
                                maxWidth = width
                        area = maxWidth * (maxZ - minZ)
                        if minZ < minZG:
                            minZG = minZ
                        if maxZ > maxZG:
                            maxZG = maxZ
                        if area > maxArea:
                            maxArea = area
                            maxGeom = ringOpen

                    # Nebeneinander liegende Flächen verschneiden
                    planeOpen = UtilitiesGeom.getPlane(maxGeom.GetPoint(0), maxGeom.GetPoint(1), maxGeom.GetPoint(2))
                    sLines = []
                    for openBound in openBounds[j]:
                        geom = openBound[1]
                        ring = geom.GetGeometryRef(0)
                        plane = UtilitiesGeom.getPlane(ring.GetPoint(0), ring.GetPoint(1), ring.GetPoint(2))
                        sLine = planeOpen.intersection(plane)[0]
                        sLines.append(sLine)
                    sPts = [[] for x in range(len(openBounds[j]))]
                    for n in range(0, len(sLines)):
                        o = 0 if n == len(sLines) - 1 else n + 1
                        sPt = sLines[n].intersection(sLines[o])
                        if len(sPt) != 0 and minZG - 0.1 < float(sPt[0][2]) < maxZG + 0.1:
                            sPts[n].append([float(sPt[0][0]), float(sPt[0][1]), float(sPt[0][2])])
                            sPts[o].append([float(sPt[0][0]), float(sPt[0][1]), float(sPt[0][2])])

                    # Schnittpunkte auswerten und in neue Geometrie als Eckpunkte setzen
                    newGeomOpen = ogr.Geometry(ogr.wkbPolygon)
                    newGeomRing = ogr.Geometry(ogr.wkbLinearRing)
                    for o in range(0, len(sPts)):

                        # Wenn zwei Schnittpunkte beim Wandstück
                        if len(sPts[o]) > 1:
                            nr = 1 if o == 0 else 0
                            newGeomRing.AddPoint(sPts[o][nr][0], sPts[o][nr][1], sPts[o][nr][2])

                        # Wenn nur 1 Schnittpunkt beim Wandstück
                        elif len(sPts[o]) == 1:
                            if o != 0:
                                newGeomRing.AddPoint(sPts[o][0][0], sPts[o][0][1], sPts[o][0][2])
                            geom = openBounds[j][o][1]
                            ring = geom.GetGeometryRef(0)
                            minZ, maxZ = sys.maxsize, -sys.maxsize
                            for p in range(0, ring.GetPointCount()):
                                if ring.GetPoint(p)[2] < minZ:
                                    minZ = ring.GetPoint(p)[2]
                                if ring.GetPoint(p)[2] > maxZ:
                                    maxZ = ring.GetPoint(p)[2]
                            if sPts[o][0][2] == minZ:
                                sPts[o].append([sPts[o][0][0], sPts[o][0][1], maxZ])
                                newGeomRing.AddPoint(sPts[o][0][0], sPts[o][0][1], maxZ)
                            elif sPts[o][0][2] == maxZ:
                                sPts[o].append([sPts[o][0][0], sPts[o][0][1], minZ])
                                newGeomRing.AddPoint(sPts[o][0][0], sPts[o][0][1], minZ)

                    # Geometrie abschließen und setzen
                    newGeomRing.CloseRings()
                    newGeomOpen.AddGeometry(newGeomRing)
                    opening[0] = [newGeomOpen]

                    # Wandflächen kürzen
                    for q in range(0, len(sPts)):
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
                                gradYSt = -1 if ptMid[0] - ptSt[0] == 0 else (ptMid[1] - ptSt[1]) / abs(
                                    ptMid[0] - ptSt[0])
                                gradYEnd = -1 if ptEnd[0] - ptMid[0] == 0 else (ptEnd[1] - ptMid[1]) / abs(
                                    ptEnd[0] - ptMid[0])
                                if gradYSt - tol < gradYEnd < gradYSt + tol:
                                    # Z-Steigung in Bezug auf X-Verlauf
                                    gradZSt = -1 if ptMid[0] - ptSt[0] == 0 else (ptMid[2] - ptSt[2]) / abs(
                                        ptMid[0] - ptSt[0])
                                    gradZEnd = -1 if ptEnd[0] - ptMid[0] == 0 else (ptEnd[2] - ptMid[2]) / abs(
                                        ptEnd[0] - ptMid[0])
                                    if gradZSt - tol < gradZEnd < gradZSt + tol:
                                        # Z-Steigung in Bezug auf Y-Verlauf
                                        gradYZSt = -1 if ptMid[1] - ptSt[1] == 0 else (ptMid[2] - ptSt[2]) / abs(
                                            ptMid[1] - ptSt[1])
                                        gradYZEnd = -1 if ptEnd[1] - ptMid[1] == 0 else (ptEnd[2] - ptMid[2]) / abs(
                                            ptEnd[1] - ptMid[1])
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

            wall[0] = finalWall
        return walls

    # noinspection PyMethodMayBeStatic
    def adjustWallSize(self, walls, bases, roofs, basesOrig, roofsOrig):
        """ Anpassen der Wände in Bezug auf die veränderten Grundflächen und Dächer in Level of Detail (LoD) 3

        Args:
            walls: Die anzupassenden Wände als Liste
            bases: Die Grundflächen, an die die Wände angepasst werden sollen, als Liste
            roofs: Die Dächer, an die die Wände angepasst werden sollen, als Liste
            basesOrig: Die originalen Grundflächen als Liste
            roofsOrig: Die originalen Dächer als Liste

        Returns:
            Die angepassten Wände als Liste
        """

        # Alle Wände durchgehen
        for i in range(0, len(walls)):
            wallGeom = walls[i][0][0]
            wallRing = wallGeom.GetGeometryRef(0)
            wallGeomTemp, wallRingTemp = ogr.Geometry(ogr.wkbPolygon), ogr.Geometry(ogr.wkbLinearRing)
            wallHoles, inHole, newWalls = [], False, []

            # Alle Eckpunkte der Wände durchgehen
            for j in range(0, wallRing.GetPointCount()):
                pt = wallRing.GetPoint(j)

                # HÖHE #
                # Gebufferte Punktgeometrie
                ptPolGeom, ptPolRing = ogr.Geometry(ogr.wkbPolygon), ogr.Geometry(ogr.wkbLinearRing)
                ptPolRing.AddPoint(pt[0] - 0.001, pt[1] - 0.001, pt[2])
                ptPolRing.AddPoint(pt[0] - 0.001, pt[1] + 0.001, pt[2])
                ptPolRing.AddPoint(pt[0] + 0.001, pt[1] + 0.001, pt[2])
                ptPolRing.AddPoint(pt[0] + 0.001, pt[1] - 0.001, pt[2])
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
                                # Prüfen, ob die Wandhöhe und Höhe der originalen Grundfläche/Dach in etwa gleich ist
                                origPlane = UtilitiesGeom.getPlane(origRing.GetPoint(0), origRing.GetPoint(1),
                                                                   origRing.GetPoint(2))
                                ptLine = Line(Point3D(pt[0], pt[1], pt[2] - 100), Point3D(pt[0], pt[1], pt[2] + 100))
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
                        break

                # ÖFFNUNGEN und GEOMETRIE #
                # Über alle Nebenwände und dessen Eckpunkte gehen
                opBound, pts = False, []
                for m in range(1, len(walls[i][0])):
                    wallOpGeom = walls[i][0][m]
                    wallOpRing = wallOpGeom.GetGeometryRef(0)
                    for n in range(0, wallOpRing.GetPointCount()):
                        wallOpPt = wallOpRing.GetPoint(n)
                        if wallOpPt == pt:
                            if inHole:
                                newN = wallOpRing.GetPointCount() - 2 if n == 0 else n-1
                                lastPt = wallOpRing.GetPoint(newN)
                            else:
                                nextPt = wallOpRing.GetPoint(n + 1)
                            opBound = True
                            break
                    if opBound:
                        break

                # Wenn Wandpunkt gleich zu einem Nebenwandpunkt
                if opBound:
                    # Bereits Teil der Öffnung: Punkt merken
                    if inHole:
                        wallHoles[len(wallHoles) - 1].append(pt)
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

            walls[i][0][0] = UtilitiesGeom.simplify(wallGeomTemp, 0.01, 0.01)

            # Neue Nebenwand hinzufügen
            for newWall in newWalls:
                walls[i][0].append(newWall)

        return walls
