# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)

Unit-Test für die Modelklasse LoD0Converter
 ***************************************************************************/
"""

# Standard-Bibliotheken
import unittest
import logging
import sys
import os

# IFC-Bibliotheken
import ifcopenshell

# XML-Bibliotheken
from lxml import etree

# Geo-Bibliotheken
from osgeo import ogr

# Plugin
sys.path.insert(0, '..')
from models.converter_lod0 import LoD0Converter
from models.transformer import Transformer

#####

LOGGER = logging.getLogger('QGIS')

# IFC-Elemente
dirPath = os.path.dirname(os.path.abspath(__file__))
inPath1 = dirPath[0:dirPath.rindex("\\")+1] + "data\\IFC_test.ifc"
outPath1 = dirPath[0:dirPath.rindex("\\")+1] + "data\\CityGML_test.gml"
inPath2 = dirPath[0:dirPath.rindex("\\")+1] + "data\\IFC_test3.ifc"
outPath2 = dirPath[0:dirPath.rindex("\\")+1] + "data\\CityGML_test3.gml"

dataPath1 = r"data/IFC_test.ifc"
ifc1 = ifcopenshell.open(dataPath1)
trans1 = Transformer(ifc1)
ifcBldg1 = ifc1.by_type("IfcBuilding")[0]
ifcSite1 = ifc1.by_type("IfcSite")[0]
ifcProj1 = ifc1.by_type("IfcProject")[0]

dataPath2 = r"data/IFC_test3.ifc"
ifc2 = ifcopenshell.open(dataPath2)
trans2 = Transformer(ifc2)
ifcBldg2 = ifc2.by_type("IfcBuilding")[0]
ifcSite2 = ifc2.by_type("IfcSite")[0]
ifcProj2 = ifc2.by_type("IfcProject")[0]

dataPath3 = r"data/IFC_test4.ifc"
ifc3 = ifcopenshell.open(dataPath3)
trans3 = Transformer(ifc3)
ifcBldg3 = ifc3.by_type("IfcBuilding")[0]
ifcSite3 = ifc3.by_type("IfcSite")[0]
ifcProj3 = ifc3.by_type("IfcProject")[0]

# XML-Elemente
root = etree.Element("root")

# Geometrien
bbox = (10, 10, 10, 20, 20, 20)
geom1 = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 20 10, 20 20 10, 20 10 10, 10 10 10))")
geom2 = ogr.CreateGeometryFromWkt("Polygon((10 10 3.1415, 10 20 3.1415, 20 20 3.1415, 20 10 10, 10 10 3.1415))")


class TestConstructor(unittest.TestCase):

    def test_1(self):
        result = LoD0Converter(None, None, ifc1, "Test123", trans1, False)
        self.assertEqual(inPath1, result.inPath)


# convert

# convertFootPrint

# convertRoofEdge



# XXX können nicht getestet werden, da es sie im Endeffekt eine QGIS-Instanz bzw. die GUI benötigen


if __name__ == '__main__':
    unittest.main()
