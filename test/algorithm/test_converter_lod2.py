# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (09.09.2022)

Unit-Tests für die Modelklasse LoD2Converter
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
from algorithm.converter_lod2 import LoD2Converter
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
ifcRoofs1 = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[], type="ROOF")
ifcWalls1 = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcWall", result=[])

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
baseGeom = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 20 10, 20 20 10, 20 10 10, 10 10 10))")
roof1Geom = ogr.CreateGeometryFromWkt("Polygon((9 9 10, 9 15 15, 21 15 15, 21 9 10, 9 9 10))")
roof2Geom = ogr.CreateGeometryFromWkt("Polygon((9 15 15, 9 21 10, 21 21 10, 21 15 15, 9 15 15))")
wall1Geom = ogr.CreateGeometryFromWkt("Polygon((10 10 10,10 10 10.8333333333333,10 15 15,10 20 10.8333333333333," +
                                      "10 20 10,10 10 10))")
wall2Geom = ogr.CreateGeometryFromWkt("Polygon((10 20 10,10 20 10.8333333333333,20 20 10.8333333333333,20 20 10," +
                                      "10 20 10))")
wall3Geom = ogr.CreateGeometryFromWkt("Polygon((20 20 10,20 20 10.8333333333333,20 15 15,20 10 10.8333333333333," +
                                      "20 10 10,20 20 10))")
wall4Geom = ogr.CreateGeometryFromWkt("Polygon((20 10 10,20 10 10.8333333333333,10 10 10.8333333333333,10 10 10," +
                                      "20 10 10))")

# Plugin
base = Surface(baseGeom, "Base-123", ifcBase1, "Base")
roof1 = Surface(roof1Geom, "Roof-123", ifcRoofs1[0], "Roof")
roof2 = Surface(roof2Geom, "Roof-987", ifcRoofs1[1], "Roof")
wall1 = Surface(wall1Geom, "Wall-123", ifcWalls1[0], "Wall")
wall2 = Surface(wall2Geom, "Wall-987", ifcWalls1[1], "Wall")
wall3 = Surface(wall3Geom, "Wall-ABC", ifcWalls1[2], "Wall")
wall4 = Surface(wall4Geom, "Wall-ÄÖÜß", ifcWalls1[3], "Wall")


#####


class TestConstructor(unittest.TestCase):

    def test_1(self):
        conv = Converter()
        result = LoD2Converter(conv, ifc1, "Test123", trans1, False)
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
        result = LoD2Converter(conv, ifc2, "TestABC", trans2, True)
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
        result = LoD2Converter.convertBound(geom1, root, trans1)
        corr = (10, 20, 10, 20, 10, 10)
        self.assertEqual(corr, result)

    def test_2(self):
        root = etree.Element("root")
        result = LoD2Converter.convertBound(geom2, root, trans1)
        corr = (10, 90, 10, 90, 10, 10)
        self.assertEqual(corr, result)

    def test_3(self):
        root = etree.Element("root")
        result = LoD2Converter.convertBound(geom3, root, trans1)
        corr = (10, 20, 10, 20, 10, 20)
        self.assertEqual(corr, result)

    def test_4(self):
        root = etree.Element("root")
        result = LoD2Converter.convertBound(geom4, root, trans1)
        corr = (10, 90, 10, 90, 10, 20)
        self.assertEqual(corr, result)


