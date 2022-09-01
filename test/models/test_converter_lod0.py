# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)

Unit-Test für die Modelklasse LoD0Converter
 ***************************************************************************/
"""

# Standard-Bibliotheken
import unittest
import logging
import sys
import os

# IFC-Bibliotheken
import ifcopenshell

# XML-Bibliotheken
from lxml import etree

# Geo-Bibliotheken
from osgeo import ogr

# Plugin
from mock_model import Model
from mock_converter import Converter
sys.path.insert(0, '..')
from models.converter_lod0 import LoD0Converter
from models.transformer import Transformer

#####

LOGGER = logging.getLogger('QGIS')

# IFC-Elemente
dirPath = os.path.dirname(os.path.abspath(__file__))
inPath1 = dirPath[0:dirPath.rindex("\\")+1] + "data\\IFC_test.ifc"
outPath1 = dirPath[0:dirPath.rindex("\\")+1] + "data\\CityGML_test.gml"
inPath2 = dirPath[0:dirPath.rindex("\\")+1] + "data\\IFC_test3.ifc"
outPath2 = dirPath[0:dirPath.rindex("\\")+1] + "data\\CityGML_test3.gml"

dataPath1 = r"data/IFC_test.ifc"
ifc1 = ifcopenshell.open(dataPath1)
trans1 = Transformer(ifc1)
ifcBldg1 = ifc1.by_type("IfcBuilding")[0]
ifcSite1 = ifc1.by_type("IfcSite")[0]
ifcProj1 = ifc1.by_type("IfcProject")[0]

dataPath2 = r"data/IFC_test3.ifc"
ifc2 = ifcopenshell.open(dataPath2)
trans2 = Transformer(ifc2)
ifcBldg2 = ifc2.by_type("IfcBuilding")[0]
ifcSite2 = ifc2.by_type("IfcSite")[0]
ifcProj2 = ifc2.by_type("IfcProject")[0]

dataPath3 = r"data/IFC_test4.ifc"
ifc3 = ifcopenshell.open(dataPath3)
trans3 = Transformer(ifc3)
ifcBldg3 = ifc3.by_type("IfcBuilding")[0]
ifcSite3 = ifc3.by_type("IfcSite")[0]
ifcProj3 = ifc3.by_type("IfcProject")[0]

# XML-Elemente
root = etree.Element("root")

# Geometrien
bbox = (10, 10, 10, 20, 20, 20)
geom1 = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 20 10, 20 20 10, 20 10 10, 10 10 10))")
geom2 = ogr.CreateGeometryFromWkt("Polygon((10 10 3.1415, 10 20 3.1415, 20 20 3.1415, 20 10 10, 10 10 3.1415))")


class TestConstructor(unittest.TestCase):

    def test_1(self):
        model = Model()
        conv = Converter()
        result = LoD0Converter(model, conv, ifc1, "Test123", trans1, False)
        self.assertEqual(model, result.parent)
        self.assertEqual(conv, result.task)
        self.assertEqual(ifc1, result.ifc)
        self.assertEqual("Test123", result.name)
        self.assertEqual(trans1, result.trans)
        self.assertFalse(result.eade)
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.geom)))
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.bldgGeom)))
        self.assertEqual(10, result.progress)

    def test_2(self):
        model = Model()
        conv = Converter()
        result = LoD0Converter(model, conv, ifc2, "TestABC", trans2, True)
        self.assertEqual(model, result.parent)
        self.assertEqual(conv, result.task)
        self.assertEqual(ifc2, result.ifc)
        self.assertEqual("TestABC", result.name)
        self.assertEqual(trans2, result.trans)
        self.assertTrue(result.eade)
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.geom)))
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.bldgGeom)))
        self.assertEqual(10, result.progress)


class TestConvert(unittest.TestCase):

    def test_1(self):
        rootNew = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc1, "Test123", trans1, True)
        result = lod0Conv.convert(rootNew)
        corr = 5028
        self.assertEqual(corr, len(etree.tostring(result)))

    def test_2(self):
        rootNew = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc2, "TestABC", trans2, False)
        result = lod0Conv.convert(rootNew)
        corr = 2882
        self.assertEqual(corr, len(etree.tostring(result)))

    def test_3(self):
        rootNew = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc3, "ÄÖÜß", trans3, False)
        result = lod0Conv.convert(rootNew)
        corr = 6587
        self.assertEqual(corr, len(etree.tostring(result)))


class TestConvertFootPrint(unittest.TestCase):

    def test_1(self):
        rootNew = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc1, "Test123", trans1, True)
        result = lod0Conv.convertFootPrint(ifcBldg1, rootNew)
        corr = b'<root><ns0:lod0FootPrint xmlns:ns0="http://www.opengis.net/citygml/building/2.0"><ns1:MultiSurface' + \
               b' xmlns:ns1="http://www.opengis.net/gml"><ns1:surfaceMember><ns1:Polygon><ns1:outerBoundaryIs>' + \
               b'<ns1:LinearRing><ns1:coordinates>458870.063285681,5438773.62904949,110 ' + \
               b'458862.40284125,5438780.05692559,110 458870.116292566,5438789.24945891,110 ' + \
               b'458877.776736998,5438782.82158281,110 458870.063285681,5438773.62904949,110</ns1:coordinates>' + \
               b'</ns1:LinearRing></ns1:outerBoundaryIs></ns1:Polygon></ns1:surfaceMember></ns1:MultiSurface>' + \
               b'</ns0:lod0FootPrint></root>'
        self.assertEqual(corr, etree.tostring(rootNew))
        corr = "POLYGON ((458870.063285681 5438773.62904949 110,458862.40284125 5438780.05692559 110," + \
               "458870.116292566 5438789.24945891 110,458877.776736998 5438782.82158281 110," + \
               "458870.063285681 5438773.62904949 110))"
        self.assertEqual(corr, result.ExportToWkt())

    def test_2(self):
        rootNew = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc2, "TestABC", trans2, False)
        result = lod0Conv.convertFootPrint(ifcBldg2, rootNew)
        corr = b'<root><ns0:lod0FootPrint xmlns:ns0="http://www.opengis.net/citygml/building/2.0"><ns1:MultiSurface' + \
               b' xmlns:ns1="http://www.opengis.net/gml"><ns1:surfaceMember><ns1:Polygon><ns1:outerBoundaryIs>' + \
               b'<ns1:LinearRing><ns1:coordinates>479356.600506348,5444183.43024925,-3 479356.600506348,' + \
               b'5444185.43024925,-3 479362.600506348,5444185.43024925,-3 479362.600506348,5444183.43024925,-3 ' + \
               b'479380.600506348,5444183.43024925,-3 479380.600506348,5444171.43024925,-3 479363.100506348,' + \
               b'5444171.43024925,-3 479363.100506348,5444167.43024925,-3 479356.100506348,5444167.43024925,-3 ' + \
               b'479356.100506348,5444171.43024925,-3 479338.600506348,5444171.43024925,-3 479338.600506348,' + \
               b'5444183.43024925,-3 479356.600506348,5444183.43024925,-3</ns1:coordinates></ns1:LinearRing>' + \
               b'</ns1:outerBoundaryIs></ns1:Polygon></ns1:surfaceMember></ns1:MultiSurface></ns0:lod0FootPrint></root>'
        self.assertEqual(corr, etree.tostring(rootNew))
        corr = "POLYGON ((479356.600506348 5444183.43024925 -3,479356.600506348 5444185.43024925 -3," + \
               "479362.600506348 5444185.43024925 -3,479362.600506348 5444183.43024925 -3,479380.600506348 " + \
               "5444183.43024925 -3,479380.600506348 5444171.43024925 -3,479363.100506348 5444171.43024925 -3," + \
               "479363.100506348 5444167.43024925 -3,479356.100506348 5444167.43024925 -3,479356.100506348 " + \
               "5444171.43024925 -3,479338.600506348 5444171.43024925 -3,479338.600506348 5444183.43024925 -3," + \
               "479356.600506348 5444183.43024925 -3))"
        self.assertEqual(corr, result.ExportToWkt())

    def test_3(self):
        rootNew = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc3, "Test123", trans3, False)
        result = lod0Conv.convertFootPrint(ifcBldg3, rootNew)
        corr = 3584
        self.assertEqual(corr, len(etree.tostring(rootNew)))
        corr = 85
        self.assertEqual(corr, result.GetGeometryRef(0).GetPointCount())


class TestConvertRoofEdge(unittest.TestCase):

    def test_1(self):
        rootNew = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc1, "Test123", trans1, True)
        lod0Conv.convertRoofEdge(ifcBldg1, rootNew)
        corr = b'<root><ns0:lod0RoofEdge xmlns:ns0="http://www.opengis.net/citygml/building/2.0"><ns1:MultiSurface ' + \
               b'xmlns:ns1="http://www.opengis.net/gml"><ns1:surfaceMember><ns1:Polygon><ns1:outerBoundaryIs>' + \
               b'<ns1:LinearRing><ns1:coordinates>458878.864175246,5438782.56181742,113 458870.50793632,' + \
               b'5438772.60323966,113 458861.315403002,5438780.31669098,113 458869.671641928,5438790.27526874,113 ' + \
               b'458878.864175246,5438782.56181742,113</ns1:coordinates></ns1:LinearRing></ns1:outerBoundaryIs>' + \
               b'</ns1:Polygon></ns1:surfaceMember></ns1:MultiSurface></ns0:lod0RoofEdge></root>'
        self.assertEqual(corr, etree.tostring(rootNew))

    def test_2(self):
        rootNew = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc2, "Test123", trans2, True)
        lod0Conv.convertRoofEdge(ifcBldg2, rootNew)
        corr = b'<root><ns0:lod0RoofEdge xmlns:ns0="http://www.opengis.net/citygml/building/2.0"><ns1:MultiSurface ' + \
               b'xmlns:ns1="http://www.opengis.net/gml"><ns1:surfaceMember><ns1:Polygon><ns1:outerBoundaryIs>' + \
               b'<ns1:LinearRing><ns1:coordinates>479337.600506348,5444176.43024925,9 479337.600506348,' + \
               b'5444184.43024925,9 479355.600506348,5444184.43024925,9 479355.600506348,5444186.43024925,9 ' + \
               b'479363.600506348,5444186.43024925,9 479363.600506348,5444184.43024925,9 479381.600506348,' + \
               b'5444184.43024925,9 479381.600506348,5444170.43024925,9 479337.600506348,5444170.43024925,9 ' + \
               b'479337.600506348,5444176.43024925,9</ns1:coordinates></ns1:LinearRing></ns1:outerBoundaryIs>' + \
               b'</ns1:Polygon></ns1:surfaceMember></ns1:MultiSurface></ns0:lod0RoofEdge></root>'
        self.assertEqual(corr, etree.tostring(rootNew))

    def test_3(self):
        rootNew = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc3, "Test123", trans3, True)
        lod0Conv.convertRoofEdge(ifcBldg3, rootNew)
        corr = 2091
        self.assertEqual(corr, len(etree.tostring(rootNew)))


if __name__ == '__main__':
    unittest.main()
