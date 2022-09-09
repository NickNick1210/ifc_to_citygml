# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (09.09.2022)

Unit-Tests für die Modelklasse Construction
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
from models.utilitiesIfc import UtilitiesIfc
from models.objects.construction import Construction

#####

LOGGER = logging.getLogger('QGIS')

# IFC-Elemente
ifc1 = ifcopenshell.open(r"data/IFC_test.ifc")
ifc2 = ifcopenshell.open(r"data/IFC_test3.ifc")
ifcBldg1 = ifc1.by_type("IfcBuilding")[0]
ifcBldg2 = ifc2.by_type("IfcBuilding")[0]
ifcRoofs = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[])
ifcWalls = UtilitiesIfc.findElement(ifc2, ifcBldg2, "IfcWall", result=[])
ifcWindows = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcWindow", result=[])
ifcMLS1 = ifc1.by_type("IfcMaterialLayerSet")[0]
ifcMLS2 = ifc2.by_type("IfcMaterialLayerSet")[0]

# Geometrien
geom1 = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 20 10, 20 20 10, 20 15 10, 10 10 10))")
geom2 = ogr.CreateGeometryFromWkt("Polygon((0 0, 0 20, 20 20, 20 0, 0 0),(5 5, 5 15, 15 15, 15 5, 5 5))")
geom3 = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 10 20, 20 10 20, 20 10 10, 10 10 10))")

#####


class TestConstructor(unittest.TestCase):

    def test_1(self):
        result = Construction("GML_ABC123", ifcMLS1, None, ifcRoofs, "layer")
        self.assertEqual("GML_ABC123", result.gmlId)
        self.assertEqual(ifcMLS1, result.ifcMLS)
        self.assertIsNone(result.optProp)
        self.assertEqual(ifcRoofs, result.ifcElems)
        self.assertEqual("layer", result.type)

    def test_2(self):
        result = Construction("GML_XYZ_äöüß", ifcMLS2, None, ifcWalls, "layer")
        self.assertEqual("GML_XYZ_äöüß", result.gmlId)
        self.assertEqual(ifcMLS2, result.ifcMLS)
        self.assertIsNone(result.optProp)
        self.assertEqual(ifcWalls, result.ifcElems)
        self.assertEqual("layer", result.type)

    def test_3(self):
        result = Construction("GML_987_XYZ", None, [3.0, 0.2, 0.15, 0.8, 0.85, 0.7], ifcWindows, "optical")
        self.assertEqual("GML_987_XYZ", result.gmlId)
        self.assertIsNone(result.ifcMLS)
        self.assertEqual([3.0, 0.2, 0.15, 0.8, 0.85, 0.7], result.optProp)
        self.assertEqual(ifcWindows, result.ifcElems)
        self.assertEqual("optical", result.type)


if __name__ == '__main__':
    unittest.main()
