# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)

Unit-Test für die Modelklasse Converter
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
from models.converter import Converter

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
ifcBldg1 = ifc1.by_type("IfcBuilding")[0]
ifcSite1 = ifc1.by_type("IfcSite")[0]
ifcProj1 = ifc1.by_type("IfcProject")[0]

dataPath2 = r"data/IFC_test3.ifc"
ifc2 = ifcopenshell.open(dataPath2)
ifcBldg2 = ifc2.by_type("IfcBuilding")[0]
ifcSite2 = ifc2.by_type("IfcSite")[0]
ifcProj2 = ifc2.by_type("IfcProject")[0]

dataPath3 = r"data/IFC_test4.ifc"
ifc3 = ifcopenshell.open(dataPath3)
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
        result = Converter("IFC-to-CityGML Conversion", None, inPath1, outPath1, 0, False, False)
        self.assertIsNone(result.exception)
        self.assertIsNone(result.parent)
        self.assertEqual(inPath1, result.inPath)
        self.assertEqual(outPath1, result.outPath)
        self.assertEqual(0, result.lod)
        self.assertFalse(result.eade)
        self.assertFalse(result.integr)
        self.assertIsNone(result.dedConv)

    def test_2(self):
        result = Converter("IFC-to-CityGML Conversion", None, inPath2, outPath2, 3, True, True)
        self.assertIsNone(result.exception)
        self.assertIsNone(result.parent)
        self.assertEqual(inPath2, result.inPath)
        self.assertEqual(outPath2, result.outPath)
        self.assertEqual(3, result.lod)
        self.assertTrue(result.eade)
        self.assertTrue(result.integr)
        self.assertIsNone(result.dedConv)


class TestReadIfc(unittest.TestCase):

    def test_1(self):
        result = Converter.readIfc(inPath1)
        corr = str(ifc1.by_type('IfcProject')[0])
        self.assertEqual(corr, str(result.by_type('IfcProject')[0]))

    def test_2(self):
        result = Converter.readIfc(inPath2)
        corr = str(ifc2.by_type('IfcProject')[0])
        self.assertEqual(corr, str(result.by_type('IfcProject')[0]))


class TestCreateSchema(unittest.TestCase):

    def test_1(self):
        result = Converter.createSchema()
        corr = b'<core:CityModel xmlns:core="http://www.opengis.net/citygml/2.0" xmlns=' + \
               b'"http://www.opengis.net/citygml/profiles/base/2.0" xmlns:bldg=' + \
               b'"http://www.opengis.net/citygml/building/2.0" xmlns:gen=' + \
               b'"http://www.opengis.net/citygml/generics/2.0" xmlns:grp=' + \
               b'"http://www.opengis.net/citygml/cityobjectgroup/2.0" xmlns:app=' + \
               b'"http://www.opengis.net/citygml/appearance/2.0" xmlns:gml="http://www.opengis.net/gml" ' + \
               b'xmlns:xAL="urn:oasis:names:tc:ciq:xsdschema:xAL:2.0" xmlns:xlink="http://www.w3.org/1999/xlink" ' + \
               b'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:energy=' + \
               b'"http://www.sig3d.org/citygml/2.0/energy/1.0"/>'
        self.assertEqual(corr, etree.tostring(result))


class TestWriteCGML(unittest.TestCase):

    def test_1(self):
        conv = Converter("IFC-to-CityGML Conversion", None, inPath1, outPath1, 0, False, False)
        conv.writeCGML(Converter.createSchema())
        f = open(outPath1, "r")
        result = ""
        for x in f:
            result += str(x)
        f.close()
        corr = '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<core:CityModel xmlns:core=' + \
               '"http://www.opengis.net/citygml/2.0" xmlns="http://www.opengis.net/citygml/profiles/base/2.0" ' + \
               'xmlns:bldg="http://www.opengis.net/citygml/building/2.0" xmlns:gen=' + \
               '"http://www.opengis.net/citygml/generics/2.0" xmlns:grp=' + \
               '"http://www.opengis.net/citygml/cityobjectgroup/2.0" xmlns:app=' + \
               '"http://www.opengis.net/citygml/appearance/2.0" xmlns:gml="http://www.opengis.net/gml" ' + \
               'xmlns:xAL="urn:oasis:names:tc:ciq:xsdschema:xAL:2.0" xmlns:xlink="http://www.w3.org/1999/xlink" ' + \
               'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:energy=' + \
               '"http://www.sig3d.org/citygml/2.0/energy/1.0"/>\n'
        self.assertEqual(corr, result)

    def test_2(self):
        rootNew = etree.Element("root")
        conv = Converter("IFC-to-CityGML Conversion", None, inPath1, outPath1, 0, False, False)
        conv.writeCGML(rootNew)
        f = open(outPath1, "r")
        result = ""
        for x in f:
            result += str(x)
        f.close()
        corr = "<?xml version='1.0' encoding='UTF-8'?>\n<root/>\n"
        self.assertEqual(corr, result)


# run und finished können nicht getestet werden, da es sie im Endeffekt eine QGIS-Instanz bzw. die GUI benötigen


if __name__ == '__main__':
    unittest.main()
