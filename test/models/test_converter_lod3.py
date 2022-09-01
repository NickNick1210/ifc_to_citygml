# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)

Unit-Tests für die Modelklasse LoD3Converter
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
from models.converter_lod3 import LoD3Converter
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
base = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 20 10, 20 20 10, 20 10 10, 10 10 10))")
roof1 = ogr.CreateGeometryFromWkt("Polygon((9 9 10, 9 15 15, 21 15 15, 21 9 10, 9 9 10))")
roof2 = ogr.CreateGeometryFromWkt("Polygon((9 15 15, 9 21 10, 21 21 10, 21 15 15, 9 15 15))")
wall1 = ogr.CreateGeometryFromWkt("Polygon((10 10 10,10 10 10.8333333333333,10 15 15,10 20 10.8333333333333," +
                                  "10 20 10,10 10 10))")
wall2 = ogr.CreateGeometryFromWkt("Polygon((10 20 10,10 20 10.8333333333333,20 20 10.8333333333333,20 20 10,10 20 10))")
wall3 = ogr.CreateGeometryFromWkt("Polygon((20 20 10,20 20 10.8333333333333,20 15 15,20 10 10.8333333333333," +
                                  "20 10 10,20 20 10))")
wall4 = ogr.CreateGeometryFromWkt("Polygon((20 10 10,20 10 10.8333333333333,10 10 10.8333333333333,10 10 10,20 10 10))")

#####


class TestConstructor(unittest.TestCase):

    def test_1(self):
        model = Model()
        conv = Converter()
        result = LoD3Converter(model, conv, ifc1, "Test123", trans1, False)
        self.assertEqual(model, result.parent)
        self.assertEqual(conv, result.task)
        self.assertEqual(ifc1, result.ifc)
        self.assertEqual("Test123", result.name)
        self.assertEqual(trans1, result.trans)
        self.assertFalse(result.eade)
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.geom)))
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.bldgGeom)))
        self.assertEqual(5, result.progress)
        self.assertEqual(1, result.bldgCount)

    def test_2(self):
        model = Model()
        conv = Converter()
        result = LoD3Converter(model, conv, ifc2, "TestABC", trans2, True)
        self.assertEqual(model, result.parent)
        self.assertEqual(conv, result.task)
        self.assertEqual(ifc2, result.ifc)
        self.assertEqual("TestABC", result.name)
        self.assertEqual(trans2, result.trans)
        self.assertTrue(result.eade)
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.geom)))
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.bldgGeom)))
        self.assertEqual(5, result.progress)
        self.assertEqual(1, result.bldgCount)


# Convert und ConvertBldgBound nicht testbar?

# calcBases(self, ifcBuilding)

# calcRoofs(self, ifcBuilding)

# calcWalls(self, ifcBuilding)

# calcOpenings(self, ifcBuilding, type)

# assignOpenings(self, openings, walls)

# adjustWallOpenings(self, walls)

# adjustWallSize(self, walls, bases, roofs, basesOrig, roofsOrig, wallMainCounts)

# setElementGroup(self, chBldg, geometries, type, lod, name, openings)



if __name__ == '__main__':
    unittest.main()
