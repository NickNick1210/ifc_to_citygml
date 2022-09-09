# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (09.09.2022)

Unit-Tests für die Modelklasse EADEConverter
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
from models.utilitiesIfc import UtilitiesIfc
from models.objects.surface import Surface
from models.objects.construction import Construction
from models.objects.material import Material

#####

LOGGER = logging.getLogger('QGIS')

# IFC-Elemente
ifc1 = ifcopenshell.open(r"data/IFC_test.ifc")
ifcBldg1 = ifc1.by_type("IfcBuilding")[0]
ifcSite1 = ifc1.by_type("IfcSite")[0]
ifcProj1 = ifc1.by_type("IfcProject")[0]
ifcWalls1 = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcWall", result=[])
ifcWindows1 = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcWindow", result=[])
ifcMLS1 = ifc1.by_type("IfcMaterialLayerSet")[0]

ifc2 = ifcopenshell.open(r"data/IFC_test3.ifc")
ifcBldg2 = ifc2.by_type("IfcBuilding")[0]
ifcSite2 = ifc2.by_type("IfcSite")[0]
ifcProj2 = ifc2.by_type("IfcProject")[0]
ifcWalls2 = UtilitiesIfc.findElement(ifc2, ifcBldg2, "IfcWall", result=[])
ifcWindows2 = UtilitiesIfc.findElement(ifc2, ifcBldg2, "IfcWindow", result=[])
ifcMLS2 = ifc2.by_type("IfcMaterialLayerSet")[0]

ifc3 = ifcopenshell.open(r"data/IFC_test4.ifc")
ifcBldg3 = ifc3.by_type("IfcBuilding")[0]
ifcSite3 = ifc3.by_type("IfcSite")[0]
ifcProj3 = ifc3.by_type("IfcProject")[0]
ifcWalls3 = UtilitiesIfc.findElement(ifc3, ifcBldg3, "IfcWall", result=[])
ifcWindows3 = UtilitiesIfc.findElement(ifc3, ifcBldg3, "IfcWindow", result=[])
ifcMLS3 = ifc3.by_type("IfcMaterialLayerSet")[0]

# Geometrien
bbox = (10, 10, 10, 20, 20, 20)
geom1 = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 20 10, 20 20 10, 20 10 10, 10 10 10))")
geom2 = ogr.CreateGeometryFromWkt("Polygon((10 10 3.1415, 10 20 3.1415, 20 20 3.1415, 20 10 10, 10 10 3.1415))")
geom3 = ogr.CreateGeometryFromWkt("Polygon((0 0, 0 20, 20 20, 20 0, 0 0),(5 5, 5 15, 15 15, 15 5, 5 5))")

# Plugin
surface1 = Surface([geom1, geom2], "Wand-ABC123", ifcWalls1[0], "Wall")
surface2 = Surface([geom3], "Wand-XYZ_äöüß", ifcWalls1[1], "Wall")
constr1 = Construction("GML_ABC123", ifcMLS1, None, ifcWalls1, "layer")
constr2 = Construction("GML_XYZ_äöüß", ifcMLS2, None, ifcWalls2, "layer")
constr3 = Construction("GML_987_XYZ", ifcMLS3, None, ifcWalls3, "layer")
constr4 = Construction("GML_987_XYZ", None, [3.0, 0.2, 0.15, 0.8, 0.85, 0.7], ifcWindows1, "optical")
constr5 = Construction("GML_ABC123", None, [3.1415, 0.25, 0.2, 0.75, 0.8, 0.7123], ifcWindows2, "optical")
constr6 = Construction("GML_XYZ_äöüß", None, [2.4, 0.15, 0.1, 0.85, 0.9, 0.6], ifcWindows3, "optical")
ifcMats1, ifcMats2, ifcMats3 = ifc1.by_type("IfcMaterial"), ifc2.by_type("IfcMaterial"), ifc3.by_type("IfcMaterial")
mats1, mats2, mats3 = [], [], []
for i in range(0, len(ifcMats1)):
    mats1.append(Material("GML_abc" + str(i), ifcMats1[i]))
for i in range(0, len(ifcMats2)):
    mats2.append(Material("GML_xyz" + str(i), ifcMats2[i]))
