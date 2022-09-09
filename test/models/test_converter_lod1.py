# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (09.09.2022)

Unit-Tests für die Modelklasse LoD1Converter
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
from mock_converter import Converter
sys.path.insert(0, '..')
from models.converter_lod1 import LoD1Converter
from models.transformer import Transformer
from models.utilitiesIfc import UtilitiesIfc

#####

LOGGER = logging.getLogger('QGIS')

# IFC-Elemente
ifc1 = ifcopenshell.open(r"data/IFC_test.ifc")
trans1 = Transformer(ifc1)
ifcSite1 = ifc1.by_type("IfcSite")[0]
ifcBldg1 = ifc1.by_type("IfcBuilding")[0]

ifc2 = ifcopenshell.open(r"data/IFC_test3.ifc")
trans2 = Transformer(ifc2)
ifcSite2 = ifc2.by_type("IfcSite")[0]
ifcBldg2 = ifc2.by_type("IfcBuilding")[0]

ifc3 = ifcopenshell.open(r"data/IFC_test4.ifc")
trans3 = Transformer(ifc3)
ifcSite3 = ifc3.by_type("IfcSite")[0]
ifcBldg3 = ifc3.by_type("IfcBuilding")[0]

# Geometrien
geom1 = ogr.CreateGeometryFromWkt("GeometryCollection(Polygon((10 10 10, 10 20 10, 20 20 10, 20 15 10, 10 10 10)))")
geom2 = ogr.CreateGeometryFromWkt("GeometryCollection(Polygon((10 10 10, 10 20 10, 20 20 10, 20 15 10, 10 10 10)), " +
                                  "Polygon((50 50 10, 50 90 10, 90 90 10, 90 70 10, 50 50 10)))")
geom3 = ogr.CreateGeometryFromWkt("GeometryCollection(Polygon((10 10 10, 10 20 10, 20 20 20, 20 15 20, 10 10 10)))")
geom4 = ogr.CreateGeometryFromWkt("GeometryCollection(Polygon((10 10 10, 10 20 10, 20 20 10, 20 15 10, 10 10 10)), " +
                                  "Polygon((50 50 10, 50 90 10, 90 90 10, 90 70 10, 50 50 10)), " +
                                  "Polygon((10 10 10, 10 20 10, 20 20 20, 20 15 20, 10 10 10)))")
geom5 = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 20 10, 20 20 10, 20 10 10, 10 10 10))")
geom6 = ogr.CreateGeometryFromWkt("Polygon((10 10 3.1415, 10 20 3.1415, 20 20 3.1415, 20 10 3.1415, 10 10 3.1415))")

#####


class TestConstructor(unittest.TestCase):

    def test_1(self):
        conv = Converter()
        result = LoD1Converter(conv, ifc1, "Test123", trans1, False)
        self.assertEqual(conv, result.task)
        self.assertEqual(ifc1, result.ifc)
        self.assertEqual("Test123", result.name)
        self.assertEqual(trans1, result.trans)
        self.assertFalse(result.eade)
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.geom)))
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.bldgGeom)))
        self.assertEqual(10, result.progress)
        self.assertEqual(1, result.bldgCount)

    def test_2(self):
        conv = Converter()
        result = LoD1Converter(conv, ifc2, "TestABC", trans2, True)
        self.assertEqual(conv, result.task)
        self.assertEqual(ifc2, result.ifc)
        self.assertEqual("TestABC", result.name)
        self.assertEqual(trans2, result.trans)
        self.assertTrue(result.eade)
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.geom)))
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.bldgGeom)))
        self.assertEqual(10, result.progress)
        self.assertEqual(1, result.bldgCount)


