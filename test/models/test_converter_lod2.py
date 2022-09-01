# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)

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
from mock_model import Model
from mock_converter import Converter
sys.path.insert(0, '..')
from models.converter_lod2 import LoD2Converter
from models.transformer import Transformer
from models.utilitiesIfc import UtilitiesIfc

#####

LOGGER = logging.getLogger('QGIS')

# IFC-Elemente
ifc1 = ifcopenshell.open(r"data/IFC_test.ifc")
trans1 = Transformer(ifc1)
ifcBldg1 = ifc1.by_type("IfcBuilding")[0]

ifc2 = ifcopenshell.open(r"data/IFC_test3.ifc")
trans2 = Transformer(ifc2)
ifcBldg2 = ifc2.by_type("IfcBuilding")[0]

ifc3 = ifcopenshell.open(r"data/IFC_test4.ifc")
trans3 = Transformer(ifc3)
ifcBldg3 = ifc3.by_type("IfcBuilding")[0]

# Geometrien
base = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 20 10, 20 20 10, 20 10 10, 10 10 10))")
roof1 = ogr.CreateGeometryFromWkt("Polygon((9 9 10, 9 15 15, 21 15 15, 21 9 10, 9 9 10))")
roof2 = ogr.CreateGeometryFromWkt("Polygon((9 15 15, 9 21 10, 21 21 10, 21 15 15, 9 15 15))")
wall1 = ogr.CreateGeometryFromWkt("Polygon((10 10 10,10 10 10.8333333333333,10 15 15,10 20 10.8333333333333," +
                                  "10 20 10,10 10 10))")
wall2 = ogr.CreateGeometryFromWkt("Polygon((10 20 10,10 20 10.8333333333333,20 20 10.8333333333333,20 20 10,10 20 10))")
wall3 = ogr.CreateGeometryFromWkt("Polygon((20 20 10,20 20 10.8333333333333,20 15 15,20 10 10.8333333333333," +
                                  "20 10 10,20 20 10))")
wall4 = ogr.CreateGeometryFromWkt("Polygon((20 10 10,20 10 10.8333333333333,10 10 10.8333333333333,10 10 10,20 10 10))")

#####


class TestConstructor(unittest.TestCase):

    def test_1(self):
        model = Model()
        conv = Converter()
        result = LoD2Converter(model, conv, ifc1, "Test123", trans1, False)
        self.assertEqual(model, result.parent)
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
        model = Model()
        conv = Converter()
        result = LoD2Converter(model, conv, ifc2, "TestABC", trans2, True)
        self.assertEqual(model, result.parent)
        self.assertEqual(conv, result.task)
        self.assertEqual(ifc2, result.ifc)
        self.assertEqual("TestABC", result.name)
        self.assertEqual(trans2, result.trans)
        self.assertTrue(result.eade)
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.geom)))
        self.assertEqual("<class 'osgeo.ogr.Geometry'>", str(type(result.bldgGeom)))
        self.assertEqual(5, result.progress)
        self.assertEqual(1, result.bldgCount)


