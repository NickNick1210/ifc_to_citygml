# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (09.09.2022)

Unit-Tests für die Modelklasse Material
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
from viewmodel.model import Material

#####

LOGGER = logging.getLogger('QGIS')

# IFC-Elemente
ifc1 = ifcopenshell.open(r"data/IFC_test.ifc")
ifc2 = ifcopenshell.open(r"data/IFC_test3.ifc")
ifcMat1 = ifc1.by_type("IfcMaterial")[0]
ifcMat2 = ifc2.by_type("IfcMaterial")[0]


#####


class TestConstructor(unittest.TestCase):

    def test_1(self):
        result = Material("GML_ABC123", ifcMat1)
        self.assertEqual("GML_ABC123", result.gmlId)
        self.assertEqual(ifcMat1, result.ifcMat)

    def test_2(self):
        result = Material("GML_XYZ_äöüß", ifcMat2)
        self.assertEqual("GML_XYZ_äöüß", result.gmlId)
        self.assertEqual(ifcMat2, result.ifcMat)


if __name__ == '__main__':
    unittest.main()
