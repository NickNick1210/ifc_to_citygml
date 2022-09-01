# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)

Unit-Test für die Modelklasse EADEConverter
 ***************************************************************************/
"""

# Standard-Bibliotheken
import unittest
import logging
import sys

# IFC-Bibliotheken
import ifcopenshell

# XML-Bibliotheken
from lxml import etree

# Geo-Bibliotheken
from osgeo import ogr

# Plugin
sys.path.insert(0, '..')
from models.converter_eade import EADEConverter

#####

LOGGER = logging.getLogger('QGIS')

# IFC-Elemente
dataPath1 = r"data/IFC_test.ifc"
ifc1 = ifcopenshell.open(dataPath1)
ifcBldg1 = ifc1.by_type("IfcBuilding")[0]
ifcSite1 = ifc1.by_type("IfcSite")[0]
ifcProj1 = ifc1.by_type("IfcProject")[0]

dataPath2 = r"data/IFC_test3.ifc"
ifc2 = ifcopenshell.open(dataPath2)
ifcBldg2 = ifc2.by_type("IfcBuilding")[0]
ifcSite2 = ifc2.by_type("IfcSite")[0]
ifcProj2 = ifc2.by_type("IfcProject")[0]

dataPath3 = r"data/IFC_test4.ifc"
ifc3 = ifcopenshell.open(dataPath3)
ifcBldg3 = ifc3.by_type("IfcBuilding")[0]
ifcSite3 = ifc3.by_type("IfcSite")[0]
ifcProj3 = ifc3.by_type("IfcProject")[0]

# XML-Elemente
root = etree.Element("root")

# Geometrien
bbox = (10, 10, 10, 20, 20, 20)
geom1 = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 20 10, 20 20 10, 20 10 10, 10 10 10))")
geom2 = ogr.CreateGeometryFromWkt("Polygon((10 10 3.1415, 10 20 3.1415, 20 20 3.1415, 20 10 10, 10 10 3.1415))")


class TestConvertWeatherData(unittest.TestCase):

    def test_1(self):
        rootNew = etree.Element("root")
        EADEConverter.convertWeatherData(ifcProj1, ifcSite1, rootNew, bbox)
        corr = b'<root><ns0:weatherData xmlns:ns0="http://www.sig3d.org/citygml/2.0/energy/1.0"><ns0:WeatherData>' + \
               b'<ns0:weatherDataType>airTemperature</ns0:weatherDataType><ns0:values><ns0:RegularTimeSeries>' + \
               b'<ns0:variableProperties><ns0:TimeValuesProperties><ns0:acqusitionMethod>unknown' + \
               b'</ns0:acqusitionMethod><ns0:interpolationType>continuous</ns0:interpolationType><ns0:source>' + \
               b'IFC building model</ns0:source><ns0:thematicDescription>ambient temperature' + \
               b'</ns0:thematicDescription></ns0:TimeValuesProperties></ns0:variableProperties><ns0:temporalExtent>' + \
               b'<ns0:TimePeriod><ns0:beginPosition>2020-01-01T00:00:00</ns0:beginPosition><ns0:endPosition>' + \
               b'2025-12-31T23:59:59</ns0:endPosition></ns0:TimePeriod></ns0:temporalExtent><ns0:timeInterval ' + \
               b'unit="month">6</ns0:timeInterval><ns0:values uom="C">-5.0 35.0 -5.0 35.0 -5.0 35.0 -5.0 35.0 -5.0 ' + \
               b'35.0 -5.0 35.0 </ns0:values></ns0:RegularTimeSeries></ns0:values><ns0:position><ns0:Point>' + \
               b'<ns0:pos>10.0 15.0 20.0</ns0:pos></ns0:Point></ns0:position></ns0:WeatherData></ns0:weatherData>' + \
               b'</root>'
        self.assertEqual(corr, etree.tostring(rootNew))

    def test_2(self):
        rootNew = etree.Element("root")
        EADEConverter.convertWeatherData(ifcProj2, ifcSite2, rootNew, bbox)
        corr = b'<root/>'
        self.assertEqual(corr, etree.tostring(rootNew))

    def test_3(self):
        rootNew = etree.Element("root")
        EADEConverter.convertWeatherData(ifcProj3, ifcSite3, rootNew, bbox)
        corr = b'<root/>'
        self.assertEqual(corr, etree.tostring(rootNew))


class TestConvertBldgAttr(unittest.TestCase):

    def test_1(self):
        rootNew = etree.Element("root")
        EADEConverter.convertBldgAttr(ifc1, ifcBldg1, rootNew, bbox, geom1)
        corr = b'<root><ns0:constructionWeight xmlns:ns0="http://www.sig3d.org/citygml/2.0/energy/1.0">medium' + \
               b'</ns0:constructionWeight><ns1:referencePoint xmlns:ns1=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0"><ns1:Point><ns1:pos>10.0 15.0 20.0</ns1:pos>' + \
               b'</ns1:Point></ns1:referencePoint><ns2:heightAboveGround xmlns:ns2=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0"><ns2:HeightAboveGround><ns2:heightReference>' + \
               b'bottomOfConstruction</ns2:heightReference><ns2:value uom="m">10.0</ns2:value>' + \
               b'</ns2:HeightAboveGround></ns2:heightAboveGround></root>'
        self.assertEqual(corr, etree.tostring(rootNew))

    def test_2(self):
        rootNew = etree.Element("root")
        EADEConverter.convertBldgAttr(ifc2, ifcBldg2, rootNew, bbox, geom2)
        corr = b'<root><ns0:constructionWeight xmlns:ns0="http://www.sig3d.org/citygml/2.0/energy/1.0">medium' + \
               b'</ns0:constructionWeight><ns1:referencePoint xmlns:ns1="' + \
               b'http://www.sig3d.org/citygml/2.0/energy/1.0"><ns1:Point><ns1:pos>10.0 15.0 20.0</ns1:pos>' + \
               b'</ns1:Point></ns1:referencePoint><ns2:heightAboveGround xmlns:ns2=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0"><ns2:HeightAboveGround><ns2:heightReference>' + \
               b'bottomOfConstruction</ns2:heightReference><ns2:value uom="m">3.1415</ns2:value>' + \
               b'</ns2:HeightAboveGround></ns2:heightAboveGround></root>'
        self.assertEqual(corr, etree.tostring(rootNew))

    def test_3(self):
        rootNew = etree.Element("root")
        EADEConverter.convertBldgAttr(ifc3, ifcBldg3, rootNew, bbox, geom1)
        corr = b'<root><ns0:constructionWeight xmlns:ns0="http://www.sig3d.org/citygml/2.0/energy/1.0">light' + \
               b'</ns0:constructionWeight><ns1:referencePoint xmlns:ns1=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0"><ns1:Point><ns1:pos>10.0 15.0 20.0</ns1:pos>' + \
               b'</ns1:Point></ns1:referencePoint><ns2:heightAboveGround xmlns:ns2=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0"><ns2:HeightAboveGround><ns2:heightReference>' + \
               b'bottomOfConstruction</ns2:heightReference><ns2:value uom="m">10.0</ns2:value>' + \
               b'</ns2:HeightAboveGround></ns2:heightAboveGround></root>'
        self.assertEqual(corr, etree.tostring(rootNew))


class TestCalcUsageZone(unittest.TestCase):

    def test_1(self):
        rootNew = etree.Element("root")
        EADEConverter.calcUsageZone(ifc1, ifcProj1, ifcBldg1, rootNew, "GML_abc123", [])
        corr = 827
        self.assertEqual(corr, len(etree.tostring(rootNew)))

    def test_2(self):
        rootNew = etree.Element("root")
        EADEConverter.calcUsageZone(ifc2, ifcProj2, ifcBldg2, rootNew, "GML_abc123", [])
        corr = 175
        self.assertEqual(corr, len(etree.tostring(rootNew)))

    def test_3(self):
        rootNew = etree.Element("root")
        EADEConverter.calcUsageZone(ifc3, ifcProj3, ifcBldg3, rootNew, "GML_abc123", [])
        corr = 175
        self.assertEqual(corr, len(etree.tostring(rootNew)))


class TestConstructTempSchedule(unittest.TestCase):

    def test_1(self):
        rootNew = etree.Element("root")
        EADEConverter.constructTempSchedule(ifc1, rootNew, "Heating", ifcBldg1)
        corr = 442
        self.assertEqual(corr, len(etree.tostring(rootNew)))

    def test_2(self):
        rootNew = etree.Element("root")
        EADEConverter.constructTempSchedule(ifc1, rootNew, "Cooling", ifcBldg1)
        corr = 441
        self.assertEqual(corr, len(etree.tostring(rootNew)))

    def test_3(self):
        rootNew = etree.Element("root")
        EADEConverter.constructTempSchedule(ifc2, rootNew, "Heating", ifcBldg2)
        corr = b'<root/>'
        self.assertEqual(corr, etree.tostring(rootNew))

    def test_4(self):
        rootNew = etree.Element("root")
        EADEConverter.constructTempSchedule(ifc3, rootNew, "Cooling", ifcBldg3)
        corr = b'<root/>'
        self.assertEqual(corr, etree.tostring(rootNew))


class TestConstructEquipSchedule(unittest.TestCase):

    def test_1(self):
        rootNew = etree.Element("root")
        EADEConverter.constructEquipSchedule(rootNew, "ElectricalAppliances")
        corr = 565
        self.assertEqual(corr, len(etree.tostring(rootNew)))

    def test_2(self):
        rootNew = etree.Element("root")
        EADEConverter.constructEquipSchedule(rootNew, "LightingFacilities")
        corr = 555
        self.assertEqual(corr, len(etree.tostring(rootNew)))

    def test_3(self):
        rootNew = etree.Element("root")
        EADEConverter.constructEquipSchedule(rootNew, "DHWFacilities")
        corr = 530
        self.assertEqual(corr, len(etree.tostring(rootNew)))


class TestCalcThermalZone(unittest.TestCase):

    def test_1(self):
        rootNew = etree.Element("root")
        EADEConverter.calcThermalZone(ifc1, ifcBldg1, rootNew, [], [], 1)
        corr = 425
        self.assertEqual(corr, len(etree.tostring(rootNew)))

    def test_2(self):
        rootNew = etree.Element("root")
        EADEConverter.calcThermalZone(ifc1, ifcBldg1, rootNew, [], [], 2)
        corr = 425
        self.assertEqual(corr, len(etree.tostring(rootNew)))

    def test_3(self):
        rootNew = etree.Element("root")
        EADEConverter.calcThermalZone(ifc1, ifcBldg1, rootNew, [], [], 3)
        corr = 425
        self.assertEqual(corr, len(etree.tostring(rootNew)))

    def test_4(self):
        rootNew = etree.Element("root")
        EADEConverter.calcThermalZone(ifc2, ifcBldg2, rootNew, [], [], 3)
        corr = 425
        self.assertEqual(corr, len(etree.tostring(rootNew)))

    def test_5(self):
        rootNew = etree.Element("root")
        EADEConverter.calcThermalZone(ifc3, ifcBldg3, rootNew, [], [], 2)
        corr = 425
        self.assertEqual(corr, len(etree.tostring(rootNew)))


class TestCalcThermalBoundaries(unittest.TestCase):

    def test_1(self):
        rootNew = etree.Element("root")
        EADEConverter.calcThermalBoundaries(ifc1, [], rootNew, 2, [], "GML_abc123")
        corr = b'<root/>'
        self.assertEqual(corr, etree.tostring(rootNew))

    def test_2(self):
        rootNew = etree.Element("root")
        EADEConverter.calcThermalBoundaries(ifc1, [], rootNew, 3, [], "GML_abc123")
        corr = b'<root/>'
        self.assertEqual(corr, etree.tostring(rootNew))

    def test_3(self):
        rootNew = etree.Element("root")
        EADEConverter.calcThermalBoundaries(ifc2, [], rootNew, 2, [], "GML_abc123")
        corr = b'<root/>'
        self.assertEqual(corr, etree.tostring(rootNew))

    def test_4(self):
        rootNew = etree.Element("root")
        EADEConverter.calcThermalBoundaries(ifc3, [], rootNew, 3, [], "GML_abc123")
        corr = b'<root/>'
        self.assertEqual(corr, etree.tostring(rootNew))


class TestCalcThermalOpenings(unittest.TestCase):

    def test_1(self):
        rootNew = etree.Element("root")
        EADEConverter.calcThermalBoundaries(ifc1, [], rootNew, 3, [], [])
        corr = b'<root/>'
        self.assertEqual(corr, etree.tostring(rootNew))

    def test_2(self):
        rootNew = etree.Element("root")
        EADEConverter.calcThermalBoundaries(ifc2, [], rootNew, 3, [], [])
        corr = b'<root/>'
        self.assertEqual(corr, etree.tostring(rootNew))

    def test_3(self):
        rootNew = etree.Element("root")
        EADEConverter.calcThermalBoundaries(ifc3, [], rootNew, 3, [], [])
        corr = b'<root/>'
        self.assertEqual(corr, etree.tostring(rootNew))


class TestConvertConstructions(unittest.TestCase):

    def test_1(self):
        rootNew = etree.Element("root")
        ifcMLSs = ifc1.by_type("IfcMaterialLayerSet")
        ifcWalls, ifcWindows = ifc1.by_type("IfcWall"), ifc1.by_type("IfcWindow")
        constr = []
        for i in range(0, len(ifcMLSs)):
            constr.append(["GML_abc" + str(i), ifcMLSs[i], [ifcWalls[i]], "layer"])
        constr.append(["GML_abc123", [123, 0.8, 0.6, 0.2, 0.4, 0.7], [ifcWindows[0]], "optical"])
        result = EADEConverter.convertConstructions(rootNew, constr)
        corr = 3
        self.assertEqual(corr, len(result))
        corr = 3809
        self.assertEqual(corr, len(etree.tostring(rootNew)))

    def test_2(self):
        rootNew = etree.Element("root")
        ifcMLSs = ifc2.by_type("IfcMaterialLayerSet")
        ifcWalls, ifcWindows = ifc2.by_type("IfcWall"), ifc2.by_type("IfcWindow")
        constr = []
        for i in range(0, len(ifcMLSs)):
            constr.append(["GML_abc" + str(i), ifcMLSs[i], [ifcWalls[i]], "layer"])
        constr.append(["GML_abc123", [123, 0.8, 0.6, 0.2, 0.4, 0.7], [ifcWindows[0]], "optical"])
        result = EADEConverter.convertConstructions(rootNew, constr)
        corr = 3
        self.assertEqual(corr, len(result))
        corr = 3661
        self.assertEqual(corr, len(etree.tostring(rootNew)))

    def test_3(self):
        rootNew = etree.Element("root")
        ifcMLSs = ifc3.by_type("IfcMaterialLayerSet")
        ifcWalls, ifcWindows = ifc3.by_type("IfcWall"), ifc3.by_type("IfcWindow")
        constr = []
        for i in range(0, len(ifcMLSs)):
            constr.append(["GML_abc" + str(i), ifcMLSs[i], [ifcWalls[i]], "layer"])
        constr.append(["GML_abc123", [123, 0.8, 0.6, 0.2, 0.4, 0.7], [ifcWindows[0]], "optical"])
        result = EADEConverter.convertConstructions(rootNew, constr)
        corr = 7
        self.assertEqual(corr, len(result))
        corr = 7900
        self.assertEqual(corr, len(etree.tostring(rootNew)))


class TestConvertMaterials(unittest.TestCase):

    def test_1(self):
        rootNew = etree.Element("root")
        ifcMaterials = ifc1.by_type("IfcMaterial")
        materials = []
        for i in range(0, len(ifcMaterials)):
            materials.append(["GML_abc" + str(i), ifcMaterials[i]])
        EADEConverter.convertMaterials(rootNew, materials)
        corr = b'<root><ns0:featureMember xmlns:ns0="http://www.opengis.net/gml"><ns1:SolidMaterial xmlns:ns1=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns0:id="GML_abc0"><ns0:name>Holz</ns0:name>' + \
               b'</ns1:SolidMaterial></ns0:featureMember><ns2:featureMember xmlns:ns2="http://www.opengis.net/gml">' + \
               b'<ns3:SolidMaterial xmlns:ns3="http://www.sig3d.org/citygml/2.0/energy/1.0" ns2:id="GML_abc1">' + \
               b'<ns2:name>Leichtbeton 102890359</ns2:name><ns3:conductivity uom="W/K*m">0.13</ns3:conductivity>' + \
               b'<ns3:density uom="kg/m3">400.0</ns3:density><ns3:specificHeat uom="W/K*m">1.0</ns3:specificHeat>' + \
               b'</ns3:SolidMaterial></ns2:featureMember><ns4:featureMember xmlns:ns4="http://www.opengis.net/gml">' + \
               b'<ns5:SolidMaterial xmlns:ns5="http://www.sig3d.org/citygml/2.0/energy/1.0" ns4:id="GML_abc2">' + \
               b'<ns4:name>Radial Gradient Fill 1515460218</ns4:name><ns5:conductivity uom="W/K*m">0.0' + \
               b'</ns5:conductivity><ns5:density uom="kg/m3">0.0</ns5:density><ns5:specificHeat uom="W/K*m">0.0' + \
               b'</ns5:specificHeat></ns5:SolidMaterial></ns4:featureMember><ns6:featureMember xmlns:ns6=' + \
               b'"http://www.opengis.net/gml"><ns7:SolidMaterial xmlns:ns7=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns6:id="GML_abc3"><ns6:name>Stahlbeton 65690' + \
               b'</ns6:name><ns7:conductivity uom="W/K*m">2.0</ns7:conductivity><ns7:density uom="kg/m3">2400.0' + \
               b'</ns7:density><ns7:specificHeat uom="W/K*m">1.0</ns7:specificHeat></ns7:SolidMaterial>' + \
               b'</ns6:featureMember><ns8:featureMember xmlns:ns8="http://www.opengis.net/gml"><ns9:SolidMaterial ' + \
               b'xmlns:ns9="http://www.sig3d.org/citygml/2.0/energy/1.0" ns8:id="GML_abc4"><ns8:name>Solid' + \
               b'</ns8:name></ns9:SolidMaterial></ns8:featureMember><ns10:featureMember xmlns:ns10=' + \
               b'"http://www.opengis.net/gml"><ns11:SolidMaterial xmlns:ns11=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns10:id="GML_abc5"><ns10:name>Solid 397409098' + \
               b'</ns10:name><ns11:conductivity uom="W/K*m">0.13</ns11:conductivity><ns11:density uom="kg/m3">500.0' + \
               b'</ns11:density><ns11:specificHeat uom="W/K*m">1.6</ns11:specificHeat></ns11:SolidMaterial>' + \
               b'</ns10:featureMember></root>'
        self.assertEqual(corr, etree.tostring(rootNew))

    def test_2(self):
        rootNew = etree.Element("root")
        ifcMaterials = ifc2.by_type("IfcMaterial")
        materials = []
        for i in range(0, len(ifcMaterials)):
            materials.append(["GML_abc" + str(i), ifcMaterials[i]])
        EADEConverter.convertMaterials(rootNew, materials)
        corr = b'<root><ns0:featureMember xmlns:ns0="http://www.opengis.net/gml"><ns1:SolidMaterial xmlns:ns1=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns0:id="GML_abc0"><ns0:name>Leer</ns0:name>' + \
               b'</ns1:SolidMaterial></ns0:featureMember><ns2:featureMember xmlns:ns2="http://www.opengis.net/gml">' + \
               b'<ns3:SolidMaterial xmlns:ns3="http://www.sig3d.org/citygml/2.0/energy/1.0" ns2:id="GML_abc1">' + \
               b'<ns2:name>Stahlbeton</ns2:name></ns3:SolidMaterial></ns2:featureMember><ns4:featureMember ' + \
               b'xmlns:ns4="http://www.opengis.net/gml"><ns5:SolidMaterial xmlns:ns5=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns4:id="GML_abc2"><ns4:name>Stahlbeton 2747937872' + \
               b'</ns4:name><ns5:conductivity uom="W/K*m">0.0</ns5:conductivity><ns5:density uom="kg/m3">0.0' + \
               b'</ns5:density><ns5:specificHeat uom="W/K*m">0.0</ns5:specificHeat></ns5:SolidMaterial>' + \
               b'</ns4:featureMember><ns6:featureMember xmlns:ns6="http://www.opengis.net/gml"><ns7:SolidMaterial ' + \
               b'xmlns:ns7="http://www.sig3d.org/citygml/2.0/energy/1.0" ns6:id="GML_abc3"><ns6:name>' + \
               b'Kalksandstein 2816491304</ns6:name><ns7:conductivity uom="W/K*m">0.0</ns7:conductivity>' + \
               b'<ns7:density uom="kg/m3">0.0</ns7:density><ns7:specificHeat uom="W/K*m">0.0</ns7:specificHeat>' + \
               b'</ns7:SolidMaterial></ns6:featureMember><ns8:featureMember xmlns:ns8=' + \
               b'"http://www.opengis.net/gml"><ns9:SolidMaterial xmlns:ns9=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns8:id="GML_abc4"><ns8:name>Luftschicht</ns8:name>' + \
               b'</ns9:SolidMaterial></ns8:featureMember><ns10:featureMember xmlns:ns10=' + \
               b'"http://www.opengis.net/gml"><ns11:SolidMaterial xmlns:ns11=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns10:id="GML_abc5"><ns10:name>' + \
               b'Kalksandstein 2774059904</ns10:name><ns11:conductivity uom="W/K*m">0.0</ns11:conductivity>' + \
               b'<ns11:density uom="kg/m3">0.0</ns11:density><ns11:specificHeat uom="W/K*m">0.0</ns11:specificHeat>' + \
               b'</ns11:SolidMaterial></ns10:featureMember><ns12:featureMember xmlns:ns12=' + \
               b'"http://www.opengis.net/gml"><ns13:SolidMaterial xmlns:ns13=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns12:id="GML_abc6"><ns12:name>Aluminium 131198' + \
               b'</ns12:name><ns13:conductivity uom="W/K*m">160.0</ns13:conductivity><ns13:density uom="kg/m3">' + \
               b'2800.0</ns13:density><ns13:specificHeat uom="W/K*m">880.0</ns13:specificHeat></ns13:SolidMaterial>' + \
               b'</ns12:featureMember></root>'
        self.assertEqual(corr, etree.tostring(rootNew))

    def test_3(self):
        rootNew = etree.Element("root")
        ifcMaterials = ifc3.by_type("IfcMaterial")
        materials = []
        for i in range(0, len(ifcMaterials)):
            materials.append(["GML_abc" + str(i), ifcMaterials[i]])
        EADEConverter.convertMaterials(rootNew, materials)
        corr = b'<root><ns0:featureMember xmlns:ns0="http://www.opengis.net/gml"><ns1:SolidMaterial xmlns:ns1=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns0:id="GML_abc0"><ns0:name>Holz</ns0:name>' + \
               b'</ns1:SolidMaterial></ns0:featureMember><ns2:featureMember xmlns:ns2="http://www.opengis.net/gml">' + \
               b'<ns3:SolidMaterial xmlns:ns3="http://www.sig3d.org/citygml/2.0/energy/1.0" ns2:id="GML_abc1">' + \
               b'<ns2:name>Stahlbeton 2784800804</ns2:name></ns3:SolidMaterial></ns2:featureMember>' + \
               b'<ns4:featureMember xmlns:ns4="http://www.opengis.net/gml"><ns5:SolidMaterial xmlns:ns5=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns4:id="GML_abc2"><ns4:name>Stahlbeton 2816491304' + \
               b'</ns4:name></ns5:SolidMaterial></ns4:featureMember><ns6:featureMember xmlns:ns6=' + \
               b'"http://www.opengis.net/gml"><ns7:SolidMaterial xmlns:ns7=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns6:id="GML_abc3"><ns6:name>Glas</ns6:name>' + \
               b'</ns7:SolidMaterial></ns6:featureMember><ns8:featureMember xmlns:ns8="http://www.opengis.net/gml">' + \
               b'<ns9:SolidMaterial xmlns:ns9="http://www.sig3d.org/citygml/2.0/energy/1.0" ns8:id="GML_abc4">' + \
               b'<ns8:name>Kalksandstein 268899148</ns8:name></ns9:SolidMaterial></ns8:featureMember>' + \
               b'<ns10:featureMember xmlns:ns10="http://www.opengis.net/gml"><ns11:SolidMaterial xmlns:ns11=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns10:id="GML_abc5"><ns10:name>Gips 275646950' + \
               b'</ns10:name></ns11:SolidMaterial></ns10:featureMember><ns12:featureMember xmlns:ns12=' + \
               b'"http://www.opengis.net/gml"><ns13:SolidMaterial xmlns:ns13=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns12:id="GML_abc6"><ns12:name>Stahl 269029580' + \
               b'</ns12:name></ns13:SolidMaterial></ns12:featureMember><ns14:featureMember xmlns:ns14=' + \
               b'"http://www.opengis.net/gml"><ns15:SolidMaterial xmlns:ns15=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns14:id="GML_abc7"><ns14:name>Aluminium 587913947' + \
               b'</ns14:name></ns15:SolidMaterial></ns14:featureMember><ns16:featureMember xmlns:ns16=' + \
               b'"http://www.opengis.net/gml"><ns17:SolidMaterial xmlns:ns17=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns16:id="GML_abc8"><ns16:name>' + \
               b'Isolierung, hart 275646950</ns16:name></ns17:SolidMaterial></ns16:featureMember>' + \
               b'<ns18:featureMember xmlns:ns18="http://www.opengis.net/gml"><ns19:SolidMaterial xmlns:ns19=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns18:id="GML_abc9"><ns18:name>' + \
               b'Beton, tragend 268571148</ns18:name></ns19:SolidMaterial></ns18:featureMember>' + \
               b'<ns20:featureMember xmlns:ns20="http://www.opengis.net/gml"><ns21:SolidMaterial xmlns:ns21=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns20:id="GML_abc10"><ns20:name>Massiv 2813929878' + \
               b'</ns20:name></ns21:SolidMaterial></ns20:featureMember><ns22:featureMember xmlns:ns22=' + \
               b'"http://www.opengis.net/gml"><ns23:SolidMaterial xmlns:ns23=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns22:id="GML_abc11"><ns22:name>Stahl</ns22:name>' + \
               b'</ns23:SolidMaterial></ns22:featureMember></root>'
        self.assertEqual(corr, etree.tostring(rootNew))


if __name__ == '__main__':
    unittest.main()
