# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (09.09.2022)
 ***************************************************************************/
"""

#####

# Standard-Bibliotheken
import math
import uuid
from copy import deepcopy

# IFC-Bibliotheken
from ifcopenshell.util import element

# XML-Bibliotheken
from lxml import etree
# noinspection PyUnresolvedReferences
from lxml.etree import QName

# QGIS-Bibliotheken
from qgis.core import QgsTask

# Geo-Bibliotheken
from osgeo import ogr

# Plugin
from ..model.xmlns import XmlNs
from ..model.mapper import Mapper
from .utilitiesGeom import UtilitiesGeom
from .utilitiesIfc import UtilitiesIfc
from ..model.construction import Construction
from ..model.material import Material

#####


class EADEConverter(QgsTask):
    """ Model-Klasse zum Konvertieren von IFC-Dateien zur EnergyADE von CityGML """

    @staticmethod
    def convertWeatherData(ifcProject, ifcSite, chBldg, bbox):
        """ Konvertiert die Wetterdaten eines Grundstücks von IFC zu CityGML als Teil der Energy ADE

        Args:
            ifcProject: Das IFC-Projekt, aus dem die Wettereinheiten entnommen werden sollen
            ifcSite: Das IFC-Grundtück, aus dem die Wetterdaten entnommen werden sollen
            chBldg: XML-Element, an dem die Wetterdaten angefügt werden sollen
            bbox: BoundingBox, aus dem die Position der Wettermessungen entnommen werden soll
        """
        if UtilitiesIfc.findPset(ifcSite, "Pset_SiteWeather") is not None:
            # Temperatur
            maxTemp = element.get_psets(ifcSite)["Pset_SiteWeather"]["MaxAmbientTemp"]
            minTemp = element.get_psets(ifcSite)["Pset_SiteWeather"]["MinAmbientTemp"]

            # Temperatureinheit
            unitName = "C"
            if ifcProject.UnitsInContext is not None:
                units = ifcProject.UnitsInContext.Units
                for unit in units:
                    if unit.is_a('IfcSIUnit') and unit.UnitType == "THERMODYNAMICTEMPERATUREUNIT":
                        unitName = "K" if unit.Name == "KELVIN" else "C"

            # XML-Struktur
            chwd = etree.SubElement(chBldg, QName(XmlNs.energy, "weatherData"))
            chWD = etree.SubElement(chwd, QName(XmlNs.energy, "WeatherData"))

            # Datentyp
            chWDType = etree.SubElement(chWD, QName(XmlNs.energy, "weatherDataType"))
            chWDType.text = "airTemperature"

            # Werte
            chWDValues = etree.SubElement(chWD, QName(XmlNs.energy, "values"))
            chWDTimeSeries = etree.SubElement(chWDValues, QName(XmlNs.energy, "RegularTimeSeries"))
            chWdTsVarProp = etree.SubElement(chWDTimeSeries, QName(XmlNs.energy, "variableProperties"))
            chWdTsTvp = etree.SubElement(chWdTsVarProp, QName(XmlNs.energy, "TimeValuesProperties"))
            chWdTsTvpAm = etree.SubElement(chWdTsTvp, QName(XmlNs.energy, "acqusitionMethod"))
            chWdTsTvpAm.text = "unknown"
            chWdTsTvpIt = etree.SubElement(chWdTsTvp, QName(XmlNs.energy, "interpolationType"))
            chWdTsTvpIt.text = "continuous"
            chWdTsTvpSource = etree.SubElement(chWdTsTvp, QName(XmlNs.energy, "source"))
            chWdTsTvpSource.text = "IFC building model"
            chWdTsTvpTd = etree.SubElement(chWdTsTvp, QName(XmlNs.energy, "thematicDescription"))
            chWdTsTvpTd.text = "ambient temperature"

            chWdTsTempExt = etree.SubElement(chWDTimeSeries, QName(XmlNs.energy, "temporalExtent"))
            chWdTsTimePer = etree.SubElement(chWdTsTempExt, QName(XmlNs.energy, "TimePeriod"))
            chWdTsTpBegin = etree.SubElement(chWdTsTimePer, QName(XmlNs.energy, "beginPosition"))
            chWdTsTpBegin.text = "2020-01-01T00:00:00"
            chWdTsTpEnd = etree.SubElement(chWdTsTimePer, QName(XmlNs.energy, "endPosition"))
            chWdTsTpEnd.text = "2025-12-31T23:59:59"

            chWdTsTimeInt = etree.SubElement(chWDTimeSeries, QName(XmlNs.energy, "timeInterval"))
            chWdTsTimeInt.set("unit", "month")
            chWdTsTimeInt.text = "6"

            chWdTsValues = etree.SubElement(chWDTimeSeries, QName(XmlNs.energy, "values"))
            chWdTsValues.set("uom", unitName)
            values, countYears = "", 6
            for i in range(0, countYears):
                values += (str(minTemp) + " " + str(maxTemp) + " ")
            chWdTsValues.text = values

            # Position
            chWDPos = etree.SubElement(chWD, QName(XmlNs.energy, "position"))
            chWDPosPt = etree.SubElement(chWDPos, QName(XmlNs.energy, "Point"))
            chWDPosPtPos = etree.SubElement(chWDPosPt, QName(XmlNs.energy, "pos"))
            meanX, meanY, meanZ = (bbox[0] + bbox[1]) / 2, (bbox[2] + bbox[3]) / 2, (bbox[4] + bbox[5]) / 2
            chWDPosPtPos.text = str(meanX) + " " + str(meanY) + " " + str(meanZ)

    @staticmethod
    def convertBldgAttr(ifc, ifcBuilding, chBldg, bbox, footPrint):
        """ Konvertiert die Gebäudeattribute für die Energy ADE

        Args:
            ifc: IFC-Datei
            ifcBuilding: IFC-Gebäude, aus dem die Attribute entnommen werden sollen
            chBldg: XML-Objekt, an das die Gebäudeattribute angehängt werden soll
            bbox: Die Bounding Box des Gebäudes
            footPrint: Der Grundriss des Gebäudes
        """

        # BuildingType
        type = None
        for child in chBldg:
            if "class" in child.tag:
                type = child.text
                break
        if type == "1000":
            bldgTypeCode = None
            if UtilitiesIfc.findPset(ifcBuilding, "Pset_BuildingCommon", "OccupancyType") is not None:
                bldgType = element.get_psets(ifcBuilding)["Pset_BuildingCommon"]["OccupancyType"]
                if bldgType in Mapper.bldgTypeDict:
                    bldgTypeCode = str(Mapper.bldgTypeDict[bldgType])
            if bldgTypeCode is None and UtilitiesIfc.findPset(ifcBuilding, "Pset_BuildingUse",
                                                              "MarketCategory") is not None:
                bldgType = element.get_psets(ifcBuilding)["Pset_BuildingUse"]["MarketCategory"]
                if bldgType in Mapper.bldgTypeDict:
                    bldgTypeCode = str(Mapper.bldgTypeDict[bldgType])
            if bldgTypeCode is None and ifcBuilding.ObjectType is not None:
                bldgType = ifcBuilding.ObjectType
                if bldgType in Mapper.bldgTypeDict:
                    bldgTypeCode = str(Mapper.bldgTypeDict[bldgType])
            if bldgTypeCode is None and ifcBuilding.Description is not None:
                bldgType = ifcBuilding.Description
                if bldgType in Mapper.bldgTypeDict:
                    bldgTypeCode = str(Mapper.bldgTypeDict[bldgType])
            if bldgTypeCode is None and ifcBuilding.LongName is not None:
                bldgType = ifcBuilding.LongName
                if bldgType in Mapper.bldgTypeDict:
                    bldgTypeCode = str(Mapper.bldgTypeDict[bldgType])
            if bldgTypeCode is None and ifcBuilding.Name is not None:
                bldgType = ifcBuilding.Name
                if bldgType in Mapper.bldgTypeDict:
                    bldgTypeCode = str(Mapper.bldgTypeDict[bldgType])
            if bldgTypeCode is not None:
                chBldgType = etree.SubElement(chBldg, QName(XmlNs.energy, "buildingType"))
                chBldgType.text = bldgTypeCode

        # ConstructionWeight
        ifcWalls = UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcWall", result=[])
        ifcWallsExt = []
        ifcRelSpaceBoundaries = UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcRelSpaceBoundary", result=[])
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
        if len(ifcWallsExt) != 0:
            thicknesses = []
            for ifcWall in ifcWallsExt:
                rels = ifc.get_inverse(ifcWall)
                for rel in rels:
                    if rel.is_a('IfcRelAssociatesMaterial') and ifcWall in rel.RelatedObjects:
                        if rel.RelatingMaterial is not None and rel.RelatingMaterial.is_a("IfcMaterialLayerSetUsage"):
                            ifcMLSU = rel.RelatingMaterial
                            if ifcMLSU.ForLayerSet is not None:
                                ifcMLS = ifcMLSU.ForLayerSet
                                if ifcMLS.MaterialLayers is not None:
                                    thicknessAll = 0
                                    for layer in ifcMLS.MaterialLayers:
                                        thickness = layer.LayerThickness
                                        factor = 1
                                        if layer.Material is not None:
                                            material = layer.Material
                                            if material.Category is not None:
                                                matCat = material.Category
                                                if matCat in Mapper.layerCatDict:
                                                    factor = str(Mapper.layerCatDict[matCat])
                                        thicknessAll += (thickness * factor)
                                    thicknesses.append(thicknessAll)

            if len(thicknesses) != 0:
                thickness, thisKey = sum(thicknesses) / len(thicknesses), None
                for key in Mapper.thicknessCatDict.keys():
                    if thickness > key:
                        thisKey = key
                constrWeight = str(Mapper.thicknessCatDict[thisKey])
                chBldgConstr = etree.SubElement(chBldg, QName(XmlNs.energy, "constructionWeight"))
                chBldgConstr.text = constrWeight

        # Volume
        grossVol, netVol = None, None
        if UtilitiesIfc.findPset(ifcBuilding, "Qto_BuildingBaseQuantities", "GrossVolume") is not None:
            grossVol = element.get_psets(ifcBuilding)["Qto_BuildingBaseQuantities"]["GrossVolume"]
        if UtilitiesIfc.findPset(ifcBuilding, "Qto_BuildingBaseQuantities", "NetVolume") is not None:
            netVol = element.get_psets(ifcBuilding)["Qto_BuildingBaseQuantities"]["NetVolume"]
        if grossVol is None and UtilitiesIfc.findPset(ifcBuilding, "Qto_BodyGeometryValidation",
                                                      "GrossVolume") is not None:
            grossVol = element.get_psets(ifcBuilding)["Qto_BodyGeometryValidation"]["GrossVolume"]
        if netVol is None and UtilitiesIfc.findPset(ifcBuilding, "Qto_BodyGeometryValidation", "NetVolume") is not None:
            netVol = element.get_psets(ifcBuilding)["Qto_BodyGeometryValidation"]["NetVolume"]
        if grossVol is None and netVol is None:
            height = None
            for child in chBldg:
                if "measuredHeight" in child.tag:
                    height = child.text
                    break
            if height is not None:
                grossArea = None
                if UtilitiesIfc.findPset(ifcBuilding, "Pset_BuildingCommon", "GrossPlannedArea") is not None:
                    grossArea = element.get_psets(ifcBuilding)["Pset_BuildingCommon"]["GrossPlannedArea"]
                if grossArea is None and UtilitiesIfc.findPset(ifcBuilding, "Qto_BuildingBaseQuantities",
                                                               "GrossFloorArea") is not None:
                    grossArea = element.get_psets(ifcBuilding)["Qto_BuildingBaseQuantities"]["GrossFloorArea"]
                if grossArea is None:
                    grossArea = footPrint.Area()
                grossVol = round(grossArea * float(height), 3)
        if grossVol is not None:
            chBldgVol = etree.SubElement(chBldg, QName(XmlNs.energy, "volume"))
            chBldgVolType = etree.SubElement(chBldgVol, QName(XmlNs.energy, "VolumeType"))
            chBldgVolTType = etree.SubElement(chBldgVolType, QName(XmlNs.energy, "type"))
            chBldgVolTType.text = "grossVolume"
            chBldgVolTValue = etree.SubElement(chBldgVolType, QName(XmlNs.energy, "value"))
            chBldgVolTValue.set("uom", "m3")
            chBldgVolTValue.text = str(grossVol)
        if netVol is not None:
            chBldgVol = etree.SubElement(chBldg, QName(XmlNs.energy, "volume"))
            chBldgVolType = etree.SubElement(chBldgVol, QName(XmlNs.energy, "VolumeType"))
            chBldgVolTType = etree.SubElement(chBldgVolType, QName(XmlNs.energy, "type"))
            chBldgVolTType.text = "netVolume"
            chBldgVolTValue = etree.SubElement(chBldgVolType, QName(XmlNs.energy, "value"))
            chBldgVolTValue.set("uom", "m3")
            chBldgVolTValue.text = str(netVol)

        # ReferencePoint
        chBldgRefPt = etree.SubElement(chBldg, QName(XmlNs.energy, "referencePoint"))
        chWDPosPt = etree.SubElement(chBldgRefPt, QName(XmlNs.energy, "Point"))
        chWDPosPtPos = etree.SubElement(chWDPosPt, QName(XmlNs.energy, "pos"))
        meanX, meanY, meanZ = (bbox[0] + bbox[1]) / 2, (bbox[2] + bbox[3]) / 2, (bbox[4] + bbox[5]) / 2
        chWDPosPtPos.text = str(meanX) + " " + str(meanY) + " " + str(meanZ)

        # FloorArea
        grossArea, netArea, grossAreaFloor, netAreaFloor = None, None, None, None
        if UtilitiesIfc.findPset(ifcBuilding, "Qto_BuildingBaseQuantities", "GrossFloorArea") is not None:
            grossArea = element.get_psets(ifcBuilding)["Qto_BuildingBaseQuantities"]["GrossFloorArea"]
        if UtilitiesIfc.findPset(ifcBuilding, "Qto_BuildingBaseQuantities", "NetFloorArea") is not None:
            netArea = element.get_psets(ifcBuilding)["Qto_BuildingBaseQuantities"]["NetFloorArea"]
        if grossArea is None and UtilitiesIfc.findPset(ifcBuilding, "Pset_BuildingCommon",
                                                       "GrossPlannedArea") is not None:
            grossAreaFloor = element.get_psets(ifcBuilding)["Pset_BuildingCommon"]["GrossPlannedArea"]
        if netArea is None and UtilitiesIfc.findPset(ifcBuilding, "Pset_BuildingCommon", "NetPlannedArea") is not None:
            netAreaFloor = element.get_psets(ifcBuilding)["Pset_BuildingCommon"]["NetPlannedArea"]
        if netArea is None and netVol is None:
            storeyCount = 0
            for child in chBldg:
                if "storeysAboveGround" in child.tag or "storeysBelowGround" in child.tag:
                    storeyCount += int(child.text)
            if storeyCount != 0:
                if grossAreaFloor is not None:
                    grossArea = grossAreaFloor * storeyCount
                if netAreaFloor is not None:
                    netArea = netAreaFloor * storeyCount
                if grossAreaFloor is None and netAreaFloor is None:
                    grossArea = footPrint.Area() * storeyCount
        if grossArea is not None:
            chBldgArea = etree.SubElement(chBldg, QName(XmlNs.energy, "floorArea"))
            chBldgFa = etree.SubElement(chBldgArea, QName(XmlNs.energy, "FloorArea"))
            chBldgFaType = etree.SubElement(chBldgFa, QName(XmlNs.energy, "type"))
            chBldgFaType.text = "grossFloorArea"
            chBldgFaValue = etree.SubElement(chBldgFa, QName(XmlNs.energy, "value"))
            chBldgFaValue.set("uom", "m2")
            chBldgFaValue.text = str(grossArea)
        if netArea is not None:
            chBldgArea = etree.SubElement(chBldg, QName(XmlNs.energy, "floorArea"))
            chBldgFa = etree.SubElement(chBldgArea, QName(XmlNs.energy, "FloorArea"))
            chBldgFaType = etree.SubElement(chBldgFa, QName(XmlNs.energy, "type"))
            chBldgFaType.text = "netFloorArea"
            chBldgFaValue = etree.SubElement(chBldgFa, QName(XmlNs.energy, "value"))
            chBldgFaValue.set("uom", "m2")
            chBldgFaValue.text = str(netArea)

        # HeightAboveGround
        chBldgHeightag = etree.SubElement(chBldg, QName(XmlNs.energy, "heightAboveGround"))
        chBldgHeightAg = etree.SubElement(chBldgHeightag, QName(XmlNs.energy, "HeightAboveGround"))
        chBldgHeightAgRef = etree.SubElement(chBldgHeightAg, QName(XmlNs.energy, "heightReference"))
        chBldgHeightAgRef.text = "bottomOfConstruction"
        chBldgHeightAgVal = etree.SubElement(chBldgHeightAg, QName(XmlNs.energy, "value"))
        chBldgHeightAgVal.set("uom", "m")
        chBldgHeightAgVal.text = str(footPrint.GetGeometryRef(0).GetPoint(0)[2])

    @staticmethod
    def calcUsageZone(ifc, ifcProject, ifcBuilding, chBldg, linkUZ, chBldgTZ):
        """ Berechnet die Nutzungszone für die Energy ADE

        Args:
            ifc: IFC-Datei
            ifcProject: IFC-Projekt, aus dem die Zeiteinheit entnommen werden soll
            ifcBuilding: IFC-Gebäude, aus dem die Nutzungszone berechnet werden soll
            chBldg: XML-Objekt, an das die Nutzungszone angehängt werden soll
            linkUZ: GML-ID der Nutzungszone, als String
            chBldgTZ: XML-Objekt der ThermalZone
        """

        # XML-Struktur
        chBldgUz = etree.SubElement(chBldg, QName(XmlNs.energy, "usageZone"))
        chBldgUZ = etree.SubElement(chBldgUz, QName(XmlNs.energy, "UsageZone"))
        chBldgUZ.set(QName(XmlNs.gml, "id"), linkUZ)

        # heatingSchedule & coolingSchedule
        for child in chBldgTZ:
            if "isCooled" in child.tag and child.text == "true":
                EADEConverter.constructTempSchedule(ifc, chBldgUZ, "Cooling", ifcBuilding)
        for child in chBldgTZ:
            if "isHeated" in child.tag and child.text == "true":
                EADEConverter.constructTempSchedule(ifc, chBldgUZ, "Heating", ifcBuilding)

        # usageZoneType
        classType = None
        for child in chBldg:
            if "class" in child.tag:
                classType = child.text
        if classType is not None:
            chBldgUzType = etree.SubElement(chBldgUZ, QName(XmlNs.energy, "usageZoneType"))
            chBldgUzType.set("codeSpace", "https://inspire.ec.europa.eu/codelist/CurrentUseValue/")
            chBldgUzType.text = str(Mapper.usageZoneTypeDict[int(classType)])

        # ventilationSchedule
        ventRate = None
        if UtilitiesIfc.findPset(ifcBuilding, "Pset_SpaceHVACDesign", "MechanicalVentilation") is not None and \
                element.get_psets(ifcBuilding)["Pset_SpaceHVACDesign"]["MechanicalVentilation"] and \
                UtilitiesIfc.findPset(ifcBuilding, "Pset_SpaceHVACDesign", "MechanicalVentilationRate") is not None:
            ventRate = element.get_psets(ifcBuilding)["Pset_SpaceHVACDesign"]["MechanicalVentilationRate"]
        if ventRate is None:
            ventRateAll, count = 0, 0
            ifcSpaces = UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcSpace", result=[])
            for ifcSpace in ifcSpaces:
                if UtilitiesIfc.findPset(ifcSpace, "Pset_SpaceHVACDesign", "MechanicalVentilation") is not None and \
                        element.get_psets(ifcSpace)["Pset_SpaceHVACDesign"]["MechanicalVentilation"] and \
                        UtilitiesIfc.findPset(ifcSpace, "Pset_SpaceHVACDesign",
                                              "MechanicalVentilationRate") is not None:
                    ventRateAll += element.get_psets(ifcSpace)["Pset_SpaceHVACDesign"]["MechanicalVentilationRate"]
                    count += 1
            if count != 0:
                ventRate = ventRateAll / count
        if ventRate is not None:
            chBldgUzVentSch = etree.SubElement(chBldgUZ, QName(XmlNs.energy, "ventilationSchedule"))
            chBldgUzVsCVS = etree.SubElement(chBldgUzVentSch, QName(XmlNs.energy, "ConstantValueSchedule"))
            chBldgUzVsAV = etree.SubElement(chBldgUzVsCVS, QName(XmlNs.energy, "averageValue"))
            chBldgUzVsAV.text = str(element.get_psets(ifcBuilding)["Pset_SpaceHVACDesign"]["MechanicalVentilationRate"])

        # occupiedBy: Occupants
        occCount, occRate = None, None
        if UtilitiesIfc.findPset(ifcBuilding, "Pset_SpaceOccupancyRequirements", "OccupancyNumber") is not None:
            occCount = element.get_psets(ifcBuilding)["Pset_SpaceOccupancyRequirements"]["OccupancyNumber"]
        if occCount is None:
            OccCountAll, count = 0, 0
            ifcSpaces = UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcSpace", result=[])
            for ifcSpace in ifcSpaces:
                if UtilitiesIfc.findPset(ifcSpace, "Pset_SpaceOccupancyRequirements", "OccupancyNumber") is not None:
                    OccCountAll += element.get_psets(ifcSpace)["Pset_SpaceOccupancyRequirements"]["OccupancyNumber"]
                    count += 1
            if count != 0:
                occCount = OccCountAll / count
        if occCount is not None:
            chBldgUzOccBy = etree.SubElement(chBldgUZ, QName(XmlNs.energy, "occupiedBy"))
            chBldgUzOcc = etree.SubElement(chBldgUzOccBy, QName(XmlNs.energy, "Occupants"))
            chBldgUzOcc.set(QName(XmlNs.gml, "id"), "GML_" + str(uuid.uuid4()))
            chBldgUzOccNr = etree.SubElement(chBldgUzOcc, QName(XmlNs.energy, "numberOfOccupants"))
            chBldgUzOccNr.text = str(occCount)

            if UtilitiesIfc.findPset(ifcBuilding, "Pset_SpaceOccupancyRequirements", "OccupancyTimePerDay") is not None:
                occRate = element.get_psets(ifcBuilding)["Pset_SpaceOccupancyRequirements"]["OccupancyTimePerDay"]
            if occRate is None:
                occRateAll, count = 0, 0
                ifcSpaces = UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcSpace", result=[])
                for ifcSpace in ifcSpaces:
                    if UtilitiesIfc.findPset(ifcSpace, "Pset_SpaceOccupancyRequirements",
                                             "OccupancyTimePerDay") is not None:
                        occRateAll += element.get_psets(ifcSpace)["Pset_SpaceOccupancyRequirements"][
                            "OccupancyTimePerDay"]
                        count += 1
                if count != 0:
                    occRate = occRateAll / count
            if occRate is not None:
                # Zeiteinheit
                if ifcProject.UnitsInContext is not None:
                    units = ifcProject.UnitsInContext.Units
                    for unit in units:
                        if unit.is_a('IfcSIUnit') and unit.UnitType == "TIMEUNIT":
                            if unit.Name == "MINUTE":
                                occRate = occRate / 60
                            elif unit.Name == "SECOND":
                                occRate = occRate / 60 / 60

                chBldgUzOccRate = etree.SubElement(chBldgUzOcc, QName(XmlNs.energy, "occupancyRate"))
                chBldgUzOccDVS = etree.SubElement(chBldgUzOccRate, QName(XmlNs.energy, "DualValueSchedule"))
                chBldgUzOccDVS.set(QName(XmlNs.gml, "id"), "GML_" + str(uuid.uuid4()))
                chBldgUzOccName = etree.SubElement(chBldgUzOccDVS, QName(XmlNs.gml, "name"))
                chBldgUzOccName.text = "Occupants"
                chBldgUzOccUH = etree.SubElement(chBldgUzOccDVS, QName(XmlNs.energy, "usageHoursPerDay"))
                chBldgUzOccUH.text = str(occRate)
                chBldgUzOccUD = etree.SubElement(chBldgUzOccDVS, QName(XmlNs.energy, "usageDaysPerYear"))
                chBldgUzOccUD.text = "365"
                chBldgUzOccUVal = etree.SubElement(chBldgUzOccDVS, QName(XmlNs.energy, "usageValue"))
                chBldgUzOccUVal.text = str(occCount)
                chBldgUzOccIVal = etree.SubElement(chBldgUzOccDVS, QName(XmlNs.energy, "idleValue"))
                chBldgUzOccIVal.text = "0"

        # equippedWith: Facilities
        hasOccSchedule = False
        for child in chBldg:
            if "occupiedBy" in child.tag:
                hasOccSchedule = True
        if hasOccSchedule:
            ifcElectricalAppl = UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcAudioVisualAppliance", result=[])
            ifcElectricalAppl += UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcCommunicationAppliance", result=[])
            ifcElectricalAppl += UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcElectricAppliance", result=[])
            ifcElectricalAppl += UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcMobileTelecommunicationsAppliance",
                                                          result=[])
            if len(ifcElectricalAppl) != 0:
                EADEConverter.constructEquipSchedule(chBldgUZ, "ElectricalAppliances")
            ifcLightingFac = UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcLamp", result=[])
            ifcLightingFac += UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcLightFixture", result=[])
            if len(ifcLightingFac) != 0:
                EADEConverter.constructEquipSchedule(chBldgUZ, "LightingFacilities")
            ifcDhwFac = UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcSpaceHeater", result=[])
            ifcDhwFac += UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcSanitaryTerminal", result=[])
            if len(ifcDhwFac) != 0:
                EADEConverter.constructEquipSchedule(chBldgUZ, "DHWFacilities")

    @staticmethod
    def constructTempSchedule(ifc, ch, mode, ifcBuilding):
        """ Erstellt den Zeitplanes der Temperaturen für die Energy ADE

        Args:
            ifc: IFC-Datei
            ch: XML-Objekt, an das der Zeitplan angehängt werden soll
            mode: Modus (Heating oder Cooling)
            ifcBuilding: IFC-Gebäude, aus dem die Nutzungszone berechnet werden soll
        """

        # min. und max. Temperaturen heraussuchen
        tempMax, tempMin = None, None
        if UtilitiesIfc.findPset(ifcBuilding, "Pset_SpaceHVACDesign", "TemperatureMax") is not None and \
                UtilitiesIfc.findPset(ifcBuilding, "Pset_SpaceHVACDesign", "TemperatureMin") is not None:
            tempMax = element.get_psets(ifcBuilding)["Pset_SpaceHVACDesign"]["TemperatureMax"]
            tempMin = element.get_psets(ifcBuilding)["Pset_SpaceHVACDesign"]["TemperatureMin"]
        if tempMax is None or tempMin is None:
            tempMaxAll, tempMinAll, count = 0, 0, 0
            ifcSpaces = UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcSpace", result=[])
            for ifcSpace in ifcSpaces:
                if UtilitiesIfc.findPset(ifcSpace, "Pset_SpaceHVACDesign", "TemperatureMax") is not None and \
                        UtilitiesIfc.findPset(ifcSpace, "Pset_SpaceHVACDesign", "TemperatureMin") is not None:
                    tempMaxAll += element.get_psets(ifcSpace)["Pset_SpaceHVACDesign"]["TemperatureMax"]
                    tempMinAll += element.get_psets(ifcSpace)["Pset_SpaceHVACDesign"]["TemperatureMin"]
                    count += 1
            if count != 0:
                tempMax, tempMin = tempMaxAll / count, tempMinAll / count

        # XML-Struktur
        if tempMax is not None and tempMin is not None:
            scheduleName = "heatingSchedule" if mode == "Heating" else "coolingSchedule"
            chBldgUzHeatSch = etree.SubElement(ch, QName(XmlNs.energy, scheduleName))
            chBldgUzHsDVS = etree.SubElement(chBldgUzHeatSch, QName(XmlNs.energy, "DualValueSchedule"))
            chBldgUzHsDVS.set(QName(XmlNs.gml, "id"), "GML_" + str(uuid.uuid4()))
            chBldgUzHsName = etree.SubElement(chBldgUzHsDVS, QName(XmlNs.gml, "name"))
            chBldgUzHsName.text = mode
            chBldgUzHsUH = etree.SubElement(chBldgUzHsDVS, QName(XmlNs.energy, "usageHoursPerDay"))
            chBldgUzHsUH.text = "8" if mode == "Heating" else "5"
            chBldgUzHsUD = etree.SubElement(chBldgUzHsDVS, QName(XmlNs.energy, "usageDaysPerYear"))
            chBldgUzHsUD.text = "200" if mode == "Heating" else "50"
            chBldgUzHsUVal = etree.SubElement(chBldgUzHsDVS, QName(XmlNs.energy, "usageValue"))
            chBldgUzHsUVal.text = str(tempMax) if mode == "Heating" else str(tempMin)
            chBldgUzHsIVal = etree.SubElement(chBldgUzHsDVS, QName(XmlNs.energy, "idleValue"))
            chBldgUzHsIVal.text = str(tempMin) if mode == "Heating" else str(tempMax)

    @staticmethod
    def constructEquipSchedule(ch, mode):
        """ Erstellt den Zeitplan der Nutzung für die Energy ADE

        Args:
            ch: XML-Objekt, an das der Zeitplan angehängt werden soll
            mode: Modus (ElectricalAppliances, LightingFacilities oder DHWFacilities)
        """

        # XML-Struktur
        chBldgUzEqW = etree.SubElement(ch, QName(XmlNs.energy, "equippedWith"))
        chBldgUzEq = etree.SubElement(chBldgUzEqW, QName(XmlNs.energy, mode))
        scheduleName = mode + "Schedule"
        chBldgUzHeatSch = etree.SubElement(chBldgUzEq, QName(XmlNs.energy, scheduleName))
        chBldgUzHsDVS = etree.SubElement(chBldgUzHeatSch, QName(XmlNs.energy, "DualValueSchedule"))
        chBldgUzHsDVS.set(QName(XmlNs.gml, "id"), "GML_" + str(uuid.uuid4()))
        chBldgUzHsName = etree.SubElement(chBldgUzHsDVS, QName(XmlNs.gml, "name"))
        chBldgUzHsName.text = mode
        chBldgUzHsUH = etree.SubElement(chBldgUzHsDVS, QName(XmlNs.energy, "usageHoursPerDay"))
        chBldgUzHsUH.text = "3" if mode == "LightingFacilities" else "8"
        chBldgUzHsUD = etree.SubElement(chBldgUzHsDVS, QName(XmlNs.energy, "usageDaysPerYear"))
        chBldgUzHsUD.text = "365"
        chBldgUzHsUVal = etree.SubElement(chBldgUzHsDVS, QName(XmlNs.energy, "usageValue"))
        chBldgUzHsUVal.text = "1"
        chBldgUzHsIVal = etree.SubElement(chBldgUzHsDVS, QName(XmlNs.energy, "idleValue"))
        chBldgUzHsIVal.text = "0"

    @staticmethod
    def calcThermalZone(ifc, ifcBuilding, chBldg, root, surfaces, lod):
        """ Berechnet die thermischen Zone für die Energy ADE

        Args:
            ifc: IFC-Datei
            ifcBuilding: IFC-Gebäude, aus dem die thermische Zone berechnet werden soll
            chBldg: XML-Objekt, an das die thermische Zone angehängt werden soll
            root: XML-Objekt, aus dem die BoundingBox entnommen werden soll
            surfaces: Die Oberflächen, als Liste
            lod: Level of Detail, als Zahl

        Returns
            linkUZ: GML-ID der anzufügenden Nutzungszone
            chBldgTZ: XML-Objekt der thermischen Zone
            constructions: Die zu erstellenden Konstruktionen, als Liste
        """

        # XML-Struktur
        chBldgTz = etree.SubElement(chBldg, QName(XmlNs.energy, "thermalZone"))
        chBldgTZ = etree.SubElement(chBldgTz, QName(XmlNs.energy, "ThermalZone"))
        linkTZ = "GML_" + str(uuid.uuid4())
        chBldgTZ.set(QName(XmlNs.gml, "id"), linkTZ)

        # contains: UsageZone
        chBldgTzContains = etree.SubElement(chBldgTZ, QName(XmlNs.energy, "contains"))
        linkUZ = "GML_" + str(uuid.uuid4())
        chBldgTzContains.set(QName(XmlNs.xlink, "href"), "#" + linkUZ)

        # floorArea & volume
        for child in chBldg:
            if "floorArea" in child.tag:
                chBldgTZ.append(deepcopy(child))
            if "volume" in child.tag:
                chBldgTZ.append(deepcopy(child))

        # infiltrationRate
        infRateS, infRateW = None, None
        if UtilitiesIfc.findPset(ifcBuilding, "Pset_ThermalLoad", "InfiltrationDiversitySummer") is not None:
            infRateS = element.get_psets(ifcBuilding)["Pset_ThermalLoad"]["InfiltrationDiversitySummer"]
        if UtilitiesIfc.findPset(ifcBuilding, "Pset_ThermalLoad", "InfiltrationDiversityWinter") is not None:
            infRateW = element.get_psets(ifcBuilding)["Pset_ThermalLoad"]["InfiltrationDiversityWinter"]
        if infRateS is None and UtilitiesIfc.findPset(ifcBuilding, "Pset_AirSideSystemInformation",
                                                      "InfiltrationDiversitySummer") is not None:
            infRateS = element.get_psets(ifcBuilding)["Pset_AirSideSystemInformation"][
                "InfiltrationDiversitySummer"]
        if infRateW is None and UtilitiesIfc.findPset(ifcBuilding, "Pset_AirSideSystemInformation",
                                                      "InfiltrationDiversityWinter") is not None:
            infRateW = element.get_psets(ifcBuilding)["Pset_AirSideSystemInformation"][
                "InfiltrationDiversityWinter"]
        if infRateS is not None or infRateW is not None:
            chBldgTzInfRate = etree.SubElement(chBldgTZ, QName(XmlNs.energy, "infiltrationRate"))
            if infRateS is not None and infRateW is not None:
                infRate = (infRateS + infRateW) / 2
            else:
                infRate = infRateS if infRateS is not None else infRateW
            chBldgTzInfRate.text = infRate

        # isCooled
        isCooled = None
        if UtilitiesIfc.findPset(ifcBuilding, "Pset_SpaceHVACDesign", "AirConditioning") is not None:
            isCooled = element.get_psets(ifcBuilding)["Pset_SpaceHVACDesign"]["AirConditioning"]
        if isCooled is None:
            ifcSpaces = UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcSpace", result=[])
            for ifcSpace in ifcSpaces:
                if UtilitiesIfc.findPset(ifcSpace, "Pset_SpaceHVACDesign", "AirConditioning") is not None and \
                        element.get_psets(ifcSpace)["Pset_SpaceHVACDesign"]["AirConditioning"]:
                    isCooled = True
        if isCooled is None:
            ifcCooler = UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcChiller", result=[])
            ifcCooler += UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcCoolingTower", result=[])
            ifcCooler += UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcCooledBeam", result=[])
            ifcCooler += UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcEvaproativeCooler", result=[])
            isCooled = True if len(ifcCooler) > 0 else False
        chBldgTzIsCooled = etree.SubElement(chBldgTZ, QName(XmlNs.energy, "isCooled"))
        chBldgTzIsCooled.text = str(isCooled).lower()

        # isHeated
        if len(UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcDistributionElement", result=[])) == 0:
            isHeated = True
        else:
            ifcHeater = UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcSpaceHeater", result=[])
            ifcHeater += UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcBurner", result=[])
            ifcHeater += UtilitiesIfc.findElement(ifc, ifcBuilding, "IfcHeatExchanger", result=[])
            isHeated = True if len(ifcHeater) > 0 else False
        chBldgTzIsHeated = etree.SubElement(chBldgTZ, QName(XmlNs.energy, "isHeated"))
        chBldgTzIsHeated.text = str(isHeated).lower()

        # boundedBy: Envelope
        for child in root:
            if "boundedBy" in child.tag:
                chBldgTZ.append(deepcopy(child))

        # boundedBy: ThermalBoundary
        constructions = []
        if lod >= 2:
            constructions = EADEConverter.calcThermalBoundaries(ifc, chBldg, chBldgTZ, lod, surfaces, linkTZ)

        # volumeGeometry
        chBldgTzVolGeom = etree.SubElement(chBldgTZ, QName(XmlNs.energy, "volumeGeometry"))
        for child in chBldg:
            tag = "lod" + str(lod) + "Solid"
            if tag in child.tag:
                chBldgTzVolGeom.append(deepcopy(child[0]))

        return linkUZ, chBldgTZ, constructions

    @staticmethod
    def calcThermalBoundaries(ifc, chBldg, chBldgTZ, lod, surfaces, linkTZ):
        """ Berechnet die thermischen Begrenzungen für die Energy ADE

        Args:
            ifc: IFC-Datei
            chBldg: XML-Objekt, aus dem die Begrenzungen entnommen werden sollen
            chBldgTZ: XML-Objekt, an das die thermischen Begrenzungen angehängt werden sollen
            lod: Level of Detail, als Zahl
            surfaces: Die Öffnungen
            linkTZ: GML-ID der thermischen Zone, der die thermischen Begrenzungen angehören

        Returns
            constructions: Die zu erstellenden Konstruktionen, als Liste
        """
        constructions = []
        for child in chBldg:
            if "boundedBy" in child.tag:
                # XML-Struktur
                chBldgTzBby = etree.SubElement(chBldgTZ, QName(XmlNs.energy, "boundedBy"))
                chBldgTb = etree.SubElement(chBldgTzBby, QName(XmlNs.energy, "ThermalBoundary"))
                chBldgTb.set(QName(XmlNs.gml, "id"), "GML_" + str(uuid.uuid4()))

                # thermalBoundaryType
                type = None
                if "GroundSurface" in child[0].tag:
                    type = "groundSlab"
                elif "RoofSurface" in child[0].tag:
                    type = "roof"
                elif "WallSurface" in child[0].tag:
                    type = "outerWall"
                chBldgTbType = etree.SubElement(chBldgTb, QName(XmlNs.energy, "thermalBoundaryType"))
                chBldgTbType.text = type

                geomR, geomAll = None, []
                for childGeom in child[0]:
                    tag = "lod" + str(lod) + "MultiSurface"
                    if tag in childGeom.tag:
                        geomGML = etree.tostring(childGeom[0][0][0]).decode('utf-8')
                        geom = ogr.CreateGeometryFromGML(geomGML)
                        if geom.GetGeometryName() == "MULTIPOLYGON":
                            geomR = geom.GetGeometryRef(0)
                            for i in range(0, geom.GetGeometryCount()):
                                geomAll.append(geom.GetGeometryRef(i))
                        else:
                            geomR = geom
                            geomAll = [geom]

                # azimuth
                chBldgTbAz = etree.SubElement(chBldgTb, QName(XmlNs.energy, "azimuth"))
                chBldgTbAz.set("uom", "deg")
                chBldgTbAz.text = str(round(UtilitiesGeom.calcAzimuth(geomR), 5))

                # inclination
                chBldgTbIncl = etree.SubElement(chBldgTb, QName(XmlNs.energy, "inclination"))
                chBldgTbIncl.set("uom", "deg")
                chBldgTbIncl.text = str(round(UtilitiesGeom.calcInclination(geomR) / math.pi * 180, 5))

                # area
                chBldgTbArea = etree.SubElement(chBldgTb, QName(XmlNs.energy, "area"))
                chBldgTbArea.set("uom", "m2")
                chBldgTbArea.text = str(round(UtilitiesGeom.calcArea3D(geomAll), 5))

                # surfaceGeometry
                chGeom = None
                for childGeom in child[0]:
                    tag = "lod" + str(lod) + "MultiSurface"
                    if tag in childGeom.tag:
                        chGeom = childGeom
                chBldgTbGeom = etree.SubElement(chBldgTb, QName(XmlNs.energy, "surfaceGeometry"))
                chBldgTbGeom.append(deepcopy(chGeom[0]))

                # construction
                ifcElem = None
                for surface in surfaces:
                    if child[0].attrib['{http://www.opengis.net/gml}id'] == surface.gmlId:
                        ifcElem = surface.ifcElem
                        break

                ifcMLS = None
                rels = ifc.get_inverse(ifcElem)
                for rel in rels:
                    if rel.is_a('IfcRelAssociatesMaterial') and ifcElem in rel.RelatedObjects:
                        if rel.RelatingMaterial is not None and rel.RelatingMaterial.is_a(
                                "IfcMaterialLayerSetUsage"):
                            ifcMLSU = rel.RelatingMaterial
                            if ifcMLSU.ForLayerSet is not None:
                                ifcMLS = ifcMLSU.ForLayerSet

                if ifcMLS is not None:
                    sameMLS, constr = False, None
                    for constr in constructions:
                        if constr.ifcMLS == ifcMLS:
                            sameMLS = True
                            break
                    if sameMLS:
                        gmlIdConstr = constr.gmlId
                        constr.ifcElems.append(ifcElem)
                    else:
                        gmlIdConstr = "GML_" + str(uuid.uuid4())
                        constrNew = Construction(gmlIdConstr, ifcMLS, None, [ifcElem], "layer")
                        constructions.append(constrNew)

                    chBldgTbConstr = etree.SubElement(chBldgTb, QName(XmlNs.energy, "construction"))
                    chBldgTbConstr.set(QName(XmlNs.xlink, "href"), "#" + gmlIdConstr)

                # contains
                if lod >= 3:
                    EADEConverter.calcThermalOpenings(ifc, child, chBldgTb, lod, surfaces, constructions)

                # delimits
                chBldgTbDel = etree.SubElement(chBldgTb, QName(XmlNs.energy, "delimits"))
                chBldgTbDel.set(QName(XmlNs.xlink, "href"), "#" + linkTZ)

        return constructions

    @staticmethod
    def calcThermalOpenings(ifc, child, chBldgTb, lod, surfaces, constructions):
        """ Berechnet die thermischen Öffnungen für die Energy ADE

        Args:
            ifc: IFC-Datei
            child: XML-Objekt, aus dem die Öffnungen entnommen werden sollen
            chBldgTb: XML-Objekt, an das die thermischen Öffnungen angehängt werden sollen
            lod: Level of Detail, als Zahl
            surfaces: Die GML-IDs und zugehörigen IFC-Elemente der Oberflächen
            constructions: Die zu erstellenden Konstruktionen, als Liste

        Returns
            constructions: Die zu erstellenden Konstruktionen der Boundary, mit GML-ID, IfcElement und Referenzen
        """
        for childSurf in child[0]:
            if "opening" in childSurf.tag:
                chOpen = childSurf[0]

                # XML-Struktur
                chBldgTbCont = etree.SubElement(chBldgTb, QName(XmlNs.energy, "contains"))
                chBldgTo = etree.SubElement(chBldgTbCont, QName(XmlNs.energy, "ThermalOpening"))
                chBldgTo.set(QName(XmlNs.gml, "id"), "GML_" + str(uuid.uuid4()))

                # area
                geom = None
                for chGeom in chOpen:
                    if "lod3MultiSurface" in chGeom.tag:
                        geomGML = etree.tostring(chGeom[0][0][0]).decode('utf-8')
                        geom = ogr.CreateGeometryFromGML(geomGML)
                chBldgToArea = etree.SubElement(chBldgTo, QName(XmlNs.energy, "area"))
                chBldgToArea.set("uom", "m2")
                chBldgToArea.text = str(round(UtilitiesGeom.calcArea3D(geom), 5))

                # construction
                ifcElem = None
                for surface in surfaces:
                    if chOpen.attrib['{http://www.opengis.net/gml}id'] == surface.gmlId:
                        ifcElem = surface.ifcElem
                        break

                # Material, falls vorhanden
                ifcMLS = None
                rels = ifc.get_inverse(ifcElem)
                for rel in rels:
                    if rel.is_a('IfcRelAssociatesMaterial') and ifcElem in rel.RelatedObjects:
                        if rel.RelatingMaterial is not None and rel.RelatingMaterial.is_a(
                                "IfcMaterialLayerSetUsage"):
                            ifcMLSU = rel.RelatingMaterial
                            if ifcMLSU.ForLayerSet is not None:
                                ifcMLS = ifcMLSU.ForLayerSet

                if ifcMLS is not None:
                    sameMLS, constr = False, None
                    for constr in constructions:
                        if constr.ifcMLS == ifcMLS:
                            sameMLS = True
                            break
                    if sameMLS:
                        gmlIdConstr = constr.gmlId
                        constr.ifcElems.append(ifcElem)
                    else:
                        gmlIdConstr = "GML_" + str(uuid.uuid4())
                        constrNew = Construction(gmlIdConstr, ifcMLS, None, [ifcElem], "layer")
                        constructions.append(constrNew)

                    chBldgToConstr = etree.SubElement(chBldgTo,
                                                      QName(XmlNs.energy, "construction"))
                    chBldgToConstr.set(QName(XmlNs.xlink, "href"), "#" + gmlIdConstr)

                # OpticalProperties, falls vorhanden
                else:
                    thTransm, glazing = None, None
                    solRefl, visRefl, solTransm, visTransm = None, None, None, None

                    # U-Wert
                    if UtilitiesIfc.findPset(ifcElem, "Pset_DoorCommon",
                                             "ThermalTransmittance") is not None:
                        thTransm = element.get_psets(ifcElem)["Pset_DoorCommon"][
                            "ThermalTransmittance"]
                    if UtilitiesIfc.findPset(ifcElem, "Pset_WindowCommon",
                                             "ThermalTransmittance") is not None:
                        thTransm = element.get_psets(ifcElem)["Pset_WindowCommon"][
                            "ThermalTransmittance"]

                    # reflectance
                    if UtilitiesIfc.findPset(ifcElem, "Pset_DoorWindowGlazingType",
                                             "SolarReflectance") is not None:
                        solRefl = element.get_psets(ifcElem)["Pset_DoorWindowGlazingType"][
                            "SolarReflectance"]
                    if UtilitiesIfc.findPset(ifcElem, "Pset_DoorWindowGlazingType",
                                             "VisibleLightReflectance") is not None:
                        visRefl = element.get_psets(ifcElem)["Pset_DoorWindowGlazingType"][
                            "VisibleLightReflectance"]

                    # transmittance
                    if UtilitiesIfc.findPset(ifcElem, "Pset_DoorWindowGlazingType",
                                             "SolarTransmittance") is not None:
                        solTransm = element.get_psets(ifcElem)["Pset_DoorWindowGlazingType"][
                            "SolarTransmittance"]
                    if UtilitiesIfc.findPset(ifcElem, "Pset_DoorWindowGlazingType",
                                             "VisibleLightTransmittance") is not None:
                        visTransm = element.get_psets(ifcElem)["Pset_DoorWindowGlazingType"][
                            "VisibleLightTransmittance"]

                    # glazingRatio
                    if UtilitiesIfc.findPset(ifcElem, "Pset_DoorCommon",
                                             "GlazingAreaFraction") is not None:
                        glazing = element.get_psets(ifcElem)["Pset_DoorCommon"][
                            "GlazingAreaFraction"]
                    if UtilitiesIfc.findPset(ifcElem, "Pset_WindowCommon",
                                             "GlazingAreaFraction") is not None:
                        glazing = element.get_psets(ifcElem)["Pset_WindowCommon"][
                            "GlazingAreaFraction"]

                    if not (
                            thTransm is None and solRefl is None and visRefl is None and solTransm
                            is None and visTransm is None and glazing is None):
                        sameOptProp, constr = False, None
                        for constr in constructions:
                            optProp = constr.optProp
                            if constr.type == "optical" and optProp[0] == thTransm and optProp[1] == solRefl and \
                                    optProp[2] == visRefl and optProp[3] == solTransm and optProp[4] == visTransm \
                                    and optProp[5] == glazing:
                                sameOptProp = True
                                break
                        if sameOptProp:
                            gmlIdConstr = constr.gmlId
                            constr.ifcElems.append(ifcElem)
                        else:
                            gmlIdConstr = "GML_" + str(uuid.uuid4())
                            optProp = [thTransm, solRefl, visRefl, solTransm, visTransm,
                                       glazing]
                            constrNew = Construction(gmlIdConstr, None, optProp, [ifcElem], "optical")
                            constructions.append(constrNew)

                        chBldgToConstr = etree.SubElement(chBldgTo,
                                                          QName(XmlNs.energy, "construction"))
                        chBldgToConstr.set(QName(XmlNs.xlink, "href"), "#" + gmlIdConstr)

                # surfaceGeometry
                for chGeom in chOpen:
                    tag = "lod" + str(lod) + "MultiSurface"
                    if tag in chGeom.tag:
                        chBldgToGeom = etree.SubElement(chBldgTo,
                                                        QName(XmlNs.energy, "surfaceGeometry"))
                        chBldgToGeom.append(deepcopy(chGeom[0]))

        return constructions

    @staticmethod
    def convertConstructions(root, constructions):
        """ Berechnet die Konstruktionen der Begrenzung der thermalen Zone für die Energy ADE

        Args:
            root: XML-Objekt, an das die Konstruktionen angehängt werden sollen
            constructions: Die zu erstellenden Konstruktionen, als Liste

        Returns
            materials: Die zu erstellenden Materialien der Konstruktion, als Liste
        """
        materials = []
        for constr in constructions:
            # XML-Struktur
            chFM = etree.SubElement(root, QName(XmlNs.gml, "featureMember"))
            chConstr = etree.SubElement(chFM, QName(XmlNs.energy, "Construction"))
            chConstr.set(QName(XmlNs.gml, "id"), constr.gmlId)

            if constr.type == "layer":

                # Name & Beschreibung
                if constr.ifcMLS.LayerSetName is not None:
                    chConstrName = etree.SubElement(chConstr, QName(XmlNs.gml, "name"))
                    chConstrName.text = constr.ifcMLS.LayerSetName
                if constr.ifcMLS.Description is not None:
                    chConstrDescr = etree.SubElement(chConstr, QName(XmlNs.gml, "description"))
                    chConstrDescr.text = constr.ifcMLS.Description

                # U-Wert
                thTransm = None
                if UtilitiesIfc.findPset(constr.ifcElems[0], "Pset_WallCommon", "ThermalTransmittance") is not None:
                    thTransm = element.get_psets(constr.ifcElems[0])["Pset_WallCommon"]["ThermalTransmittance"]
                if UtilitiesIfc.findPset(constr.ifcElems[0], "Pset_RoofCommon", "ThermalTransmittance") is not None:
                    thTransm = element.get_psets(constr.ifcElems[0])["Pset_RoofCommon"]["ThermalTransmittance"]
                if UtilitiesIfc.findPset(constr.ifcElems[0], "Pset_SlabCommon", "ThermalTransmittance") is not None:
                    thTransm = element.get_psets(constr.ifcElems[0])["Pset_SlabCommon"]["ThermalTransmittance"]
                if thTransm is not None:
                    chConstrUV = etree.SubElement(chConstr, QName(XmlNs.energy, "uValue"))
                    chConstrUV.set("uom", "W/K*m2")
                    chConstrUV.text = str(thTransm)

                # Layer
                if constr.ifcMLS.MaterialLayers is not None:
                    for matLayer in constr.ifcMLS.MaterialLayers:

                        # XML-Struktur
                        chConstrlayer = etree.SubElement(chConstr, QName(XmlNs.energy, "layer"))
                        chConstrLayer = etree.SubElement(chConstrlayer, QName(XmlNs.energy, "Layer"))
                        chConstrLayer.set(QName(XmlNs.gml, "id"), "GML_" + str(uuid.uuid4()))
                        chConstrLaycomp = etree.SubElement(chConstrLayer, QName(XmlNs.energy, "layerComponent"))
                        chConstrLayComp = etree.SubElement(chConstrLaycomp,
                                                           QName(XmlNs.energy, "LayerComponent"))

                        # areaFraction
                        chConstrLayFrac = etree.SubElement(chConstrLayComp, QName(XmlNs.energy, "areaFraction"))
                        chConstrLayFrac.set("uom", "scale")
                        chConstrLayFrac.text = "1"

                        # thickness
                        if matLayer.LayerThickness is not None:
                            chConstrLayThick = etree.SubElement(chConstrLayComp,
                                                                QName(XmlNs.energy, "thickness"))
                            chConstrLayThick.set("uom", "m")
                            chConstrLayThick.text = str(matLayer.LayerThickness)

                        # material: Verweis auf Material
                        if matLayer.Material is not None:
                            chConstrLayMat = etree.SubElement(chConstrLayComp, QName(XmlNs.energy, "material"))
                            gmlId = None
                            for mat in materials:
                                if mat.ifcMat == matLayer.Material:
                                    gmlId = mat.gmlId
                            if gmlId is None:
                                gmlId = "GML_" + str(uuid.uuid4())
                                materials.append(Material(gmlId, matLayer.Material))
                            chConstrLayMat.set(QName(XmlNs.xlink, "href"), "#" + gmlId)
            else:
                # U-Wert
                optProp = constr.optProp
                if optProp[0] is not None:
                    chConstrUV = etree.SubElement(chConstr, QName(XmlNs.energy, "uValue"))
                    chConstrUV.set("uom", "W/K*m2")
                    chConstrUV.text = str(optProp[0])

                # OpticalProperties
                if not (optProp[1] is None and optProp[2] is None and optProp[3] is None and optProp[4]
                        is None and optProp[5] is None):
                    chConstrOp = etree.SubElement(chConstr, QName(XmlNs.energy, "opticalProperties"))
                    chConstrOP = etree.SubElement(chConstrOp, QName(XmlNs.energy, "OpticalProperties"))
                    if optProp[1] is not None:
                        chConstrOprefl = etree.SubElement(chConstrOP, QName(XmlNs.energy, "reflectance"))
                        chConstrOpRefl = etree.SubElement(chConstrOprefl, QName(XmlNs.energy, "Reflectance"))
                        chConstrOpReflFrac = etree.SubElement(chConstrOpRefl, QName(XmlNs.energy, "fraction"))
                        chConstrOpReflFrac.set("uom", "scale")
                        chConstrOpReflFrac.text = str(optProp[1])
                        chConstrOpReflSurf = etree.SubElement(chConstrOpRefl, QName(XmlNs.energy, "surface"))
                        chConstrOpReflSurf.text = "outside"
                        chConstrOpReflWLR = etree.SubElement(chConstrOpRefl,
                                                             QName(XmlNs.energy, "wavelengthRange"))
                        chConstrOpReflWLR.text = "solar"
                    if optProp[2] is not None:
                        chConstrOprefl = etree.SubElement(chConstrOP, QName(XmlNs.energy, "reflectance"))
                        chConstrOpRefl = etree.SubElement(chConstrOprefl, QName(XmlNs.energy, "Reflectance"))
                        chConstrOpReflFrac = etree.SubElement(chConstrOpRefl, QName(XmlNs.energy, "fraction"))
                        chConstrOpReflFrac.set("uom", "scale")
                        chConstrOpReflFrac.text = str(optProp[2])
                        chConstrOpReflSurf = etree.SubElement(chConstrOpRefl, QName(XmlNs.energy, "surface"))
                        chConstrOpReflSurf.text = "outside"
                        chConstrOpReflWLR = etree.SubElement(chConstrOpRefl,
                                                             QName(XmlNs.energy, "wavelengthRange"))
                        chConstrOpReflWLR.text = "visible"
                    if optProp[3] is not None:
                        chConstrOptransm = etree.SubElement(chConstrOP, QName(XmlNs.energy, "transmittance"))
                        chConstrOpTransm = etree.SubElement(chConstrOptransm,
                                                            QName(XmlNs.energy, "Transmittance"))
                        chConstrOpTransmFrac = etree.SubElement(chConstrOpTransm,
                                                                QName(XmlNs.energy, "fraction"))
                        chConstrOpTransmFrac.set("uom", "scale")
                        chConstrOpTransmFrac.text = str(optProp[3])
                        chConstrOpTransmWLR = etree.SubElement(chConstrOpTransm,
                                                               QName(XmlNs.energy, "wavelengthRange"))
                        chConstrOpTransmWLR.text = "solar"
                    if optProp[4] is not None:
                        chConstrOptransm = etree.SubElement(chConstrOP, QName(XmlNs.energy, "transmittance"))
                        chConstrOpTransm = etree.SubElement(chConstrOptransm,
                                                            QName(XmlNs.energy, "Transmittance"))
                        chConstrOpTransmFrac = etree.SubElement(chConstrOpTransm,
                                                                QName(XmlNs.energy, "fraction"))
                        chConstrOpTransmFrac.set("uom", "scale")
                        chConstrOpTransmFrac.text = str(optProp[4])
                        chConstrOpTransmWLR = etree.SubElement(chConstrOpTransm,
                                                               QName(XmlNs.energy, "wavelengthRange"))
                        chConstrOpTransmWLR.text = "visible"
                    if optProp[5] is not None:
                        chConstrOpGlaz = etree.SubElement(chConstrOP, QName(XmlNs.energy, "glazingRatio"))
                        chConstrOpGlaz.set("uom", "scale")
                        chConstrOpGlaz.text = str(optProp[5])

        return materials

    @staticmethod
    def convertMaterials(root, materials):
        """ Berechnet die Materialien der Konstruktionen der Begrenzung der thermalen Zone für die Energy ADE

        Args:
            root: XML-Objekt, an das die Materialien angehängt werden sollen
            materials: Zu erstellende Materialien, als Liste
        """
        for mat in materials:

            # XML-Struktur
            chFM = etree.SubElement(root, QName(XmlNs.gml, "featureMember"))
            chMat = etree.SubElement(chFM, QName(XmlNs.energy, "SolidMaterial"))
            chMat.set(QName(XmlNs.gml, "id"), mat.gmlId)

            # Name & Beschreibung
            if mat.ifcMat.Name is not None:
                chMatName = etree.SubElement(chMat, QName(XmlNs.gml, "name"))
                chMatName.text = mat.ifcMat.Name
            if mat.ifcMat.Description is not None:
                chMatDescr = etree.SubElement(chMat, QName(XmlNs.gml, "description"))
                chMatDescr.text = mat.ifcMat.Description

            # Eigenschaften heraussuchen
            cond, density, perm, spHeat = None, None, None, None
            matProps = mat.ifcMat.HasProperties
            for matProp in matProps:
                # noinspection PyBroadException
                try:
                    if matProp.Name == "Pset_MaterialCommon":
                        for prop in matProp.Properties:
                            if prop.Name == "MassDensity":
                                density = prop.NominalValue.wrappedValue
                    if matProp.Name == "Pset_MaterialThermal":
                        for prop in matProp.Properties:
                            if prop.Name == "ThermalConductivity":
                                cond = prop.NominalValue.wrappedValue
                            if prop.Name == "SpecificHeatCapacity":
                                spHeat = prop.NominalValue.wrappedValue
                    if matProp.Name == "Pset_MaterialHygroscopic":
                        for prop in matProp.Properties:
                            if prop.Name == "VaporPermeability":
                                perm = prop.NominalValue.wrappedValue
                except Exception:
                    pass

            # Conductivity
            if cond is not None:
                chMatCond = etree.SubElement(chMat, QName(XmlNs.energy, "conductivity"))
                chMatCond.set("uom", "W/K*m")
                chMatCond.text = str(cond)

            # Density
            if density is not None:
                chMatDensity = etree.SubElement(chMat, QName(XmlNs.energy, "density"))
                chMatDensity.set("uom", "kg/m3")
                chMatDensity.text = str(density)

            # Permeance
            if perm is not None:
                chMatPerm = etree.SubElement(chMat, QName(XmlNs.energy, "permeance"))
                chMatPerm.set("uom", "kg/s*m*Pa")
                chMatPerm.text = str(perm)

            # SpecificHeat
            if spHeat is not None:
                chMatSpHeat = etree.SubElement(chMat, QName(XmlNs.energy, "specificHeat"))
                chMatSpHeat.set("uom", "W/K*m")
                chMatSpHeat.text = str(spHeat)
