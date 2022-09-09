# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (09.09.2022)

Unit-Tests für die Modelklasse Surface
 ***************************************************************************/
"""

# Standard-Bibliotheken
import unittest
import logging
import sys

# IFC-Bibliotheken
import ifcopenshell

# Geo-Bibliotheken
from osgeo import ogr

# Plugin
sys.path.insert(0, '..')
from algorithm.utilitiesIfc import UtilitiesIfc
from viewmodel.model import Surface

#####

LOGGER = logging.getLogger('QGIS')

# IFC-Elemente
ifc1 = ifcopenshell.open(r"data/IFC_test.ifc")
ifc2 = ifcopenshell.open(r"data/IFC_test3.ifc")
ifcBldg1 = ifc1.by_type("IfcBuilding")[0]
ifcBldg2 = ifc2.by_type("IfcBuilding")[0]
ifcRoof = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[])[1]
ifcWall = UtilitiesIfc.findElement(ifc2, ifcBldg2, "IfcWall", result=[])[0]

# Geometrien
geom1 = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 20 10, 20 20 10, 20 15 10, 10 10 10))")
geom2 = ogr.CreateGeometryFromWkt("Polygon((0 0, 0 20, 20 20, 20 0, 0 0),(5 5, 5 15, 15 15, 15 5, 5 5))")
geom3 = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 10 20, 20 10 20, 20 10 10, 10 10 10))")

#####


class TestConstructor(unittest.TestCase):

    def test_1(self):
        result = Surface([geom1], "Dach-01", ifcRoof, "Roof")
        self.assertEqual([geom1], result.geom)
        self.assertEqual("Dach-01", result.name)
        self.assertEqual(ifcRoof, result.ifcElem)
        self.assertEqual("Roof", result.type)
        self.assertIsNone(result.gmlId)
        self.assertEqual([], result.openings)

    def test_2(self):
        result = Surface([geom2, geom3], "Wand-ABC123", ifcWall, "Wall")
        self.assertEqual([geom2, geom3], result.geom)
        self.assertEqual("Wand-ABC123", result.name)
        self.assertEqual(ifcWall, result.ifcElem)
        self.assertEqual("Wall", result.type)
        self.assertIsNone(result.gmlId)
        self.assertEqual([], result.openings)


if __name__ == '__main__':
    unittest.main()
