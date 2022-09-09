# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (09.09.2022)

Unit-Tests für die Modelklasse LoD3Converter
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
from algorithm.converter_lod3 import LoD3Converter
from algorithm.transformer import Transformer
from algorithm.utilitiesIfc import UtilitiesIfc
from viewmodel.model import Surface

#####

LOGGER = logging.getLogger('QGIS')

# IFC-Elemente
ifc1 = ifcopenshell.open(r"data/IFC_test.ifc")
trans1 = Transformer(ifc1)
ifcSite1 = ifc1.by_type("IfcSite")[0]
ifcBldg1 = ifc1.by_type("IfcBuilding")[0]
ifcBase1 = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[], type="BASESLAB")[0]
ifcDoors1 = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcDoor", result=[])


ifc2 = ifcopenshell.open(r"data/IFC_test3.ifc")
trans2 = Transformer(ifc2)
ifcSite2 = ifc2.by_type("IfcSite")[0]
ifcBldg2 = ifc2.by_type("IfcBuilding")[0]

ifc3 = ifcopenshell.open(r"data/IFC_test4.ifc")
trans3 = Transformer(ifc3)
ifcSite3 = ifc1.by_type("IfcSite")[0]
ifcBldg3 = ifc3.by_type("IfcBuilding")[0]

ifc4 = ifcopenshell.open(r"data/IFC_test2.ifc")
trans4 = Transformer(ifc4)
ifcBldg4 = ifc4.by_type("IfcBuilding")[0]
ifcWalls4 = UtilitiesIfc.findElement(ifc4, ifcBldg4, "IfcWall", result=[])

# Geometrien
geom1 = ogr.CreateGeometryFromWkt("GeometryCollection(Polygon((10 10 10, 10 20 10, 20 20 10, 20 15 10, 10 10 10)))")
geom2 = ogr.CreateGeometryFromWkt("GeometryCollection(Polygon((10 10 10, 10 20 10, 20 20 10, 20 15 10, 10 10 10)), " +
                                  "Polygon((50 50 10, 50 90 10, 90 90 10, 90 70 10, 50 50 10)))")
geom3 = ogr.CreateGeometryFromWkt("GeometryCollection(Polygon((10 10 10, 10 20 10, 20 20 20, 20 15 20, 10 10 10)))")
geom4 = ogr.CreateGeometryFromWkt("GeometryCollection(Polygon((10 10 10, 10 20 10, 20 20 10, 20 15 10, 10 10 10)), " +
                                  "Polygon((50 50 10, 50 90 10, 90 90 10, 90 70 10, 50 50 10)), " +
                                  "Polygon((10 10 10, 10 20 10, 20 20 20, 20 15 20, 10 10 10)))")
baseGeom = ogr.CreateGeometryFromWkt("Polygon((0 0 0, -20 0 0, -20 -20 0, 0 -20 0, 0 0 0))")

wall1Geom = ogr.CreateGeometryFromWkt("Polygon((0 0 0, 20 0 0, 20 0 10, 0 0 10, 0 0 0))")
wall2Geom = ogr.CreateGeometryFromWkt("Polygon((0 30 10, 20 30 10, 20 30 20, 0 30 20, 0 30 10))")
door1Geom = [[8, 0, 0], [8, 0, 2], [10, 0, 2], [10, 0, 0]]
door2Geom = ogr.CreateGeometryFromWkt("Polygon((8 0 0, 8 0 2, 10 0 2, 10 0 0, 8 0 0))")

# Plugin
base = Surface([baseGeom], "Base-123", ifcBase1, "Base")
wall1 = Surface([wall1Geom], "Wand-Ext-Test123", ifcWalls4[0], "Wall")
wall2 = Surface([wall2Geom], "Wand-Ext-Test123", ifcWalls4[1], "Wall")
door1 = Surface(door1Geom, "Tür-Ext-TestABC", ifcDoors1[3], "IfcDoor")
door2 = Surface([door2Geom], "Tür-Ext-TestABC", ifcDoors1[3], "IfcDoor")


#####


