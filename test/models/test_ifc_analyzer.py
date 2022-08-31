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
import os

# IFC-Bibliotheken
import ifcopenshell

# Plugin
sys.path.insert(0, '..')
from models.ifc_analyzer import IfcAnalyzer

#####

LOGGER = logging.getLogger('QGIS')

# IFC-Elemente
dirPath = os.path.dirname(os.path.abspath(__file__))
dataPath = dirPath[0:dirPath.rindex("\\")+1] + "data\\IFC_test.ifc"
ifc = ifcopenshell.open(dataPath)


class TestConstructor(unittest.TestCase):

    def test_1(self):
        result = IfcAnalyzer(None, dataPath)
        self.assertIsNone(result.parent)
        self.assertIsNone(result.valTask)
        corr = str(ifc.by_type('IfcProject')[0])
        self.assertEqual(corr, str(result.ifc.by_type('IfcProject')[0]))
        self.assertEqual("IFC_test", result.fileName)


class TestRead(unittest.TestCase):

    def test_1(self):
        result = IfcAnalyzer.read(dataPath)
        corr = str(ifc.by_type('IfcProject')[0])
        self.assertEqual(corr, str(result.by_type('IfcProject')[0]))


# Weitere Methoden können nicht getestet werden, da sie Verbindungen zu weiteren Klassen bzw. der QGIS-Instanz haben
#   oder als eigenständige Tasks ausgeführt werden.



if __name__ == '__main__':
    unittest.main()