class TestConvertBldgAttr(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        lod2Conv = LoD2Converter(Converter(), ifc1, "Test123", trans1, True)
        result = lod2Conv.convertBldgAttr(ifc1, ifcBldg1, root)
        self.assertAlmostEqual(6.51769, result, 3)
        self.assertEqual(1514, len(etree.tostring(root)))

    def test_2(self):
        root = etree.Element("root")
        lod2Conv = LoD2Converter(Converter(), ifc2, "Test123", trans2, False)
        result = lod2Conv.convertBldgAttr(ifc2, ifcBldg2, root)
        self.assertAlmostEqual(15.34932, result, 3)
        self.assertEqual(1520, len(etree.tostring(root)))

    def test_3(self):
        root = etree.Element("root")
        lod2Conv = LoD2Converter(Converter(), ifc3, "Test123", trans3, False)
        result = lod2Conv.convertBldgAttr(ifc3, ifcBldg3, root)
        self.assertAlmostEqual(11.01, result, 3)
        self.assertEqual(918, len(etree.tostring(root)))


class TestConvertFunctionUsage(unittest.TestCase):

    def test_1(self):
        result = LoD2Converter.convertFunctionUsage("1680")
        self.assertEqual(1680, result)

    def test_2(self):
        result = LoD2Converter.convertFunctionUsage("3210")
        self.assertIsNone(result)

    def test_3(self):
        result = LoD2Converter.convertFunctionUsage("hospital")
        self.assertEqual(2310, result)

    def test_4(self):
        result = LoD2Converter.convertFunctionUsage("Bibliothek")
        self.assertEqual(2190, result)

    def test_5(self):
        result = LoD2Converter.convertFunctionUsage("Betreutes Wohnen")
        self.assertEqual(1000, result)


class TestCalcHeight(unittest.TestCase):

    def test_1(self):
        result = LoD2Converter.calcHeight(ifc1, ifcBldg1)
        self.assertAlmostEqual(6.51769, result, 3)

    def test_2(self):
        result = LoD2Converter.calcHeight(ifc2, ifcBldg2)
        self.assertAlmostEqual(15.34932, result, 3)

    def test_3(self):
        result = LoD2Converter.calcHeight(ifc3, ifcBldg3)
        self.assertAlmostEqual(11.01, result, 3)


class TestConvertAddress(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        result = LoD2Converter.convertAddress(ifcBldg1, ifcSite1, root)
        self.assertTrue(result)
        self.assertEqual(655, len(etree.tostring(root)))

    def test_2(self):
        root = etree.Element("root")
        result = LoD2Converter.convertAddress(ifcBldg2, ifcSite2, root)
        self.assertFalse(result)
        self.assertEqual(7, len(etree.tostring(root)))

    def test_3(self):
        root = etree.Element("root")
        result = LoD2Converter.convertAddress(ifcBldg3, ifcSite3, root)
        self.assertFalse(result)
        self.assertEqual(7, len(etree.tostring(root)))


class TestCalcPlane(unittest.TestCase):

    def test_1(self):
        ifcSlabs = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[], type="BASESLAB")
        result = LoD2Converter.calcPlane(ifcSlabs, trans1)
        self.assertEqual(ifcSlabs[0], result[0])
        corr = "POLYGON ((458870.063285681 5438773.62904949 110,458862.40284125 5438780.05692559 110," + \
               "458870.116292566 5438789.24945891 110,458877.776736998 5438782.82158281 110," + \
               "458870.063285681 5438773.62904949 110))"
        self.assertEqual(corr, result[1].ExportToWkt())

    def test_2(self):
        ifcSlabs = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[], type="ROOF")
        result = LoD2Converter.calcPlane(ifcSlabs, trans1)
        self.assertEqual(ifcSlabs[0], result[0])
        corr = "POLYGON ((458878.864175246 5438782.56181742 113,458870.50793632 5438772.60323966 113," + \
               "458861.315403002 5438780.31669098 113,458869.671641928 5438790.27526874 113," + \
               "458878.864175246 5438782.56181742 113))"
        self.assertEqual(corr, result[1].ExportToWkt())

    def test_3(self):
        ifcSlabs = UtilitiesIfc.findElement(ifc2, ifcBldg2, "IfcSlab", result=[], type="FLOOR")
        result = LoD2Converter.calcPlane(ifcSlabs, trans2)
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
        result = LoD2Converter.calcPlane(ifcSlabs, trans3)
        self.assertEqual(ifcSlabs[0], result[0])
        self.assertEqual(3235, len(result[1].ExportToWkt()))