class TestConstructor(unittest.TestCase):

    def test_1(self):
        conv = Converter()
        result = LoD3Converter(conv, ifc1, "Test123", trans1, False)
        self.assertEqual(conv, result.task)
        self.assertEqual(ifc1, result.ifc)
        self.assertEqual("Test123", result.name)
        self.assertEqual(trans1, result.trans)
        self.assertFalse(result.eade)
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.geom)))
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.bldgGeom)))
        self.assertEqual(5, result.progress)
        self.assertEqual(1, result.bldgCount)

    def test_2(self):
        conv = Converter()
        result = LoD3Converter(conv, ifc2, "TestABC", trans2, True)
        self.assertEqual(conv, result.task)
        self.assertEqual(ifc2, result.ifc)
        self.assertEqual("TestABC", result.name)
        self.assertEqual(trans2, result.trans)
        self.assertTrue(result.eade)
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.geom)))
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.bldgGeom)))
        self.assertEqual(5, result.progress)
        self.assertEqual(1, result.bldgCount)


class TestConvertBound(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        result = LoD3Converter.convertBound(geom1, root, trans1)
        corr = (10, 20, 10, 20, 10, 10)
        self.assertEqual(corr, result)

    def test_2(self):
        root = etree.Element("root")
        result = LoD3Converter.convertBound(geom2, root, trans1)
        corr = (10, 90, 10, 90, 10, 10)
        self.assertEqual(corr, result)

    def test_3(self):
        root = etree.Element("root")
        result = LoD3Converter.convertBound(geom3, root, trans1)
        corr = (10, 20, 10, 20, 10, 20)
        self.assertEqual(corr, result)

    def test_4(self):
        root = etree.Element("root")
        result = LoD3Converter.convertBound(geom4, root, trans1)
        corr = (10, 90, 10, 90, 10, 20)
        self.assertEqual(corr, result)


class TestConvertBldgAttr(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        lod3Conv = LoD3Converter(Converter(), ifc1, "Test123", trans1, False)
        result = lod3Conv.convertBldgAttr(ifc1, ifcBldg1, root)
        self.assertAlmostEqual(6.51769, result, 3)
        self.assertEqual(1514, len(etree.tostring(root)))

    def test_2(self):
        root = etree.Element("root")
        lod3Conv = LoD3Converter(Converter(), ifc2, "Test123", trans2, False)
        result = lod3Conv.convertBldgAttr(ifc2, ifcBldg2, root)
        self.assertAlmostEqual(15.34932, result, 3)
        self.assertEqual(1520, len(etree.tostring(root)))

    def test_3(self):
        root = etree.Element("root")
        lod3Conv = LoD3Converter(Converter(), ifc2, "TestABC", trans2, False)
        result = lod3Conv.convertBldgAttr(ifc3, ifcBldg3, root)
        self.assertAlmostEqual(11.01, result, 3)
        self.assertEqual(918, len(etree.tostring(root)))


class TestConvertFunctionUsage(unittest.TestCase):

    def test_1(self):
        result = LoD3Converter.convertFunctionUsage("1680")
        self.assertEqual(1680, result)

    def test_2(self):
        result = LoD3Converter.convertFunctionUsage("3210")
        self.assertIsNone(result)

    def test_3(self):
        result = LoD3Converter.convertFunctionUsage("hospital")
        self.assertEqual(2310, result)

    def test_4(self):
        result = LoD3Converter.convertFunctionUsage("Bibliothek")
        self.assertEqual(2190, result)

    def test_5(self):
        result = LoD3Converter.convertFunctionUsage("Betreutes Wohnen")
        self.assertEqual(1000, result)


class TestCalcHeight(unittest.TestCase):

    def test_1(self):
        result = LoD3Converter.calcHeight(ifc1, ifcBldg1)
        self.assertAlmostEqual(6.51769, result, 3)

    def test_2(self):
        result = LoD3Converter.calcHeight(ifc2, ifcBldg2)
        self.assertAlmostEqual(15.34932, result, 3)

    def test_3(self):
        result = LoD3Converter.calcHeight(ifc3, ifcBldg3)
        self.assertAlmostEqual(11.01, result, 3)


class TestConvertAddress(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        result = LoD3Converter.convertAddress(ifcBldg1, ifcSite1, root)
        self.assertTrue(result)
        self.assertEqual(655, len(etree.tostring(root)))

    def test_2(self):
        root = etree.Element("root")
        result = LoD3Converter.convertAddress(ifcBldg2, ifcSite2, root)
        self.assertFalse(result)
        self.assertEqual(7, len(etree.tostring(root)))

    def test_3(self):
        root = etree.Element("root")
        result = LoD3Converter.convertAddress(ifcBldg3, ifcSite3, root)
        self.assertFalse(result)
        self.assertEqual(7, len(etree.tostring(root)))


class TestCalcPlane(unittest.TestCase):

    def test_1(self):
        ifcSlabs = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[], type="BASESLAB")
        result = LoD3Converter.calcPlane(ifcSlabs, trans1)
        self.assertEqual(ifcSlabs[0], result[0])
        corr = "POLYGON ((458870.063285681 5438773.62904949 110,458862.40284125 5438780.05692559 110," + \
               "458870.116292566 5438789.24945891 110,458877.776736998 5438782.82158281 110," + \
               "458870.063285681 5438773.62904949 110))"
        self.assertEqual(corr, result[1].ExportToWkt())

    def test_2(self):
        ifcSlabs = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[], type="ROOF")
        result = LoD3Converter.calcPlane(ifcSlabs, trans1)
        self.assertEqual(ifcSlabs[0], result[0])
        corr = "POLYGON ((458878.864175246 5438782.56181742 113,458870.50793632 5438772.60323966 113," + \
               "458861.315403002 5438780.31669098 113,458869.671641928 5438790.27526874 113," + \
               "458878.864175246 5438782.56181742 113))"
        self.assertEqual(corr, result[1].ExportToWkt())

    def test_3(self):
        ifcSlabs = UtilitiesIfc.findElement(ifc2, ifcBldg2, "IfcSlab", result=[], type="FLOOR")
        result = LoD3Converter.calcPlane(ifcSlabs, trans2)
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
        result = LoD3Converter.calcPlane(ifcSlabs, trans3)
        self.assertEqual(ifcSlabs[0], result[0])
        self.assertEqual(3235, len(result[1].ExportToWkt()))


class TestConvertSolid(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        LoD3Converter.convertSolid(root, ["ABC123", "GML_ID1234567890", "987zyx"], 2)
        corr = b'<root><ns0:lod2Solid xmlns:ns0="http://www.opengis.net/citygml/building/2.0"><ns1:Solid xmlns:ns1=' + \
               b'"http://www.opengis.net/gml"><ns1:exterior><ns1:CompositeSurface><ns1:surfaceMember xmlns:ns2=' + \
               b'"http://www.w3.org/1999/xlink" ns2:href="#ABC123"/><ns1:surfaceMember xmlns:ns3=' + \
               b'"http://www.w3.org/1999/xlink" ns3:href="#GML_ID1234567890"/><ns1:surfaceMember xmlns:ns4=' + \
               b'"http://www.w3.org/1999/xlink" ns4:href="#987zyx"/></ns1:CompositeSurface></ns1:exterior>' + \
               b'</ns1:Solid></ns0:lod2Solid></root>'
        self.assertEqual(corr, etree.tostring(root))

    def test_2(self):
        root = etree.Element("root")
        LoD3Converter.convertSolid(root, [], 3)
        self.assertEqual(b'<root/>', etree.tostring(root))


class TestCalcBases(unittest.TestCase):

    def test_1(self):
        lod3Conv = LoD3Converter(Converter(), ifc1, "Test123", trans1, False)
        result1, result2, result3 = lod3Conv.calcBases(ifcBldg1)
        self.assertEqual(1, len(result1))
        corr = "POLYGON ((458870.063285681 5438773.62904949 109.8,458862.40284125 5438780.05692559 109.8," + \
               "458870.116292566 5438789.24945891 109.8,458877.776736998 5438782.82158281 109.8,458870.063285681 " + \
               "5438773.62904949 109.8))"
        self.assertEqual(corr, result1[0].geom[0].ExportToWkt())
        self.assertEqual("Bodenplatte", result1[0].name)
        self.assertEqual([], result1[0].openings)
        corr = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[], type="BASESLAB")[0]
        self.assertEqual(str(corr), str(result1[0].ifcElem))
        self.assertEqual(6, len(result2[0]))
        corr = "POLYGON ((458862.40284125 5438780.05692559 110,458862.40284125 5438780.05692559 109.8," + \
               "458870.063285681 5438773.62904949 109.8,458870.063285681 5438773.62904949 110,458862.40284125 " + \
               "5438780.05692559 110))"
        self.assertEqual(corr, result2[0][0].ExportToWkt())
        corr = "POLYGON ((458870.063285681 5438773.62904949 109.8,458862.40284125 5438780.05692559 109.8," + \
               "458870.116292566 5438789.24945891 109.8,458877.776736998 5438782.82158281 109.8,458870.063285681 " + \
               "5438773.62904949 109.8))"
        self.assertEqual(corr, result3[0].geom[0].ExportToWkt())

    def test_2(self):
        lod3Conv = LoD3Converter(Converter(), ifc2, "Test123", trans2, False)
        result1, result2, result3 = lod3Conv.calcBases(ifcBldg2)
        self.assertEqual(3, len(result1))
        corr = "POLYGON ((479338.600506348 5444171.43024925 -3.3,479338.600506348 5444183.43024925 -3.3," + \
               "479356.600506348 5444183.43024925 -3.3,479356.600506348 5444185.43024925 -3.3,479362.600506348 " + \
               "5444185.43024925 -3.3,479362.600506348 5444183.43024925 -3.3,479380.600506348 5444183.43024925 " + \
               "-3.3,479380.600506348 5444171.43024925 -3.3,479338.600506348 5444171.43024925 -3.3))"
        self.assertEqual(corr, result1[0].geom[0].ExportToWkt())
        self.assertEqual("Decke-002", result1[0].name)
        self.assertEqual([], result1[0].openings)
        corr = UtilitiesIfc.findElement(ifc2, ifcBldg2, "IfcSlab", result=[], type="FLOOR")[0]
        self.assertEqual(str(corr), str(result1[0].ifcElem))
        self.assertEqual(10, len(result2[0]))
        corr = "POLYGON ((479338.600506348 5444171.43024925 -3,479338.600506348 5444171.43024925 -3.3," + \
               "479380.600506348 5444171.43024925 -3.3,479380.600506348 5444171.43024925 -3,479338.600506348 " + \
               "5444171.43024925 -3))"
        self.assertEqual(corr, result2[0][0].ExportToWkt())
        self.assertEqual(5, len(result3))
        corr = "POLYGON ((479338.600506348 5444171.43024925 -3.3,479338.600506348 5444183.43024925 -3.3," + \
               "479356.600506348 5444183.43024925 -3.3,479356.600506348 5444185.43024925 -3.3,479362.600506348 " + \
               "5444185.43024925 -3.3,479362.600506348 5444183.43024925 -3.3,479380.600506348 5444183.43024925 " + \
               "-3.3,479380.600506348 5444171.43024925 -3.3,479338.600506348 5444171.43024925 -3.3))"
        self.assertEqual(corr, result3[0].geom[0].ExportToWkt())

    def test_3(self):
        lod3Conv = LoD3Converter(Converter(), ifc3, "Test123", trans2, False)
        result1, result2, result3 = lod3Conv.calcBases(ifcBldg3)
        self.assertEqual(40, len(result1))
        corr = "POLYGON ((479338.600506348 5444169.43024925 -3.06,479338.600506348 5444176.34024925 -3.06," + \
               "479346.075506348 5444176.34024925 -3.06,479346.075506348 5444169.43024925 -3.06,479338.600506348 " + \
               "5444169.43024925 -3.06))"
        self.assertEqual(corr, result1[0].geom[0].ExportToWkt())
        self.assertEqual("Keller-Boden-01", result1[0].name)
        self.assertEqual([], result1[0].openings)
        corr = UtilitiesIfc.findElement(ifc3, ifcBldg3, "IfcSlab", result=[], type="FLOOR")[0]
        self.assertEqual(str(corr), str(result1[0].ifcElem))
        self.assertEqual(6, len(result2[0]))
        corr = "POLYGON ((479346.075506348 5444169.43024925 -2.81,479346.075506348 5444169.43024925 -3.06," + \
               "479346.075506348 5444176.34024925 -3.06,479346.075506348 5444176.34024925 -2.81,479346.075506348 " + \
               "5444169.43024925 -2.81))"
        self.assertEqual(corr, result2[0][0].ExportToWkt())
        self.assertEqual(100, len(result3))
        corr = "POLYGON ((479338.600506348 5444169.43024925 -3.06,479338.600506348 5444176.34024925 -3.06," + \
               "479346.075506348 5444176.34024925 -3.06,479346.075506348 5444169.43024925 -3.06,479338.600506348 " + \
               "5444169.43024925 -3.06))"
        self.assertEqual(corr, result3[0].geom[0].ExportToWkt())


class TestCalcRoofs(unittest.TestCase):

    def test_1(self):
        lod3Conv = LoD3Converter(Converter(), ifc1, "Test123", trans1, False)
        result1, result2 = lod3Conv.calcRoofs(ifcBldg1)
        self.assertEqual(2, len(result1))
        corr = "POLYGON ((458870.05466415 5438789.95387493 113.14226,458861.698425224 5438779.99529717 113.14226," + \
               "458865.911669661 5438776.45996532 116.31769,458874.267908587 5438786.41854308 116.31769," + \
               "458870.05466415 5438789.95387493 113.14226))"
        self.assertEqual(corr, result1[0].geom[0].ExportToWkt())
        self.assertEqual("Dach-1", result1[0].name)
        self.assertEqual([], result1[0].openings)
        corr = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[], type="ROOF")[0]
        self.assertEqual(str(corr), str(result1[0].ifcElem))
        self.assertEqual(6, len(result2[0]))
        corr = "POLYGON ((458865.911669661 5438776.45996532 116.31769,458865.911669661 5438776.45996532 116.08675," + \
               "458874.267908587 5438786.41854308 116.08675,458874.267908587 5438786.41854308 116.31769," + \
               "458865.911669661 5438776.45996532 116.31769))"
        self.assertEqual(corr, result2[0][0].ExportToWkt())

    def test_2(self):
        lod3Conv = LoD3Converter(Converter(), ifc2, "Test123", trans2, False)
        result1, result2 = lod3Conv.calcRoofs(ifcBldg2)
        self.assertEqual(21, len(result1))
        corr = "POLYGON ((479356.600506348 5444182.54302925 10.09998,479337.600506348 5444182.54302925 10.09998," + \
               "479337.600506348 5444180.54352925 10.71118,479356.600506348 5444180.54352925 10.71118," + \
               "479356.600506348 5444182.54302925 10.09998))"
        self.assertEqual(corr, result1[0].geom[0].ExportToWkt())
        self.assertEqual("Dach-001", result1[0].name)
        self.assertEqual([], result1[0].openings)
        corr = UtilitiesIfc.findElement(ifc2, ifcBldg2, "IfcSlab", result=[], type="ROOF")[0]
        self.assertEqual(str(corr), str(result1[0].ifcElem))
        self.assertEqual(6, len(result2[0]))
        corr = "POLYGON ((479356.600506348 5444182.54302925 10.09998,479337.600506348 5444182.54302925 10.09998," + \
               "479337.600506348 5444180.54352925 10.71118,479356.600506348 5444180.54352925 10.71118," + \
               "479356.600506348 5444182.54302925 10.09998))"
        self.assertEqual(corr, result2[0][0].ExportToWkt())

    def test_3(self):
        lod3Conv = LoD3Converter(Converter(), ifc3, "Test123", trans3, False)
        result1, result2 = lod3Conv.calcRoofs(ifcBldg3)
        self.assertEqual(20, len(result1))
        corr = "POLYGON ((455480.005320756 5431327.26161912 112.77785,455483.082417578 5431329.22194599 112.77785," + \
               "455482.161518287 5431330.66746833 112.41355,455479.084421465 5431328.70714145 112.41355," + \
               "455480.005320756 5431327.26161912 112.77785))"
        self.assertEqual(corr, result1[0].geom[0].ExportToWkt())
        self.assertEqual("EG-Vordach-01", result1[0].name)
        self.assertEqual([], result1[0].openings)
        corr = UtilitiesIfc.findElement(ifc3, ifcBldg3, "IfcSlab", result=[], type="ROOF")[0]
        self.assertEqual(str(corr), str(result1[0].ifcElem))
        self.assertEqual(6, len(result2[0]))
        corr = "POLYGON ((455482.161518287 5431330.66746833 112.41355,455482.161518287 5431330.66746833 112.31355," + \
               "455479.084421465 5431328.70714145 112.31355,455479.084421465 5431328.70714145 112.41355," + \
               "455482.161518287 5431330.66746833 112.41355))"
        self.assertEqual(corr, result2[0][0].ExportToWkt())


