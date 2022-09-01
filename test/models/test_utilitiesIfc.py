# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)

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
from models.utilitiesIfc import UtilitiesIfc

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
        result = str(result)
        corr = "{'BuildingHeightLimit': 9.0, 'GrossAreaPlanned': 0.0}"
        self.assertEqual(corr, result)

    def test_2(self):
        result = UtilitiesIfc.findPset(ifcSite, "Pset_ABC123")
        corr = None
        self.assertEqual(corr, result)

    def test_3(self):
        result = UtilitiesIfc.findPset(ifcSite, "Pset_SiteCommon", "BuildingHeightLimit")
        corr = 9
        self.assertEqual(corr, result)

    def test_4(self):
        result = UtilitiesIfc.findPset(ifcSite, "Pset_SiteCommon", "AttrABC123")
        corr = None
        self.assertEqual(corr, result)

    def test_5(self):
        result = UtilitiesIfc.findPset(ifcBldg, "Pset_SpaceHVACDesign", "TemperatureMax")
        corr = 23
        self.assertEqual(corr, result)


class TestFindElement(unittest.TestCase):

    def test_1(self):
        result = UtilitiesIfc.findElement(ifc, ifcBldg, "IfcSpace", result=[])
        result = len(result)
        corr = 7
        self.assertEqual(corr, result)

    def test_2(self):
        result = UtilitiesIfc.findElement(ifc, ifcBldg, "IfcSlab", result=[])
        result = len(result)
        corr = 4
        self.assertEqual(corr, result)

    def test_3(self):
        result = UtilitiesIfc.findElement(ifc, ifcBldg, "IfcSlab", result=[], type="ROOF")
        result = len(result)
        corr = 2
        self.assertEqual(corr, result)

    def test_4(self):
        result = UtilitiesIfc.findElement(ifc, ifcBldg, "IfcABC123", result=[])
        result = len(result)
        corr = 0
        self.assertEqual(corr, result)

    def test_5(self):
        result = UtilitiesIfc.findElement(ifc, ifcBldg, "IfcSlab", result=[], type="ABC123")
        result = len(result)
        corr = 0
        self.assertEqual(corr, result)

    def test_6(self):
        result = UtilitiesIfc.findElement(ifc, ifcSite, "IfcBuilding", result=[])
        result = len(result)
        corr = 1
        self.assertEqual(corr, result)

    def test_7(self):
        result = UtilitiesIfc.findElement(ifc, ifcSite, "IfcWall", result=[])
        result = len(result)
        corr = 13
        self.assertEqual(corr, result)


if __name__ == '__main__':
    unittest.main()