class TestConvert(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        lod2Conv = LoD2Converter(Model(), Converter(), ifc1, "Test123", trans1, True)
        result = lod2Conv.convert(root)
        corr = 24347
        self.assertEqual(corr, len(etree.tostring(result)))


class TestConvertBldgBound(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        lod2Conv = LoD2Converter(Model(), Converter(), ifc1, "Test123", trans1, True)
        result1, result2, result3 = lod2Conv.convertBldgBound(ifcBldg1, root, 10)
        corr = 5469
        self.assertEqual(corr, len(etree.tostring(root)))
        corr = 7
        self.assertEqual(corr, len(result1))
        corr = "POLYGON ((458870.063285681 5438773.62904949 110,458862.40284125 5438780.05692559 110," + \
               "458870.116292566 5438789.24945891 110,458877.776736998 5438782.82158281 110,458870.063285681 " + \
               "5438773.62904949 110))"
        self.assertEqual(corr, result2.ExportToWkt())
        corr = 7
        self.assertEqual(corr, len(result3))
        corr = "#34509=IfcSlab('1pPHnf7cXCpPsNEnQf8_6B',#12,'Bodenplatte',$,$,#34464,#34505," + \
               "'E4D9CD4B-CA43-4735-94-BD-1FD4376BD455',.BASESLAB.)"
        self.assertEqual(corr, str(result3[0][1]))


class TestExtractRoofs(unittest.TestCase):

    def test_1(self):
        lod2Conv = LoD2Converter(Model(), Converter(), ifc1, "Test123", trans1, False)
        ifcRoofs = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[], type="ROOF")
        result = lod2Conv.extractRoofs(ifcRoofs)
        corr = 2
        self.assertEqual(corr, len(result))
        corr = "POLYGON ((458861.698425224 5438779.99529717 113.14226,458870.05466415 5438789.95387493 113.14226," + \
               "458874.267908587 5438786.41854308 116.31769,458865.911669661 5438776.45996532 116.31769," + \
               "458861.698425224 5438779.99529717 113.14226))"
        self.assertEqual(corr, result[0][1].ExportToWkt())
        corr = ifcRoofs[0]
        self.assertEqual(corr, result[0][0])

    def test_2(self):
        lod2Conv = LoD2Converter(Model(), Converter(), ifc2, "Test123", trans2, False)
        ifcRoofs = UtilitiesIfc.findElement(ifc2, ifcBldg2, "IfcSlab", result=[], type="ROOF")
        result = lod2Conv.extractRoofs(ifcRoofs)
        corr = 21
        self.assertEqual(corr, len(result))
        corr = "POLYGON ((479337.600506348 5444182.54302925 10.09998,479356.600506348 5444182.54302925 10.09998," + \
               "479356.600506348 5444180.54352925 10.71118,479337.600506348 5444180.54352925 10.71118," + \
               "479337.600506348 5444182.54302925 10.09998))"
        self.assertEqual(corr, result[0][1].ExportToWkt())
        corr = ifcRoofs[0]
        self.assertEqual(corr, result[0][0])

    def test_3(self):
        lod2Conv = LoD2Converter(Model(), Converter(), ifc3, "Test123", trans3, False)
        ifcRoofs = UtilitiesIfc.findElement(ifc3, ifcBldg3, "IfcSlab", result=[], type="ROOF")
        result = lod2Conv.extractRoofs(ifcRoofs)
        corr = 20
        self.assertEqual(corr, len(result))
        corr = "POLYGON ((455479.084421465 5431328.70714145 112.41355,455482.161518287 5431330.66746833 112.41355," + \
               "455483.082417578 5431329.22194599 112.77785,455480.005320756 5431327.26161912 112.77785," + \
               "455479.084421465 5431328.70714145 112.41355))"
        self.assertEqual(corr, result[0][1].ExportToWkt())
        corr = ifcRoofs[0]
        self.assertEqual(corr, result[0][0])


class TestCalcWalls(unittest.TestCase):

    def test_1(self):
        lod2Conv = LoD2Converter(Model(), Converter(), ifc1, "Test123", trans1, False)
        result1, result2 = lod2Conv.calcWalls([None, base], [[None, roof1], [None, roof2]], 10)
        corr = 4
        self.assertEqual(corr, len(result1))
        corr = "POLYGON ((10 10 10,10 10 10.8333333333333,10 15 15,10 15 15,10 20 10.8333333333333,10 20 10,10 10 10))"
        self.assertEqual(corr, result1[0].ExportToWkt())
        corr = "POLYGON ((10 20 10,10 20 10.8333333333333,20 20 10.8333333333333,20 20 10,10 20 10))"
        self.assertEqual(corr, result1[1].ExportToWkt())
        corr = "POLYGON ((20 20 10,20 20 10.8333333333333,20 15 15,20 15 15,20 10 10.8333333333333,20 10 10,20 20 10))"
        self.assertEqual(corr, result1[2].ExportToWkt())
        corr = "POLYGON ((20 10 10,20 10 10.8333333333333,10 10 10.8333333333333,10 10 10,20 10 10))"
        self.assertEqual(corr, result1[3].ExportToWkt())
        corr = []
        self.assertEqual(corr, result2)


class TestCalcRoofWalls(unittest.TestCase):

    def test_1(self):
        lod2Conv = LoD2Converter(Model(), Converter(), ifc1, "Test123", trans1, False)
        result1, result2 = lod2Conv.calcRoofWalls([[None, roof1], [None, roof2]])
        corr = 0
        self.assertEqual(corr, len(result1))
        corr = 2
        self.assertEqual(corr, len(result2))
        corr = roof1.ExportToWkt()
        self.assertEqual(corr, result2[0][1].ExportToWkt())
        corr = roof2.ExportToWkt()
        self.assertEqual(corr, result2[1][1].ExportToWkt())


class TestCalcRoofs(unittest.TestCase):

    def test_1(self):
        lod2Conv = LoD2Converter(Model(), Converter(), ifc1, "Test123", trans1, False)
        result = lod2Conv.calcRoofs([[None, roof1], [None, roof2]], [None, base])
        corr = 2
        self.assertEqual(corr, len(result))
        corr = "POLYGON ((20 15 15,10 15 15,10 10 10.8333333333333,20 10 10.8333333333333,20 15 15))"
        self.assertEqual(corr, result[0][1].ExportToWkt())
        corr = "POLYGON ((10 15 15,20 15 15,20 20 10.8333333333333,10 20 10.8333333333333,10 15 15))"
        self.assertEqual(corr, result[1][1].ExportToWkt())


class TestCheckRoofWallss(unittest.TestCase):

    def test_1(self):
        lod2Conv = LoD2Converter(Model(), Converter(), ifc1, "Test123", trans1, False)
        result = lod2Conv.checkRoofWalls([wall1, wall2, wall3, wall4], [[None, roof1], [None, roof2]])
        corr = 4
        self.assertEqual(corr, len(result))
        corr = wall1.ExportToWkt()
        self.assertEqual(corr, result[0].ExportToWkt())
        corr = wall2.ExportToWkt()
        self.assertEqual(corr, result[1].ExportToWkt())
        corr = wall3.ExportToWkt()
        self.assertEqual(corr, result[2].ExportToWkt())
        corr = wall4.ExportToWkt()
        self.assertEqual(corr, result[3].ExportToWkt())


class TestSetElement(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        lod2Conv = LoD2Converter(Model(), Converter(), ifc1, "Test123", trans1, False)
        result1, result2 = lod2Conv.setElement(root, base, "GroundSurface", 2)
        corr = 583
        self.assertEqual(corr, len(etree.tostring(root)))
        corr = 42
        self.assertEqual(corr, len(result1))
        corr = 40
        self.assertEqual(corr, len(result2))

    def test_2(self):
        root = etree.Element("root")
        lod2Conv = LoD2Converter(Model(), Converter(), ifc2, "Test123", trans2, False)
        result1, result2 = lod2Conv.setElement(root, roof1, "RoofSurface", 2)
        corr = 573
        self.assertEqual(corr, len(etree.tostring(root)))
        corr = 42
        self.assertEqual(corr, len(result1))
        corr = 40
        self.assertEqual(corr, len(result2))

    def test_3(self):
        root = etree.Element("root")
        lod2Conv = LoD2Converter(Model(), Converter(), ifc3, "Test123", trans3, False)
        result1, result2 = lod2Conv.setElement(root, wall1, "WallSurface", 2)
        corr = 616
        self.assertEqual(corr, len(etree.tostring(root)))
        corr = 42
        self.assertEqual(corr, len(result1))
        corr = 40
        self.assertEqual(corr, len(result2))


if __name__ == '__main__':
    unittest.main()