class TestCalcWalls(unittest.TestCase):

    def test_1(self):
        lod3Conv = LoD3Converter(Converter(), ifc4, "Test123", trans4, False)
        result = lod3Conv.calcWalls(ifcBldg4)
        self.assertEqual(4, len(result))
        self.assertEqual(18, len(result[0].geom))
        self.assertEqual("Wand-Ext-ERDG-1", result[0].name)
        self.assertEqual([], result[0].openings)
        corr = UtilitiesIfc.findElement(ifc4, ifcBldg4, "IfcWall", result=[])[5]
        self.assertEqual(corr, result[0].ifcElem)
        self.assertEqual(18, len(result[1].geom))
        self.assertEqual("Wand-Ext-ERDG-4", result[1].name)
        self.assertEqual([], result[1].openings)
        corr = UtilitiesIfc.findElement(ifc4, ifcBldg4, "IfcWall", result=[])[6]
        self.assertEqual(corr, result[1].ifcElem)


class TestCalcOpenings(unittest.TestCase):

    def test_1(self):
        lod3Conv = LoD3Converter(Converter(), ifc1, "Test123", trans1, False)
        result = lod3Conv.calcOpenings(ifcBldg1, "ifcDoor")
        self.assertEqual(2, len(result))
        self.assertEqual(44, len(result[0].geom))
        self.assertEqual("Haustuer", result[0].name)
        self.assertEqual("ifcDoor", result[0].type)
        corr = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcDoor", result=[])[3]
        self.assertEqual(corr, result[0].ifcElem)
        self.assertEqual(28, len(result[1].geom))
        self.assertEqual("Terrassentuer", result[1].name)
        self.assertEqual("ifcDoor", result[1].type)
        corr = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcDoor", result=[])[4]
        self.assertEqual(corr, result[1].ifcElem)

    def test_2(self):
        lod3Conv = LoD3Converter(Converter(), ifc1, "Test123", trans1, False)
        result = lod3Conv.calcOpenings(ifcBldg1, "ifcWindow")
        self.assertEqual(11, len(result))
        self.assertEqual(12, len(result[0].geom))
        self.assertEqual("EG-Fenster-6", result[0].name)
        self.assertEqual("ifcWindow", result[0].type)
        corr = UtilitiesIfc.findElement(ifc1, ifcBldg1, "ifcWindow", result=[])[0]
        self.assertEqual(corr, result[0].ifcElem)
        self.assertEqual(12, len(result[1].geom))
        self.assertEqual("EG-Fenster-7", result[1].name)
        self.assertEqual("ifcWindow", result[1].type)
        corr = UtilitiesIfc.findElement(ifc1, ifcBldg1, "ifcWindow", result=[])[1]
        self.assertEqual(corr, result[1].ifcElem)

    def test_3(self):
        lod3Conv = LoD3Converter(Converter(), ifc2, "TestABC", trans2, False)
        result = lod3Conv.calcOpenings(ifcBldg2, "ifcDoor")
        self.assertEqual(1, len(result))
        self.assertEqual(70, len(result[0].geom))
        self.assertEqual("Tür-019", result[0].name)
        self.assertEqual("ifcDoor", result[0].type)
        corr = UtilitiesIfc.findElement(ifc2, ifcBldg2, "IfcDoor", result=[])[16]
        self.assertEqual(corr, result[0].ifcElem)


