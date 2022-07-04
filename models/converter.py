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
from qgis.core import QgsTask
from qgis.PyQt.QtCore import QCoreApplication

# Geo-Bibliotheken
from osgeo import ogr

# Plugin
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
        chBldg.set("id", "UUID_" + str(uuid.uuid4()))

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

        # Zur Geometrieliste hinzufügen und in GML konvertieren
        self.geom.AddGeometry(geometry)
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
        for i in range(ringBase.GetPointCount()-1, -1, -1):
            pt = ringBase.GetPoint(i)
            ringRoof.AddPoint(pt[0], pt[1], pt[2]+height)
        geomRoof.AddGeometry(ringRoof)
        geometries.append(geomRoof)

        # Wandflächen
        for i in range(0, ringBase.GetPointCount()-1):
            geomWall = ogr.Geometry(ogr.wkbPolygon)
            ringWall = ogr.Geometry(ogr.wkbLinearRing)
            pt1 = ringBase.GetPoint(i)
            pt2 = ringBase.GetPoint(i+1)
            ringWall.AddPoint(pt1[0], pt1[1], pt1[2])
            ringWall.AddPoint(pt1[0], pt1[1], pt1[2]+height)
            ringWall.AddPoint(pt2[0], pt2[1], pt2[2]+height)
            ringWall.AddPoint(pt2[0], pt2[1], pt2[2])
            ringWall.CloseRings()
            geomWall.AddGeometry(ringWall)
            geometries.append(geomWall)

        return geometries

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
