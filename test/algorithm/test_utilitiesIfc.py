# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (09.09.2022)

Unit-Tests für die Modelklasse UtilitiesIfc
 ***************************************************************************/
"""

# Standard-Bibliotheken
import unittest
import logging
import sys

# IFC-Bibliotheken
import ifcopenshell

# Plugin
sys.path.insert(0, '..')
from algorithm.utilitiesIfc import UtilitiesIfc

#####

LOGGER = logging.getLogger('QGIS')

# IFC-Elemente
ifc = ifcopenshell.open(r"data/IFC_test.ifc")
ifcSite = ifc.by_type("IfcSite")[0]
ifcBldg = ifc.by_type("IfcBuilding")[0]

#####


class TestFindPset(unittest.TestCase):

    def test_1(self):
        result = UtilitiesIfc.findPset(ifcSite, "Pset_SiteCommon")
        self.assertEqual("{'BuildingHeightLimit': 9.0, 'GrossAreaPlanned': 0.0}", str(result))

    def test_2(self):
        result = UtilitiesIfc.findPset(ifcSite, "Pset_ABC123")
        self.assertIsNone(result)

    def test_3(self):
        result = UtilitiesIfc.findPset(ifcSite, "Pset_SiteCommon", "BuildingHeightLimit")
        self.assertEqual(9, result)

    def test_4(self):
        result = UtilitiesIfc.findPset(ifcSite, "Pset_SiteCommon", "AttrABC123")
        self.assertIsNone(result)

    def test_5(self):
        result = UtilitiesIfc.findPset(ifcBldg, "Pset_SpaceHVACDesign", "TemperatureMax")
        self.assertEqual(23, result)


class TestFindElement(unittest.TestCase):

    def test_1(self):
        result = UtilitiesIfc.findElement(ifc, ifcBldg, "IfcSpace", result=[])
        self.assertEqual(7, len(result))

    def test_2(self):
        result = UtilitiesIfc.findElement(ifc, ifcBldg, "IfcSlab", result=[])
        self.assertEqual(4, len(result))

    def test_3(self):
        result = UtilitiesIfc.findElement(ifc, ifcBldg, "IfcSlab", result=[], type="ROOF")
        self.assertEqual(2, len(result))

    def test_4(self):
        result = UtilitiesIfc.findElement(ifc, ifcBldg, "IfcABC123", result=[])
        self.assertEqual(0, len(result))

    def test_5(self):
        result = UtilitiesIfc.findElement(ifc, ifcBldg, "IfcSlab", result=[], type="ABC123")
        self.assertEqual(0, len(result))

    def test_6(self):
        result = UtilitiesIfc.findElement(ifc, ifcSite, "IfcBuilding", result=[])
        self.assertEqual(1, len(result))

    def test_7(self):
        result = UtilitiesIfc.findElement(ifc, ifcSite, "IfcWall", result=[])
        self.assertEqual(13, len(result))


if __name__ == '__main__':
    unittest.main()