class TestAssignOpenings(unittest.TestCase):

    def test_1(self):
        lod3Conv = LoD3Converter(Converter(), ifc1, "Test123", trans1, False)
        result = lod3Conv.assignOpenings([door1], [wall1, wall2])
        self.assertEqual(2, len(result))
        self.assertEqual(1, len(result[0].openings))
        self.assertEqual(door1, result[0].openings[0])
        self.assertEqual(0, len(result[1].openings))


class TestSetElementGroup(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        lod3Conv = LoD3Converter(Converter(), ifc1, "Test123", trans1, False)
        result1, result2, result3 = lod3Conv.setElementGroup(root, base.geom, "GroundSurface", base.name, base.openings)
        self.assertEqual(741, len(etree.tostring(root)))
        self.assertEqual(42, len(result1[0]))
        self.assertEqual(40, len(result2))
        self.assertEqual(0, len(result3))

    def test_2(self):
        root = etree.Element("root")
        lod3Conv = LoD3Converter(Converter(), ifc1, "Test123", trans1, False)
        result1, result2, result3 = lod3Conv.setElementGroup(root, wall1.geom, "WallSurface", wall1.name, [door2])
        self.assertEqual(1360, len(etree.tostring(root)))
        self.assertEqual(42, len(result1[0]))
        self.assertEqual(40, len(result2))
        self.assertEqual(1, len(result3))

    def test_3(self):
        root = etree.Element("root")
        lod3Conv = LoD3Converter(Converter(), ifc1, "Test123", trans1, False)
        result1, result2, result3 = lod3Conv.setElementGroup(root, wall2.geom, "WallSurface", wall2.name, [])
        self.assertEqual(749, len(etree.tostring(root)))
        self.assertEqual(42, len(result1[0]))
        self.assertEqual(40, len(result2))
        self.assertEqual(0, len(result3))


# convert, convertBldgBound, adjustWallOpenings und adjustWallSize sind aufgrund der langen, mehrminütigen Rechenzeit
#   sowie des komplexen In- und Outpus nicht vernünftig testbar.

if __name__ == '__main__':
    unittest.main()