class TestConvertSolid(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        LoD2Converter.convertSolid(root, ["ABC123", "GML_ID1234567890", "987zyx"], 2)
        corr = b'<root><ns0:lod2Solid xmlns:ns0="http://www.opengis.net/citygml/building/2.0"><ns1:Solid xmlns:ns1=' + \
               b'"http://www.opengis.net/gml"><ns1:exterior><ns1:CompositeSurface><ns1:surfaceMember xmlns:ns2=' + \
               b'"http://www.w3.org/1999/xlink" ns2:href="#ABC123"/><ns1:surfaceMember xmlns:ns3=' + \
               b'"http://www.w3.org/1999/xlink" ns3:href="#GML_ID1234567890"/><ns1:surfaceMember xmlns:ns4=' + \
               b'"http://www.w3.org/1999/xlink" ns4:href="#987zyx"/></ns1:CompositeSurface></ns1:exterior>' + \
               b'</ns1:Solid></ns0:lod2Solid></root>'
        self.assertEqual(corr, etree.tostring(root))

    def test_2(self):
        root = etree.Element("root")
        LoD2Converter.convertSolid(root, [], 3)
        self.assertEqual(b'<root/>', etree.tostring(root))


class TestConvert(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        lod2Conv = LoD2Converter(Converter(), ifc1, "Test123", trans1, True)
        result = lod2Conv.convert(root)
        self.assertEqual(24433, len(etree.tostring(result)))


class TestConvertBldgBound(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        lod2Conv = LoD2Converter(Converter(), ifc1, "Test123", trans1, True)
        result1, result2, result3 = lod2Conv.convertBldgBound(ifcBldg1, root, 10)
        self.assertEqual(5555, len(etree.tostring(root)))
        self.assertEqual(7, len(result1))
        corr = "POLYGON ((458870.063285681 5438773.62904949 110,458862.40284125 5438780.05692559 110," + \
               "458870.116292566 5438789.24945891 110,458877.776736998 5438782.82158281 110,458870.063285681 " + \
               "5438773.62904949 110))"
        self.assertEqual(corr, result2.ExportToWkt())
        self.assertEqual(7, len(result3))
        corr = "#34509=IfcSlab('1pPHnf7cXCpPsNEnQf8_6B',#12,'Bodenplatte',$,$,#34464,#34505," + \
               "'E4D9CD4B-CA43-4735-94-BD-1FD4376BD455',.BASESLAB.)"
        self.assertEqual(corr, str(result3[0].ifcElem))


class TestExtractRoofs(unittest.TestCase):

    def test_1(self):
        lod2Conv = LoD2Converter(Converter(), ifc1, "Test123", trans1, False)
        ifcRoofs = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[], type="ROOF")
        result = lod2Conv.extractRoofs(ifcRoofs)
        self.assertEqual(2, len(result))
        corr = "POLYGON ((458861.698425224 5438779.99529717 113.14226,458870.05466415 5438789.95387493 113.14226," + \
               "458874.267908587 5438786.41854308 116.31769,458865.911669661 5438776.45996532 116.31769," + \
               "458861.698425224 5438779.99529717 113.14226))"
        self.assertEqual(corr, result[0].geom.ExportToWkt())
        self.assertEqual(ifcRoofs[0], result[0].ifcElem)
        self.assertEqual("Dach-1", result[0].name)
        self.assertEqual("Roof", result[0].type)

    def test_2(self):
        lod2Conv = LoD2Converter(Converter(), ifc2, "Test123", trans2, False)
        ifcRoofs = UtilitiesIfc.findElement(ifc2, ifcBldg2, "IfcSlab", result=[], type="ROOF")
        result = lod2Conv.extractRoofs(ifcRoofs)
        self.assertEqual(21, len(result))
        corr = "POLYGON ((479337.600506348 5444182.54302925 10.09998,479356.600506348 5444182.54302925 10.09998," + \
               "479356.600506348 5444180.54352925 10.71118,479337.600506348 5444180.54352925 10.71118," + \
               "479337.600506348 5444182.54302925 10.09998))"
        self.assertEqual(corr, result[0].geom.ExportToWkt())
        self.assertEqual(ifcRoofs[0], result[0].ifcElem)
        self.assertEqual("Dach-001", result[0].name)
        self.assertEqual("Roof", result[0].type)

    def test_3(self):
        lod2Conv = LoD2Converter(Converter(), ifc3, "Test123", trans3, False)
        ifcRoofs = UtilitiesIfc.findElement(ifc3, ifcBldg3, "IfcSlab", result=[], type="ROOF")
        result = lod2Conv.extractRoofs(ifcRoofs)
        self.assertEqual(20, len(result))
        corr = "POLYGON ((455479.084421465 5431328.70714145 112.41355,455482.161518287 5431330.66746833 112.41355," + \
               "455483.082417578 5431329.22194599 112.77785,455480.005320756 5431327.26161912 112.77785," + \
               "455479.084421465 5431328.70714145 112.41355))"
        self.assertEqual(corr, result[0].geom.ExportToWkt())
        self.assertEqual(ifcRoofs[0], result[0].ifcElem)
        self.assertEqual("EG-Vordach-01", result[0].name)
        self.assertEqual("Roof", result[0].type)


class TestCalcWalls(unittest.TestCase):

    def test_1(self):
        lod2Conv = LoD2Converter(Converter(), ifc1, "Test123", trans1, False)
        result1, result2 = lod2Conv.calcWalls(base, [roof1, roof2], 10)
        self.assertEqual(4, len(result1))
        corr = "POLYGON ((10 10 10,10 10 10.8333333333333,10 15 15,10 15 15,10 20 10.8333333333333,10 20 10,10 10 10))"
        self.assertEqual(corr, result1[0].geom.ExportToWkt())
        corr = "POLYGON ((10 20 10,10 20 10.8333333333333,20 20 10.8333333333333,20 20 10,10 20 10))"
        self.assertEqual(corr, result1[1].geom.ExportToWkt())
        corr = "POLYGON ((20 20 10,20 20 10.8333333333333,20 15 15,20 15 15,20 10 10.8333333333333,20 10 10,20 20 10))"
        self.assertEqual(corr, result1[2].geom.ExportToWkt())
        corr = "POLYGON ((20 10 10,20 10 10.8333333333333,10 10 10.8333333333333,10 10 10,20 10 10))"
        self.assertEqual(corr, result1[3].geom.ExportToWkt())
        self.assertEqual([], result2)


class TestCalcRoofWalls(unittest.TestCase):

    def test_1(self):
        lod2Conv = LoD2Converter(Converter(), ifc1, "Test123", trans1, False)
        result1, result2 = lod2Conv.calcRoofWalls([roof1, roof2])
        self.assertEqual(0, len(result1))
        self.assertEqual(2, len(result2))
        self.assertEqual(roof1.geom.ExportToWkt(), result2[0].geom.ExportToWkt())
        self.assertEqual(roof2.geom.ExportToWkt(), result2[1].geom.ExportToWkt())


class TestCalcRoofs(unittest.TestCase):

    def test_1(self):
        lod2Conv = LoD2Converter(Converter(), ifc1, "Test123", trans1, False)
        result = lod2Conv.calcRoofs([roof1, roof2], base)
        self.assertEqual(2, len(result))
        corr = "POLYGON ((20 15 15,10 15 15,10 10 10.8333333333333,20 10 10.8333333333333,20 15 15))"
        self.assertEqual(corr, result[0].geom.ExportToWkt())
        corr = "POLYGON ((10 15 15,20 15 15,20 20 10.8333333333333,10 20 10.8333333333333,10 15 15))"
        self.assertEqual(corr, result[1].geom.ExportToWkt())


class TestCheckRoofWalls(unittest.TestCase):

    def test_1(self):
        lod2Conv = LoD2Converter(Converter(), ifc1, "Test123", trans1, False)
        result = lod2Conv.checkRoofWalls([wall1, wall2, wall3, wall4], [roof1, roof2])
        self.assertEqual(4, len(result))
        self.assertEqual(wall1.geom.ExportToWkt(), result[0].geom.ExportToWkt())
        self.assertEqual(wall2.geom.ExportToWkt(), result[1].geom.ExportToWkt())
        self.assertEqual(wall3.geom.ExportToWkt(), result[2].geom.ExportToWkt())
        self.assertEqual(wall4.geom.ExportToWkt(), result[3].geom.ExportToWkt())


class TestSetElement(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        lod2Conv = LoD2Converter(Converter(), ifc1, "Test123", trans1, False)
        result1, result2 = lod2Conv.setElement(root, base.geom, "GroundSurface", base.name)
        self.assertEqual(612, len(etree.tostring(root)))
        self.assertEqual(42, len(result1))
        self.assertEqual(40, len(result2))

    def test_2(self):
        root = etree.Element("root")
        lod2Conv = LoD2Converter(Converter(), ifc2, "Test123", trans2, False)
        result1, result2 = lod2Conv.setElement(root, roof1.geom, "RoofSurface", roof1.name)
        self.assertEqual(602, len(etree.tostring(root)))
        self.assertEqual(42, len(result1))
        self.assertEqual(40, len(result2))

    def test_3(self):
        root = etree.Element("root")
        lod2Conv = LoD2Converter(Converter(), ifc3, "Test123", trans3, False)
        result1, result2 = lod2Conv.setElement(root, wall1.geom, "WallSurface", wall1.name)
        self.assertEqual(645, len(etree.tostring(root)))
        self.assertEqual(42, len(result1))
        self.assertEqual(40, len(result2))


if __name__ == '__main__':
    unittest.main()