class TestConvertBound(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        result = LoD1Converter.convertBound(geom1, root, trans1)
        corr = (10, 20, 10, 20, 10, 10)
        self.assertEqual(corr, result)

    def test_2(self):
        root = etree.Element("root")
        result = LoD1Converter.convertBound(geom2, root, trans1)
        corr = (10, 90, 10, 90, 10, 10)
        self.assertEqual(corr, result)

    def test_3(self):
        root = etree.Element("root")
        result = LoD1Converter.convertBound(geom3, root, trans1)
        corr = (10, 20, 10, 20, 10, 20)
        self.assertEqual(corr, result)

    def test_4(self):
        root = etree.Element("root")
        result = LoD1Converter.convertBound(geom4, root, trans1)
        corr = (10, 90, 10, 90, 10, 20)
        self.assertEqual(corr, result)


class TestConvertBldgAttr(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        lod1Conv = LoD1Converter(Converter(), ifc1, "Test123", trans1, True)
        result = lod1Conv.convertBldgAttr(ifc1, ifcBldg1, root)
        self.assertAlmostEqual(6.51769, result, 3)
        self.assertEqual(1514, len(etree.tostring(root)))

    def test_2(self):
        root = etree.Element("root")
        lod1Conv = LoD1Converter(Converter(), ifc2, "TestABC", trans2, False)
        result = lod1Conv.convertBldgAttr(ifc2, ifcBldg2, root)
        self.assertAlmostEqual(15.34932, result, 3)
        self.assertEqual(1520, len(etree.tostring(root)))

    def test_3(self):
        root = etree.Element("root")
        lod1Conv = LoD1Converter(Converter(), ifc3, "ÄÖÜß", trans3, False)
        result = lod1Conv.convertBldgAttr(ifc3, ifcBldg3, root)
        self.assertAlmostEqual(11.01, result, 3)
        self.assertEqual(918, len(etree.tostring(root)))


class TestConvertFunctionUsage(unittest.TestCase):

    def test_1(self):
        result = LoD1Converter.convertFunctionUsage("1680")
        self.assertEqual(1680, result)

    def test_2(self):
        result = LoD1Converter.convertFunctionUsage("3210")
        self.assertIsNone(result)

    def test_3(self):
        result = LoD1Converter.convertFunctionUsage("hospital")
        self.assertEqual(2310, result)

    def test_4(self):
        result = LoD1Converter.convertFunctionUsage("Bibliothek")
        self.assertEqual(2190, result)

    def test_5(self):
        result = LoD1Converter.convertFunctionUsage("Betreutes Wohnen")
        self.assertEqual(1000, result)


class TestCalcHeight(unittest.TestCase):

    def test_1(self):
        result = LoD1Converter.calcHeight(ifc1, ifcBldg1)
        self.assertAlmostEqual(6.51769, result, 3)

    def test_2(self):
        result = LoD1Converter.calcHeight(ifc2, ifcBldg2)
        self.assertAlmostEqual(15.34932, result, 3)

    def test_3(self):
        result = LoD1Converter.calcHeight(ifc3, ifcBldg3)
        self.assertAlmostEqual(11.01, result, 3)


class TestConvertAddress(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        result = LoD1Converter.convertAddress(ifcBldg1, ifcSite1, root)
        self.assertTrue(result)
        self.assertEqual(655, len(etree.tostring(root)))

    def test_2(self):
        root = etree.Element("root")
        result = LoD1Converter.convertAddress(ifcBldg2, ifcSite2, root)
        self.assertFalse(result)
        self.assertEqual(7, len(etree.tostring(root)))

    def test_3(self):
        root = etree.Element("root")
        result = LoD1Converter.convertAddress(ifcBldg3, ifcSite3, root)
        self.assertFalse(result)
        self.assertEqual(7, len(etree.tostring(root)))


class TestCalcPlane(unittest.TestCase):

    def test_1(self):
        ifcSlabs = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[], type="BASESLAB")
        result = LoD1Converter.calcPlane(ifcSlabs, trans1)
        self.assertEqual(ifcSlabs[0], result[0])
        corr = "POLYGON ((458870.063285681 5438773.62904949 110,458862.40284125 5438780.05692559 110," + \
               "458870.116292566 5438789.24945891 110,458877.776736998 5438782.82158281 110," + \
               "458870.063285681 5438773.62904949 110))"
        self.assertEqual(corr, result[1].ExportToWkt())

    def test_2(self):
        ifcSlabs = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[], type="ROOF")
        result = LoD1Converter.calcPlane(ifcSlabs, trans1)
        self.assertEqual(ifcSlabs[0], result[0])
        corr = "POLYGON ((458878.864175246 5438782.56181742 113,458870.50793632 5438772.60323966 113," + \
               "458861.315403002 5438780.31669098 113,458869.671641928 5438790.27526874 113," + \
               "458878.864175246 5438782.56181742 113))"
        self.assertEqual(corr, result[1].ExportToWkt())

    def test_3(self):
        ifcSlabs = UtilitiesIfc.findElement(ifc2, ifcBldg2, "IfcSlab", result=[], type="FLOOR")
        result = LoD1Converter.calcPlane(ifcSlabs, trans2)
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
        result = LoD1Converter.calcPlane(ifcSlabs, trans3)
        self.assertEqual(ifcSlabs[0], result[0])
        self.assertEqual(3235, len(result[1].ExportToWkt()))


class TestConvert(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        lod1Conv = LoD1Converter(Converter(), ifc1, "Test123", trans1, True)
        result = lod1Conv.convert(root)
        self.assertEqual(11410, len(etree.tostring(result)))

    def test_2(self):
        root = etree.Element("root")
        lod1Conv = LoD1Converter(Converter(), ifc2, "TestABC", trans2, False)
        result = lod1Conv.convert(root)
        self.assertEqual(7806, len(etree.tostring(result)))

    def test_3(self):
        root = etree.Element("root")
        lod1Conv = LoD1Converter(Converter(), ifc3, "ÄÖÜß", trans3, False)
        result = lod1Conv.convert(root)
        self.assertEqual(39529, len(etree.tostring(result)))


class TestConvertSolid(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        lod1Conv = LoD1Converter(Converter(), ifc1, "Test123", trans1, True)
        result = lod1Conv.convertSolid(ifcBldg1, root, 10)
        self.assertEqual(2425, len(etree.tostring(root)))
        corr = "POLYGON ((458870.063285681 5438773.62904949 110,458862.40284125 5438780.05692559 110," + \
               "458870.116292566 5438789.24945891 110,458877.776736998 5438782.82158281 110,458870.063285681 " + \
               "5438773.62904949 110))"
        self.assertEqual(corr, result.ExportToWkt())

    def test_2(self):
        root = etree.Element("root")
        lod1Conv = LoD1Converter(Converter(), ifc2, "Test123", trans2, True)
        result = lod1Conv.convertSolid(ifcBldg2, root, 10)
        self.assertEqual(5845, len(etree.tostring(root)))
        corr = "POLYGON ((479356.600506348 5444183.43024925 -3,479356.600506348 5444185.43024925 -3," + \
               "479362.600506348 5444185.43024925 -3,479362.600506348 5444183.43024925 -3,479380.600506348 " + \
               "5444183.43024925 -3,479380.600506348 5444171.43024925 -3,479363.100506348 5444171.43024925 -3," + \
               "479363.100506348 5444167.43024925 -3,479356.100506348 5444167.43024925 -3,479356.100506348 " + \
               "5444171.43024925 -3,479338.600506348 5444171.43024925 -3,479338.600506348 5444183.43024925 -3," + \
               "479356.600506348 5444183.43024925 -3))"
        self.assertEqual(corr, result.ExportToWkt())

    def test_3(self):
        root = etree.Element("root")
        lod1Conv = LoD1Converter(Converter(), ifc3, "Test123", trans3, True)
        result = lod1Conv.convertSolid(ifcBldg3, root, 10)
        self.assertEqual(37750, len(etree.tostring(root)))
        self.assertEqual(85, result.GetGeometryRef(0).GetPointCount())


class TestCalcRoof(unittest.TestCase):

    def test_1(self):
        result = LoD1Converter.calcRoof(geom5, 10)
        corr = "POLYGON ((10 10 20,20 10 20,20 20 20,10 20 20,10 10 20))"
        self.assertEqual(corr, result.ExportToWkt())

    def test_2(self):
        result = LoD1Converter.calcRoof(geom6, 3.1415)
        corr = "POLYGON ((10 10 6.283,20 10 6.283,20 20 6.283,10 20 6.283,10 10 6.283))"
        self.assertEqual(corr, result.ExportToWkt())


class TestCalcWalls(unittest.TestCase):

    def test_1(self):
        result = LoD1Converter.calcWalls(geom5, 10)
        self.assertEqual(4, len(result))
        corr = "POLYGON ((10 10 10,10 10 20,10 20 20,10 20 10,10 10 10))"
        self.assertEqual(corr, result[0].ExportToWkt())
        corr = "POLYGON ((10 20 10,10 20 20,20 20 20,20 20 10,10 20 10))"
        self.assertEqual(corr, result[1].ExportToWkt())
        corr = "POLYGON ((20 20 10,20 20 20,20 10 20,20 10 10,20 20 10))"
        self.assertEqual(corr, result[2].ExportToWkt())
        corr = "POLYGON ((20 10 10,20 10 20,10 10 20,10 10 10,20 10 10))"
        self.assertEqual(corr, result[3].ExportToWkt())

    def test_2(self):
        result = LoD1Converter.calcWalls(geom6, 3.1415)
        corr = 4
        self.assertEqual(corr, len(result))
        corr = "POLYGON ((10 10 3.1415,10 10 6.283,10 20 6.283,10 20 3.1415,10 10 3.1415))"
        self.assertEqual(corr, result[0].ExportToWkt())
        corr = "POLYGON ((10 20 3.1415,10 20 6.283,20 20 6.283,20 20 3.1415,10 20 3.1415))"
        self.assertEqual(corr, result[1].ExportToWkt())
        corr = "POLYGON ((20 20 3.1415,20 20 6.283,20 10 6.283,20 10 3.1415,20 20 3.1415))"
        self.assertEqual(corr, result[2].ExportToWkt())
        corr = "POLYGON ((20 10 3.1415,20 10 6.283,10 10 6.283,10 10 3.1415,20 10 3.1415))"
        self.assertEqual(corr, result[3].ExportToWkt())


if __name__ == '__main__':
    unittest.main()
