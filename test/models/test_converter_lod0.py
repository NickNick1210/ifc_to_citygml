# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)

Unit-Tests für die Modelklasse LoD0Converter
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

# Plugin
from mock_model import Model
from mock_converter import Converter
sys.path.insert(0, '..')
from models.converter_lod0 import LoD0Converter
from models.transformer import Transformer

#####

LOGGER = logging.getLogger('QGIS')

# IFC-Elemente
ifc1 = ifcopenshell.open(r"data/IFC_test.ifc")
trans1 = Transformer(ifc1)
ifcBldg1 = ifc1.by_type("IfcBuilding")[0]

ifc2 = ifcopenshell.open(r"data/IFC_test3.ifc")
trans2 = Transformer(ifc2)
ifcBldg2 = ifc2.by_type("IfcBuilding")[0]

ifc3 = ifcopenshell.open(r"data/IFC_test4.ifc")
trans3 = Transformer(ifc3)
ifcBldg3 = ifc3.by_type("IfcBuilding")[0]

#####


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
        root = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc1, "Test123", trans1, True)
        result = lod0Conv.convert(root)
        corr = 5028
        self.assertEqual(corr, len(etree.tostring(result)))

    def test_2(self):
        root = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc2, "TestABC", trans2, False)
        result = lod0Conv.convert(root)
        corr = 2882
        self.assertEqual(corr, len(etree.tostring(result)))

    def test_3(self):
        root = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc3, "ÄÖÜß", trans3, False)
        result = lod0Conv.convert(root)
        corr = 6587
        self.assertEqual(corr, len(etree.tostring(result)))


class TestConvertFootPrint(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc1, "Test123", trans1, True)
        result = lod0Conv.convertFootPrint(ifcBldg1, root)
        corr = b'<root><ns0:lod0FootPrint xmlns:ns0="http://www.opengis.net/citygml/building/2.0"><ns1:MultiSurface' + \
               b' xmlns:ns1="http://www.opengis.net/gml"><ns1:surfaceMember><ns1:Polygon><ns1:outerBoundaryIs>' + \
               b'<ns1:LinearRing><ns1:coordinates>458870.063285681,5438773.62904949,110 ' + \
               b'458862.40284125,5438780.05692559,110 458870.116292566,5438789.24945891,110 ' + \
               b'458877.776736998,5438782.82158281,110 458870.063285681,5438773.62904949,110</ns1:coordinates>' + \
               b'</ns1:LinearRing></ns1:outerBoundaryIs></ns1:Polygon></ns1:surfaceMember></ns1:MultiSurface>' + \
               b'</ns0:lod0FootPrint></root>'
        self.assertEqual(corr, etree.tostring(root))
        corr = "POLYGON ((458870.063285681 5438773.62904949 110,458862.40284125 5438780.05692559 110," + \
               "458870.116292566 5438789.24945891 110,458877.776736998 5438782.82158281 110," + \
               "458870.063285681 5438773.62904949 110))"
        self.assertEqual(corr, result.ExportToWkt())

    def test_2(self):
        root = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc2, "TestABC", trans2, False)
        result = lod0Conv.convertFootPrint(ifcBldg2, root)
        corr = b'<root><ns0:lod0FootPrint xmlns:ns0="http://www.opengis.net/citygml/building/2.0"><ns1:MultiSurface' + \
               b' xmlns:ns1="http://www.opengis.net/gml"><ns1:surfaceMember><ns1:Polygon><ns1:outerBoundaryIs>' + \
               b'<ns1:LinearRing><ns1:coordinates>479356.600506348,5444183.43024925,-3 479356.600506348,' + \
               b'5444185.43024925,-3 479362.600506348,5444185.43024925,-3 479362.600506348,5444183.43024925,-3 ' + \
               b'479380.600506348,5444183.43024925,-3 479380.600506348,5444171.43024925,-3 479363.100506348,' + \
               b'5444171.43024925,-3 479363.100506348,5444167.43024925,-3 479356.100506348,5444167.43024925,-3 ' + \
               b'479356.100506348,5444171.43024925,-3 479338.600506348,5444171.43024925,-3 479338.600506348,' + \
               b'5444183.43024925,-3 479356.600506348,5444183.43024925,-3</ns1:coordinates></ns1:LinearRing>' + \
               b'</ns1:outerBoundaryIs></ns1:Polygon></ns1:surfaceMember></ns1:MultiSurface></ns0:lod0FootPrint></root>'
        self.assertEqual(corr, etree.tostring(root))
        corr = "POLYGON ((479356.600506348 5444183.43024925 -3,479356.600506348 5444185.43024925 -3," + \
               "479362.600506348 5444185.43024925 -3,479362.600506348 5444183.43024925 -3,479380.600506348 " + \
               "5444183.43024925 -3,479380.600506348 5444171.43024925 -3,479363.100506348 5444171.43024925 -3," + \
               "479363.100506348 5444167.43024925 -3,479356.100506348 5444167.43024925 -3,479356.100506348 " + \
               "5444171.43024925 -3,479338.600506348 5444171.43024925 -3,479338.600506348 5444183.43024925 -3," + \
               "479356.600506348 5444183.43024925 -3))"
        self.assertEqual(corr, result.ExportToWkt())

    def test_3(self):
        root = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc3, "Test123", trans3, False)
        result = lod0Conv.convertFootPrint(ifcBldg3, root)
        corr = 3584
        self.assertEqual(corr, len(etree.tostring(root)))
        corr = 85
        self.assertEqual(corr, result.GetGeometryRef(0).GetPointCount())


