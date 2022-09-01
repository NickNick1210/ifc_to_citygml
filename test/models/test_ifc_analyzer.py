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
from dep_model import Model
sys.path.insert(0, '..')
from models.ifc_analyzer import IfcAnalyzer

#####

LOGGER = logging.getLogger('QGIS')

# IFC-Elemente
dirPath = os.path.dirname(os.path.abspath(__file__))
inPath1 = dirPath[0:dirPath.rindex("\\")+1] + "data\\IFC_test.ifc"
inPath2 = dirPath[0:dirPath.rindex("\\")+1] + "data\\IFC_test3.ifc"
inPath3 = dirPath[0:dirPath.rindex("\\")+1] + "data\\IFC_test4.ifc"
ifc1 = ifcopenshell.open(inPath1)
ifc2 = ifcopenshell.open(inPath2)
ifc3 = ifcopenshell.open(inPath3)


class TestConstructor(unittest.TestCase):

    def test_1(self):
        model = Model()
        result = IfcAnalyzer(model, inPath1)
        self.assertEqual(model, result.parent)
        self.assertIsNone(result.valTask)
        corr = str(ifc1.by_type('IfcProject')[0])
        self.assertEqual(corr, str(result.ifc.by_type('IfcProject')[0]))

    def test_2(self):
        model = Model()
        result = IfcAnalyzer(model, inPath2)
        self.assertEqual(model, result.parent)
        self.assertIsNone(result.valTask)
        corr = str(ifc2.by_type('IfcProject')[0])
        self.assertEqual(corr, str(result.ifc.by_type('IfcProject')[0]))


class TestRead(unittest.TestCase):

    def test_1(self):
        result = IfcAnalyzer.read(inPath1)
        corr = str(ifc1.by_type('IfcProject')[0])
        self.assertEqual(corr, str(result.by_type('IfcProject')[0]))

    def test_2(self):
        result = IfcAnalyzer.read(inPath2)
        corr = str(ifc2.by_type('IfcProject')[0])
        self.assertEqual(corr, str(result.by_type('IfcProject')[0]))

    def test_3(self):
        result = IfcAnalyzer.read(inPath3)
        corr = str(ifc3.by_type('IfcProject')[0])
        self.assertEqual(corr, str(result.by_type('IfcProject')[0]))


class TestPrintInfo(unittest.TestCase):

    def test_1(self):
        ifcAnalyzer = IfcAnalyzer(Model(), inPath1)
        ifcAnalyzer.printInfo(ifc1)
        corr = "IFC file 'IFC_test' is analyzed"
        self.assertEqual(corr, ifcAnalyzer.parent.dlg.logText)
        corr = "Schema: IFC4<br>Name: Projekt-FZK-Haus<br>" + \
               "Description: Projekt FZK-House create by KHH Forschuungszentrum Karlsruhe<br>No. of Buildings: 1"
        self.assertEqual(corr, ifcAnalyzer.parent.dlg.ifcInfo)

    def test_2(self):
        ifcAnalyzer = IfcAnalyzer(Model(), inPath2)
        ifcAnalyzer.printInfo(ifc2)
        corr = "IFC file 'IFC_test3' is analyzed"
        self.assertEqual(corr, ifcAnalyzer.parent.dlg.logText)
        corr = "Schema: IFC4<br>Name: Projekt Buerogebaeude<br>Description: No real Project<br>No. of Buildings: 1"
        self.assertEqual(corr, ifcAnalyzer.parent.dlg.ifcInfo)

    def test_3(self):
        ifcAnalyzer = IfcAnalyzer(Model(), inPath3)
        ifcAnalyzer.printInfo(ifc3)
        corr = "IFC file 'IFC_test4' is analyzed"
        self.assertEqual(corr, ifcAnalyzer.parent.dlg.logText)
        corr = "Schema: IFC4<br>Name: Smiley West<br>Description: -<br>No. of Buildings: 1"
        self.assertEqual(corr, ifcAnalyzer.parent.dlg.ifcInfo)


class TestCheck(unittest.TestCase):

    def test_1(self):
        ifcAnalyzer = IfcAnalyzer(Model(), inPath1)
        ifcAnalyzer.check(ifc1, True)
        self.assertEqual(1, 1)

    def test_2(self):
        ifcAnalyzer = IfcAnalyzer(Model(), inPath2)
        ifcAnalyzer.check(ifc2, False)
        self.assertEqual(1, 1)

    def test_3(self):
        ifcAnalyzer = IfcAnalyzer(Model(), inPath3)
        ifcAnalyzer.check(ifc3, False)
        self.assertEqual(1, 1)


class TestValCompleted(unittest.TestCase):

    def test_1(self):
        model = Model()
        ifcAnalyzer = IfcAnalyzer(model, inPath1)
        ifcAnalyzer.valCompleted()
        self.assertTrue(model.valid)

    def test_2(self):
        model = Model()
        ifcAnalyzer = IfcAnalyzer(model, inPath2)
        ifcAnalyzer.valCompleted()
        self.assertTrue(model.valid)

    def test_3(self):
        model = Model()
        ifcAnalyzer = IfcAnalyzer(model, inPath3)
        ifcAnalyzer.valCompleted()
        self.assertTrue(model.valid)


# Validate kann nicht eigenständig angesprochen werden, da er als Task die Eigenschaften der IfcAnalyzer-Klasse braucht


if __name__ == '__main__':
    unittest.main()
