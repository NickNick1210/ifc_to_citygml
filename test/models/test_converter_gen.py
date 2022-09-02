# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (02.09.2022)

Unit-Tests für die Modelklasse GenConverter
 ***************************************************************************/
"""

# Standard-Bibliotheken
import unittest
import logging
import sys

# IFC-Bibliotheken
import ifcopenshell

# XML-Bibliotheken
from lxml import etree

# Geo-Bibliotheken
from osgeo import ogr

# Plugin
sys.path.insert(0, '..')
from models.converter_gen import GenConverter
from models.transformer import Transformer
from models.utilitiesIfc import UtilitiesIfc

#####

LOGGER = logging.getLogger('QGIS')

# IFC-Elemente
ifc1 = ifcopenshell.open(r"data/IFC_test.ifc")
ifcBldg1 = ifc1.by_type("IfcBuilding")[0]
ifcSite1 = ifc1.by_type("IfcSite")[0]
trans1 = Transformer(ifc1)

ifc2 = ifcopenshell.open(r"data/IFC_test3.ifc")
ifcBldg2 = ifc2.by_type("IfcBuilding")[0]
ifcSite2 = ifc2.by_type("IfcSite")[0]
trans2 = Transformer(ifc2)

ifc3 = ifcopenshell.open(r"data/IFC_test4.ifc")
ifcBldg3 = ifc3.by_type("IfcBuilding")[0]
ifcSite3 = ifc3.by_type("IfcSite")[0]
trans3 = Transformer(ifc3)

# Geometrien
geom1 = ogr.CreateGeometryFromWkt("GeometryCollection(Polygon((10 10 10, 10 20 10, 20 20 10, 20 15 10, 10 10 10)))")
geom2 = ogr.CreateGeometryFromWkt("GeometryCollection(Polygon((10 10 10, 10 20 10, 20 20 10, 20 15 10, 10 10 10)), " +
                                  "Polygon((50 50 10, 50 90 10, 90 90 10, 90 70 10, 50 50 10)))")
geom3 = ogr.CreateGeometryFromWkt("GeometryCollection(Polygon((10 10 10, 10 20 10, 20 20 20, 20 15 20, 10 10 10)))")
geom4 = ogr.CreateGeometryFromWkt("GeometryCollection(Polygon((10 10 10, 10 20 10, 20 20 10, 20 15 10, 10 10 10)), " +
                                  "Polygon((50 50 10, 50 90 10, 90 90 10, 90 70 10, 50 50 10)), " +
                                  "Polygon((10 10 10, 10 20 10, 20 20 20, 20 15 20, 10 10 10)))")

#####


class TestConvertBound(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        result = GenConverter.convertBound(geom1, root, trans1)
        corr = (10, 20, 10, 20, 10, 10)
        self.assertEqual(corr, result)

    def test_2(self):
        root = etree.Element("root")
        result = GenConverter.convertBound(geom2, root, trans1)
        corr = (10, 90, 10, 90, 10, 10)
        self.assertEqual(corr, result)

    def test_3(self):
        root = etree.Element("root")
        result = GenConverter.convertBound(geom3, root, trans1)
        corr = (10, 20, 10, 20, 10, 20)
        self.assertEqual(corr, result)

    def test_4(self):
        root = etree.Element("root")
        result = GenConverter.convertBound(geom4, root, trans1)
        corr = (10, 90, 10, 90, 10, 20)
        self.assertEqual(corr, result)


class TestConvertBldgAttr(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        result = GenConverter.convertBldgAttr(ifc1, ifcBldg1, root)
        self.assertAlmostEqual(6.51769, result, 3)
        self.assertEqual(1514, len(etree.tostring(root)))

    def test_2(self):
        root = etree.Element("root")
        result = GenConverter.convertBldgAttr(ifc2, ifcBldg2, root)
        self.assertAlmostEqual(15.34932, result, 3)
        self.assertEqual(1520, len(etree.tostring(root)))

    def test_3(self):
        root = etree.Element("root")
        result = GenConverter.convertBldgAttr(ifc3, ifcBldg3, root)
        self.assertAlmostEqual(11.01, result, 3)
        self.assertEqual(918, len(etree.tostring(root)))


class TestConvertFunctionUsage(unittest.TestCase):

    def test_1(self):
        result = GenConverter.convertFunctionUsage("1680")
        self.assertEqual(1680, result)

    def test_2(self):
        result = GenConverter.convertFunctionUsage("3210")
        self.assertIsNone(result)

    def test_3(self):
        result = GenConverter.convertFunctionUsage("hospital")
        self.assertEqual(2310, result)

    def test_4(self):
        result = GenConverter.convertFunctionUsage("Bibliothek")
        self.assertEqual(2190, result)

    def test_5(self):
        result = GenConverter.convertFunctionUsage("Betreutes Wohnen")
        self.assertEqual(1000, result)


class TestCalcHeight(unittest.TestCase):

    def test_1(self):
        result = GenConverter.calcHeight(ifc1, ifcBldg1)
        self.assertAlmostEqual(6.51769, result, 3)

    def test_2(self):
        result = GenConverter.calcHeight(ifc2, ifcBldg2)
        self.assertAlmostEqual(15.34932, result, 3)

    def test_3(self):
        result = GenConverter.calcHeight(ifc3, ifcBldg3)
        self.assertAlmostEqual(11.01, result, 3)


class TestConvertAddress(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        result = GenConverter.convertAddress(ifcBldg1, ifcSite1, root)
        self.assertTrue(result)
        self.assertEqual(655, len(etree.tostring(root)))

    def test_2(self):
        root = etree.Element("root")
        result = GenConverter.convertAddress(ifcBldg2, ifcSite2, root)
        self.assertFalse(result)
        self.assertEqual(7, len(etree.tostring(root)))

    def test_3(self):
        root = etree.Element("root")
        result = GenConverter.convertAddress(ifcBldg3, ifcSite3, root)
        self.assertFalse(result)
        self.assertEqual(7, len(etree.tostring(root)))


class TestCalcPlane(unittest.TestCase):

    def test_1(self):
        ifcSlabs = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[], type="BASESLAB")
        result = GenConverter.calcPlane(ifcSlabs, trans1)
        self.assertEqual(ifcSlabs[0], result[0])
        corr = "POLYGON ((458870.063285681 5438773.62904949 110,458862.40284125 5438780.05692559 110," + \
               "458870.116292566 5438789.24945891 110,458877.776736998 5438782.82158281 110," + \
               "458870.063285681 5438773.62904949 110))"
        self.assertEqual(corr, result[1].ExportToWkt())

    def test_2(self):
        ifcSlabs = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[], type="ROOF")
        result = GenConverter.calcPlane(ifcSlabs, trans1)
        self.assertEqual(ifcSlabs[0], result[0])
        corr = "POLYGON ((458878.864175246 5438782.56181742 113,458870.50793632 5438772.60323966 113," + \
               "458861.315403002 5438780.31669098 113,458869.671641928 5438790.27526874 113," + \
               "458878.864175246 5438782.56181742 113))"
        self.assertEqual(corr, result[1].ExportToWkt())

    def test_3(self):
        ifcSlabs = UtilitiesIfc.findElement(ifc2, ifcBldg2, "IfcSlab", result=[], type="FLOOR")
        result = GenConverter.calcPlane(ifcSlabs, trans2)
        self.assertEqual(ifcSlabs[0], result[0])
        corr = "POLYGON ((479356.600506348 5444183.43024925 -3,479356.600506348 5444185.43024925 -3," + \
               "479362.600506348 5444185.43024925 -3,479362.600506348 5444183.43024925 -3,479380.600506348 " + \
               "5444183.43024925 -3,479380.600506348 5444171.43024925 -3,479363.100506348 5444171.43024925 " + \
               "-3,479363.100506348 5444167.43024925 -3,479356.100506348 5444167.43024925 -3,479356.100506348 " + \
               "5444171.43024925 -3,479338.600506348 5444171.43024925 -3,479338.600506348 5444183.43024925 " + \
               "-3,479356.600506348 5444183.43024925 -3))"
        self.assertEqual(corr, result[1].ExportToWkt())

    def test_4(self):
        ifcSlabs = UtilitiesIfc.findElement(ifc3, ifcBldg3, "IfcSlab", result=[], type="FLOOR")
        result = GenConverter.calcPlane(ifcSlabs, trans3)
        self.assertEqual(ifcSlabs[0], result[0])
        self.assertEqual(3235, len(result[1].ExportToWkt()))


class TestConvertSolid(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        GenConverter.convertSolid(root, ["ABC123", "GML_ID1234567890", "987zyx"], 2)
        corr = b'<root><ns0:lod2Solid xmlns:ns0="http://www.opengis.net/citygml/building/2.0"><ns1:Solid xmlns:ns1=' + \
               b'"http://www.opengis.net/gml"><ns1:exterior><ns1:CompositeSurface><ns1:surfaceMember xmlns:ns2=' + \
               b'"http://www.w3.org/1999/xlink" ns2:href="#ABC123"/><ns1:surfaceMember xmlns:ns3=' + \
               b'"http://www.w3.org/1999/xlink" ns3:href="#GML_ID1234567890"/><ns1:surfaceMember xmlns:ns4=' + \
               b'"http://www.w3.org/1999/xlink" ns4:href="#987zyx"/></ns1:CompositeSurface></ns1:exterior>' + \
               b'</ns1:Solid></ns0:lod2Solid></root>'
        self.assertEqual(corr, etree.tostring(root))

    def test_2(self):
        root = etree.Element("root")
        GenConverter.convertSolid(root, [], 3)
        self.assertEqual(b'<root/>', etree.tostring(root))


if __name__ == '__main__':
    unittest.main()