class TestConvertRoofEdge(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc1, "Test123", trans1, True)
        lod0Conv.convertRoofEdge(ifcBldg1, root)
        corr = b'<root><ns0:lod0RoofEdge xmlns:ns0="http://www.opengis.net/citygml/building/2.0"><ns1:MultiSurface ' + \
               b'xmlns:ns1="http://www.opengis.net/gml"><ns1:surfaceMember><ns1:Polygon><ns1:outerBoundaryIs>' + \
               b'<ns1:LinearRing><ns1:coordinates>458878.864175246,5438782.56181742,113 458870.50793632,' + \
               b'5438772.60323966,113 458861.315403002,5438780.31669098,113 458869.671641928,5438790.27526874,113 ' + \
               b'458878.864175246,5438782.56181742,113</ns1:coordinates></ns1:LinearRing></ns1:outerBoundaryIs>' + \
               b'</ns1:Polygon></ns1:surfaceMember></ns1:MultiSurface></ns0:lod0RoofEdge></root>'
        self.assertEqual(corr, etree.tostring(root))

    def test_2(self):
        root = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc2, "Test123", trans2, True)
        lod0Conv.convertRoofEdge(ifcBldg2, root)
        corr = b'<root><ns0:lod0RoofEdge xmlns:ns0="http://www.opengis.net/citygml/building/2.0"><ns1:MultiSurface ' + \
               b'xmlns:ns1="http://www.opengis.net/gml"><ns1:surfaceMember><ns1:Polygon><ns1:outerBoundaryIs>' + \
               b'<ns1:LinearRing><ns1:coordinates>479337.600506348,5444176.43024925,9 479337.600506348,' + \
               b'5444184.43024925,9 479355.600506348,5444184.43024925,9 479355.600506348,5444186.43024925,9 ' + \
               b'479363.600506348,5444186.43024925,9 479363.600506348,5444184.43024925,9 479381.600506348,' + \
               b'5444184.43024925,9 479381.600506348,5444170.43024925,9 479337.600506348,5444170.43024925,9 ' + \
               b'479337.600506348,5444176.43024925,9</ns1:coordinates></ns1:LinearRing></ns1:outerBoundaryIs>' + \
               b'</ns1:Polygon></ns1:surfaceMember></ns1:MultiSurface></ns0:lod0RoofEdge></root>'
        self.assertEqual(corr, etree.tostring(root))

    def test_3(self):
        root = etree.Element("root")
        lod0Conv = LoD0Converter(Model(), Converter(), ifc3, "Test123", trans3, True)
        lod0Conv.convertRoofEdge(ifcBldg3, root)
        corr = 2091
        self.assertEqual(corr, len(etree.tostring(root)))


if __name__ == '__main__':
    unittest.main()
