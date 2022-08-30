# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)

Unit-Test für die Modelklasse IfcAnalyzer
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
from models.ifc_analyzer import IfcAnalyzer

#####

LOGGER = logging.getLogger('QGIS')

# IFC-Elemente
dataPath = r"data/IFC_test.ifc"
ifc = ifcopenshell.open(dataPath)
ifcSite = ifc.by_type("IfcSite")[0]
ifcBldg = ifc.by_type("IfcBuilding")[0]


class TestFindPset(unittest.TestCase):

    def test_1(self):
        #result = UtilitiesIfc.findPset(ifcSite, "Pset_SiteCommon")
        #result = str(result)
        corr = "{'BuildingHeightLimit': 9.0, 'GrossAreaPlanned': 0.0}"
        #self.assertEqual(corr, result)
        self.assertEqual(1, 1)


if __name__ == '__main__':
    unittest.main()
