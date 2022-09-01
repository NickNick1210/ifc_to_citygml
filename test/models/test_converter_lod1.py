# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)

Unit-Tests für die Modelklasse LoD1Converter
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
from mock_model import Model
from mock_converter import Converter
sys.path.insert(0, '..')
from models.converter_lod1 import LoD1Converter
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

# Geometrien
geom1 = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 20 10, 20 20 10, 20 10 10, 10 10 10))")
geom2 = ogr.CreateGeometryFromWkt("Polygon((10 10 3.1415, 10 20 3.1415, 20 20 3.1415, 20 10 3.1415, 10 10 3.1415))")

#####


class TestConstructor(unittest.TestCase):

    def test_1(self):
        model = Model()
        conv = Converter()
        result = LoD1Converter(model, conv, ifc1, "Test123", trans1, False)
        self.assertEqual(model, result.parent)
        self.assertEqual(conv, result.task)
        self.assertEqual(ifc1, result.ifc)
        self.assertEqual("Test123", result.name)
        self.assertEqual(trans1, result.trans)
        self.assertFalse(result.eade)
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.geom)))
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.bldgGeom)))
        self.assertEqual(10, result.progress)
        self.assertEqual(1, result.bldgCount)

    def test_2(self):
        model = Model()
        conv = Converter()
        result = LoD1Converter(model, conv, ifc2, "TestABC", trans2, True)
        self.assertEqual(model, result.parent)
        self.assertEqual(conv, result.task)
        self.assertEqual(ifc2, result.ifc)
        self.assertEqual("TestABC", result.name)
        self.assertEqual(trans2, result.trans)
        self.assertTrue(result.eade)
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.geom)))
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.bldgGeom)))
        self.assertEqual(10, result.progress)
        self.assertEqual(1, result.bldgCount)


class TestConvert(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        lod1Conv = LoD1Converter(Model(), Converter(), ifc1, "Test123", trans1, True)
        result = lod1Conv.convert(root)
        corr = 11410
        self.assertEqual(corr, len(etree.tostring(result)))

    def test_2(self):
        root = etree.Element("root")
        lod1Conv = LoD1Converter(Model(), Converter(), ifc2, "TestABC", trans2, False)
        result = lod1Conv.convert(root)
        corr = 7806
        self.assertEqual(corr, len(etree.tostring(result)))

    def test_3(self):
        root = etree.Element("root")
        lod1Conv = LoD1Converter(Model(), Converter(), ifc3, "ÄÖÜß", trans3, False)
        result = lod1Conv.convert(root)
        corr = 39529
        self.assertEqual(corr, len(etree.tostring(result)))


class TestConvertSolid(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        lod1Conv = LoD1Converter(Model(), Converter(), ifc1, "Test123", trans1, True)
        result = lod1Conv.convertSolid(ifcBldg1, root, 10)
        corr = 2425
        self.assertEqual(corr, len(etree.tostring(root)))
        corr = "POLYGON ((458870.063285681 5438773.62904949 110,458862.40284125 5438780.05692559 110," + \
               "458870.116292566 5438789.24945891 110,458877.776736998 5438782.82158281 110,458870.063285681 " + \
               "5438773.62904949 110))"
        self.assertEqual(corr, result.ExportToWkt())

    def test_2(self):
        root = etree.Element("root")
        lod1Conv = LoD1Converter(Model(), Converter(), ifc2, "Test123", trans2, True)
        result = lod1Conv.convertSolid(ifcBldg2, root, 10)
        corr = 5845
        self.assertEqual(corr, len(etree.tostring(root)))
        corr = "POLYGON ((479356.600506348 5444183.43024925 -3,479356.600506348 5444185.43024925 -3," + \
               "479362.600506348 5444185.43024925 -3,479362.600506348 5444183.43024925 -3,479380.600506348 " + \
               "5444183.43024925 -3,479380.600506348 5444171.43024925 -3,479363.100506348 5444171.43024925 -3," + \
               "479363.100506348 5444167.43024925 -3,479356.100506348 5444167.43024925 -3,479356.100506348 " + \
               "5444171.43024925 -3,479338.600506348 5444171.43024925 -3,479338.600506348 5444183.43024925 -3," + \
               "479356.600506348 5444183.43024925 -3))"
        self.assertEqual(corr, result.ExportToWkt())

    def test_3(self):
        root = etree.Element("root")
        lod1Conv = LoD1Converter(Model(), Converter(), ifc3, "Test123", trans3, True)
        result = lod1Conv.convertSolid(ifcBldg3, root, 10)
        corr = 37750
        self.assertEqual(corr, len(etree.tostring(root)))
        corr = 85
        self.assertEqual(corr, result.GetGeometryRef(0).GetPointCount())


class TestCalcRoof(unittest.TestCase):

    def test_1(self):
        result = LoD1Converter.calcRoof(geom1, 10)
        corr = "POLYGON ((10 10 20,20 10 20,20 20 20,10 20 20,10 10 20))"
        self.assertEqual(corr, result.ExportToWkt())

    def test_2(self):
        result = LoD1Converter.calcRoof(geom2, 3.1415)
        corr = "POLYGON ((10 10 6.283,20 10 6.283,20 20 6.283,10 20 6.283,10 10 6.283))"
        self.assertEqual(corr, result.ExportToWkt())


class TestCalcWalls(unittest.TestCase):

    def test_1(self):
        result = LoD1Converter.calcWalls(geom1, 10)
        corr = 4
        self.assertEqual(corr, len(result))
        corr = "POLYGON ((10 10 10,10 10 20,10 20 20,10 20 10,10 10 10))"
        self.assertEqual(corr, result[0].ExportToWkt())
        corr = "POLYGON ((10 20 10,10 20 20,20 20 20,20 20 10,10 20 10))"
        self.assertEqual(corr, result[1].ExportToWkt())
        corr = "POLYGON ((20 20 10,20 20 20,20 10 20,20 10 10,20 20 10))"
        self.assertEqual(corr, result[2].ExportToWkt())
        corr = "POLYGON ((20 10 10,20 10 20,10 10 20,10 10 10,20 10 10))"
        self.assertEqual(corr, result[3].ExportToWkt())

    def test_2(self):
        result = LoD1Converter.calcWalls(geom2, 3.1415)
        corr = 4
        self.assertEqual(corr, len(result))
        corr = "POLYGON ((10 10 3.1415,10 10 6.283,10 20 6.283,10 20 3.1415,10 10 3.1415))"
        self.assertEqual(corr, result[0].ExportToWkt())
        corr = "POLYGON ((10 20 3.1415,10 20 6.283,20 20 6.283,20 20 3.1415,10 20 3.1415))"
        self.assertEqual(corr, result[1].ExportToWkt())
        corr = "POLYGON ((20 20 3.1415,20 20 6.283,20 10 6.283,20 10 3.1415,20 20 3.1415))"
        self.assertEqual(corr, result[2].ExportToWkt())
        corr = "POLYGON ((20 10 3.1415,20 10 6.283,10 10 6.283,10 10 3.1415,20 10 3.1415))"
        self.assertEqual(corr, result[3].ExportToWkt())


if __name__ == '__main__':
    unittest.main()