for i in range(0, len(ifcMats3)):
    mats3.append(Material("GML_" + str(i), ifcMats3[i]))


class TestConvertWeatherData(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        EADEConverter.convertWeatherData(ifcProj1, ifcSite1, root, bbox)
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
        self.assertEqual(corr, etree.tostring(root))

    def test_2(self):
        root = etree.Element("root")
        EADEConverter.convertWeatherData(ifcProj2, ifcSite2, root, bbox)
        self.assertEqual(b'<root/>', etree.tostring(root))

    def test_3(self):
        root = etree.Element("root")
        EADEConverter.convertWeatherData(ifcProj3, ifcSite3, root, bbox)
        self.assertEqual(b'<root/>', etree.tostring(root))


class TestConvertBldgAttr(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        EADEConverter.convertBldgAttr(ifc1, ifcBldg1, root, bbox, geom1)
        corr = b'<root><ns0:constructionWeight xmlns:ns0="http://www.sig3d.org/citygml/2.0/energy/1.0">medium' + \
               b'</ns0:constructionWeight><ns1:referencePoint xmlns:ns1=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0"><ns1:Point><ns1:pos>10.0 15.0 20.0</ns1:pos>' + \
               b'</ns1:Point></ns1:referencePoint><ns2:heightAboveGround xmlns:ns2=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0"><ns2:HeightAboveGround><ns2:heightReference>' + \
               b'bottomOfConstruction</ns2:heightReference><ns2:value uom="m">10.0</ns2:value>' + \
               b'</ns2:HeightAboveGround></ns2:heightAboveGround></root>'
        self.assertEqual(corr, etree.tostring(root))

    def test_2(self):
        root = etree.Element("root")
        EADEConverter.convertBldgAttr(ifc2, ifcBldg2, root, bbox, geom2)
        corr = b'<root><ns0:constructionWeight xmlns:ns0="http://www.sig3d.org/citygml/2.0/energy/1.0">medium' + \
               b'</ns0:constructionWeight><ns1:referencePoint xmlns:ns1="' + \
               b'http://www.sig3d.org/citygml/2.0/energy/1.0"><ns1:Point><ns1:pos>10.0 15.0 20.0</ns1:pos>' + \
               b'</ns1:Point></ns1:referencePoint><ns2:heightAboveGround xmlns:ns2=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0"><ns2:HeightAboveGround><ns2:heightReference>' + \
               b'bottomOfConstruction</ns2:heightReference><ns2:value uom="m">3.1415</ns2:value>' + \
               b'</ns2:HeightAboveGround></ns2:heightAboveGround></root>'
        self.assertEqual(corr, etree.tostring(root))

    def test_3(self):
        root = etree.Element("root")
        EADEConverter.convertBldgAttr(ifc3, ifcBldg3, root, bbox, geom1)
        corr = b'<root><ns0:constructionWeight xmlns:ns0="http://www.sig3d.org/citygml/2.0/energy/1.0">light' + \
               b'</ns0:constructionWeight><ns1:referencePoint xmlns:ns1=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0"><ns1:Point><ns1:pos>10.0 15.0 20.0</ns1:pos>' + \
               b'</ns1:Point></ns1:referencePoint><ns2:heightAboveGround xmlns:ns2=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0"><ns2:HeightAboveGround><ns2:heightReference>' + \
               b'bottomOfConstruction</ns2:heightReference><ns2:value uom="m">10.0</ns2:value>' + \
               b'</ns2:HeightAboveGround></ns2:heightAboveGround></root>'
        self.assertEqual(corr, etree.tostring(root))


class TestCalcUsageZone(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        EADEConverter.calcUsageZone(ifc1, ifcProj1, ifcBldg1, root, "GML_abc123", [])
        self.assertEqual(827, len(etree.tostring(root)))

    def test_2(self):
        root = etree.Element("root")
        EADEConverter.calcUsageZone(ifc2, ifcProj2, ifcBldg2, root, "GML_abc123", [])
        self.assertEqual(175, len(etree.tostring(root)))

    def test_3(self):
        root = etree.Element("root")
        EADEConverter.calcUsageZone(ifc3, ifcProj3, ifcBldg3, root, "GML_abc123", [])
        self.assertEqual(175, len(etree.tostring(root)))


class TestConstructTempSchedule(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        EADEConverter.constructTempSchedule(ifc1, root, "Heating", ifcBldg1)
        self.assertEqual(442, len(etree.tostring(root)))

    def test_2(self):
        root = etree.Element("root")
        EADEConverter.constructTempSchedule(ifc1, root, "Cooling", ifcBldg1)
        self.assertEqual(441, len(etree.tostring(root)))

    def test_3(self):
        root = etree.Element("root")
        EADEConverter.constructTempSchedule(ifc2, root, "Heating", ifcBldg2)
        self.assertEqual(b'<root/>', etree.tostring(root))

    def test_4(self):
        root = etree.Element("root")
        EADEConverter.constructTempSchedule(ifc3, root, "Cooling", ifcBldg3)
        self.assertEqual(b'<root/>', etree.tostring(root))


class TestConstructEquipSchedule(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        EADEConverter.constructEquipSchedule(root, "ElectricalAppliances")
        self.assertEqual(565, len(etree.tostring(root)))

    def test_2(self):
        root = etree.Element("root")
        EADEConverter.constructEquipSchedule(root, "LightingFacilities")
        self.assertEqual(555, len(etree.tostring(root)))

    def test_3(self):
        root = etree.Element("root")
        EADEConverter.constructEquipSchedule(root, "DHWFacilities")
        self.assertEqual(530, len(etree.tostring(root)))


class TestCalcThermalZone(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        EADEConverter.calcThermalZone(ifc1, ifcBldg1, root, [], [surface1, surface2], 1)
        self.assertEqual(425, len(etree.tostring(root)))

    def test_2(self):
        root = etree.Element("root")
        EADEConverter.calcThermalZone(ifc1, ifcBldg1, root, [], [surface2, surface1], 2)
        self.assertEqual(425, len(etree.tostring(root)))

    def test_3(self):
        root = etree.Element("root")
        EADEConverter.calcThermalZone(ifc1, ifcBldg1, root, [], [surface1, surface2], 3)
        self.assertEqual(425, len(etree.tostring(root)))

    def test_4(self):
        root = etree.Element("root")
        EADEConverter.calcThermalZone(ifc2, ifcBldg2, root, [], [surface2, surface1], 3)
        self.assertEqual(425, len(etree.tostring(root)))

    def test_5(self):
        root = etree.Element("root")
        EADEConverter.calcThermalZone(ifc3, ifcBldg3, root, [], [surface1, surface2], 2)
        self.assertEqual(425, len(etree.tostring(root)))


class TestCalcThermalBoundaries(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        EADEConverter.calcThermalBoundaries(ifc1, [], root, 2, [surface1, surface2], "GML_abc123")
        self.assertEqual(b'<root/>', etree.tostring(root))

    def test_2(self):
        root = etree.Element("root")
        EADEConverter.calcThermalBoundaries(ifc1, [], root, 3, [surface2, surface1], "GML_abc123")
        self.assertEqual(b'<root/>', etree.tostring(root))

    def test_3(self):
        root = etree.Element("root")
        EADEConverter.calcThermalBoundaries(ifc2, [], root, 2, [surface2, surface1], "GML_abc123")
        self.assertEqual(b'<root/>', etree.tostring(root))

    def test_4(self):
        root = etree.Element("root")
        EADEConverter.calcThermalBoundaries(ifc3, [], root, 3, [surface1, surface2], "GML_abc123")
        self.assertEqual(b'<root/>', etree.tostring(root))


class TestCalcThermalOpenings(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        EADEConverter.calcThermalBoundaries(ifc1, [], root, 3, [surface1, surface2], [constr1, constr4])
        self.assertEqual(b'<root/>', etree.tostring(root))

    def test_2(self):
        root = etree.Element("root")
        EADEConverter.calcThermalBoundaries(ifc2, [], root, 3, [surface2, surface1], [constr2, constr5])
        self.assertEqual(b'<root/>', etree.tostring(root))

    def test_3(self):
        root = etree.Element("root")
        EADEConverter.calcThermalBoundaries(ifc3, [], root, 3, [surface1, surface2], [constr3, constr6])
        self.assertEqual(b'<root/>', etree.tostring(root))


class TestConvertConstructions(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        result = EADEConverter.convertConstructions(root, [constr1, constr4])
        self.assertEqual(1, len(result))
        self.assertEqual(1789, len(etree.tostring(root)))

    def test_2(self):
        root = etree.Element("root")
        result = EADEConverter.convertConstructions(root, [constr2, constr5])
        self.assertEqual(1, len(result))
        self.assertEqual(1773, len(etree.tostring(root)))

    def test_3(self):
        root = etree.Element("root")
        result = EADEConverter.convertConstructions(root, [constr3, constr6])
        self.assertEqual(1, len(result))
        self.assertEqual(1770, len(etree.tostring(root)))


class TestConvertMaterials(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        EADEConverter.convertMaterials(root, mats1)
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
        self.assertEqual(corr, etree.tostring(root))

    def test_2(self):
        root = etree.Element("root")
        EADEConverter.convertMaterials(root, mats2)
        corr = b'<root><ns0:featureMember xmlns:ns0="http://www.opengis.net/gml"><ns1:SolidMaterial xmlns:ns1=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns0:id="GML_xyz0"><ns0:name>Leer</ns0:name>' + \
               b'</ns1:SolidMaterial></ns0:featureMember><ns2:featureMember xmlns:ns2="http://www.opengis.net/gml">' + \
               b'<ns3:SolidMaterial xmlns:ns3="http://www.sig3d.org/citygml/2.0/energy/1.0" ns2:id="GML_xyz1">' + \
               b'<ns2:name>Stahlbeton</ns2:name></ns3:SolidMaterial></ns2:featureMember><ns4:featureMember ' + \
               b'xmlns:ns4="http://www.opengis.net/gml"><ns5:SolidMaterial xmlns:ns5=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns4:id="GML_xyz2"><ns4:name>Stahlbeton 2747937872' + \
               b'</ns4:name><ns5:conductivity uom="W/K*m">0.0</ns5:conductivity><ns5:density uom="kg/m3">0.0' + \
               b'</ns5:density><ns5:specificHeat uom="W/K*m">0.0</ns5:specificHeat></ns5:SolidMaterial>' + \
               b'</ns4:featureMember><ns6:featureMember xmlns:ns6="http://www.opengis.net/gml"><ns7:SolidMaterial ' + \
               b'xmlns:ns7="http://www.sig3d.org/citygml/2.0/energy/1.0" ns6:id="GML_xyz3"><ns6:name>' + \
               b'Kalksandstein 2816491304</ns6:name><ns7:conductivity uom="W/K*m">0.0</ns7:conductivity>' + \
               b'<ns7:density uom="kg/m3">0.0</ns7:density><ns7:specificHeat uom="W/K*m">0.0</ns7:specificHeat>' + \
               b'</ns7:SolidMaterial></ns6:featureMember><ns8:featureMember xmlns:ns8=' + \
               b'"http://www.opengis.net/gml"><ns9:SolidMaterial xmlns:ns9=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns8:id="GML_xyz4"><ns8:name>Luftschicht</ns8:name>' + \
               b'</ns9:SolidMaterial></ns8:featureMember><ns10:featureMember xmlns:ns10=' + \
               b'"http://www.opengis.net/gml"><ns11:SolidMaterial xmlns:ns11=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns10:id="GML_xyz5"><ns10:name>' + \
               b'Kalksandstein 2774059904</ns10:name><ns11:conductivity uom="W/K*m">0.0</ns11:conductivity>' + \
               b'<ns11:density uom="kg/m3">0.0</ns11:density><ns11:specificHeat uom="W/K*m">0.0</ns11:specificHeat>' + \
               b'</ns11:SolidMaterial></ns10:featureMember><ns12:featureMember xmlns:ns12=' + \
               b'"http://www.opengis.net/gml"><ns13:SolidMaterial xmlns:ns13=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns12:id="GML_xyz6"><ns12:name>Aluminium 131198' + \
               b'</ns12:name><ns13:conductivity uom="W/K*m">160.0</ns13:conductivity><ns13:density uom="kg/m3">' + \
               b'2800.0</ns13:density><ns13:specificHeat uom="W/K*m">880.0</ns13:specificHeat></ns13:SolidMaterial>' + \
               b'</ns12:featureMember></root>'
        self.assertEqual(corr, etree.tostring(root))

    def test_3(self):
        root = etree.Element("root")
        EADEConverter.convertMaterials(root, mats3)
        corr = b'<root><ns0:featureMember xmlns:ns0="http://www.opengis.net/gml"><ns1:SolidMaterial xmlns:ns1=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns0:id="GML_0"><ns0:name>Holz</ns0:name>' + \
               b'</ns1:SolidMaterial></ns0:featureMember><ns2:featureMember xmlns:ns2="http://www.opengis.net/gml">' + \
               b'<ns3:SolidMaterial xmlns:ns3="http://www.sig3d.org/citygml/2.0/energy/1.0" ns2:id="GML_1">' + \
               b'<ns2:name>Stahlbeton 2784800804</ns2:name></ns3:SolidMaterial></ns2:featureMember>' + \
               b'<ns4:featureMember xmlns:ns4="http://www.opengis.net/gml"><ns5:SolidMaterial xmlns:ns5=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns4:id="GML_2"><ns4:name>Stahlbeton 2816491304' + \
               b'</ns4:name></ns5:SolidMaterial></ns4:featureMember><ns6:featureMember xmlns:ns6=' + \
               b'"http://www.opengis.net/gml"><ns7:SolidMaterial xmlns:ns7=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns6:id="GML_3"><ns6:name>Glas</ns6:name>' + \
               b'</ns7:SolidMaterial></ns6:featureMember><ns8:featureMember xmlns:ns8="http://www.opengis.net/gml">' + \
               b'<ns9:SolidMaterial xmlns:ns9="http://www.sig3d.org/citygml/2.0/energy/1.0" ns8:id="GML_4">' + \
               b'<ns8:name>Kalksandstein 268899148</ns8:name></ns9:SolidMaterial></ns8:featureMember>' + \
               b'<ns10:featureMember xmlns:ns10="http://www.opengis.net/gml"><ns11:SolidMaterial xmlns:ns11=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns10:id="GML_5"><ns10:name>Gips 275646950' + \
               b'</ns10:name></ns11:SolidMaterial></ns10:featureMember><ns12:featureMember xmlns:ns12=' + \
               b'"http://www.opengis.net/gml"><ns13:SolidMaterial xmlns:ns13=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns12:id="GML_6"><ns12:name>Stahl 269029580' + \
               b'</ns12:name></ns13:SolidMaterial></ns12:featureMember><ns14:featureMember xmlns:ns14=' + \
               b'"http://www.opengis.net/gml"><ns15:SolidMaterial xmlns:ns15=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns14:id="GML_7"><ns14:name>Aluminium 587913947' + \
               b'</ns14:name></ns15:SolidMaterial></ns14:featureMember><ns16:featureMember xmlns:ns16=' + \
               b'"http://www.opengis.net/gml"><ns17:SolidMaterial xmlns:ns17=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns16:id="GML_8"><ns16:name>' + \
               b'Isolierung, hart 275646950</ns16:name></ns17:SolidMaterial></ns16:featureMember>' + \
               b'<ns18:featureMember xmlns:ns18="http://www.opengis.net/gml"><ns19:SolidMaterial xmlns:ns19=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns18:id="GML_9"><ns18:name>' + \
               b'Beton, tragend 268571148</ns18:name></ns19:SolidMaterial></ns18:featureMember>' + \
               b'<ns20:featureMember xmlns:ns20="http://www.opengis.net/gml"><ns21:SolidMaterial xmlns:ns21=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns20:id="GML_10"><ns20:name>Massiv 2813929878' + \
               b'</ns20:name></ns21:SolidMaterial></ns20:featureMember><ns22:featureMember xmlns:ns22=' + \
               b'"http://www.opengis.net/gml"><ns23:SolidMaterial xmlns:ns23=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0" ns22:id="GML_11"><ns22:name>Stahl</ns22:name>' + \
               b'</ns23:SolidMaterial></ns22:featureMember></root>'
        self.assertEqual(corr, etree.tostring(root))


if __name__ == '__main__':
    unittest.main()
