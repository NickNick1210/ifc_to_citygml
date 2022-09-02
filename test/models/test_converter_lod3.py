# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)

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
from test.mock_model import Model
from models.converter_lod3 import LoD3Converter
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

ifc4 = ifcopenshell.open(r"data/IFC_test2.ifc")
trans4 = Transformer(ifc4)
ifcBldg4 = ifc4.by_type("IfcBuilding")[0]

# Geometrien
baseGeom = ogr.CreateGeometryFromWkt("Polygon((0 0 0, -20 0 0, -20 -20 0, 0 -20 0, 0 0 0))")

wallGeom = ogr.CreateGeometryFromWkt("Polygon((0 0 0, 20 0 0, 20 0 10, 0 0 10, 0 0 0))")
wallGeom2 = ogr.CreateGeometryFromWkt("Polygon((0 30 10, 20 30 10, 20 30 20, 0 30 20, 0 30 10))")
ifcWall = UtilitiesIfc.findElement(ifc4, ifcBldg4, "IfcWall", result=[])[5]
wall = [[wallGeom], "Wand-Ext-Test123", [], ifcWall]
wall2 = [[wallGeom2], "Wand-Ext-Test123", [], ifcWall]

doorGeom = [[8, 0, 0], [8, 0, 2], [10, 0, 2], [10, 0, 0]]
ifcDoor = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcDoor", result=[])[3]
door = [doorGeom, "Tür-Ext-TestABC", 'ifcDoor', ifcDoor]
doorGeom2 = ogr.CreateGeometryFromWkt("Polygon((8 0 0, 8 0 2, 10 0 2, 10 0 0, 8 0 0))")
door2 = [doorGeom2, "Tür-Ext-TestABC", 'ifcDoor', ifcDoor]

#####


class TestConstructor(unittest.TestCase):

    def test_1(self):
        model = Model()
        conv = Converter()
        result = LoD3Converter(model, conv, ifc1, "Test123", trans1, False)
        self.assertEqual(model, result.parent)
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
        model = Model()
        conv = Converter()
        result = LoD3Converter(model, conv, ifc2, "TestABC", trans2, True)
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


class TestCalcBases(unittest.TestCase):

    def test_1(self):
        lod3Conv = LoD3Converter(Model(), Converter(), ifc1, "Test123", trans1, False)
        result1, result2, result3 = lod3Conv.calcBases(ifcBldg1)
        self.assertEqual(1, len(result1))
        corr = "POLYGON ((458870.063285681 5438773.62904949 109.8,458862.40284125 5438780.05692559 109.8," + \
               "458870.116292566 5438789.24945891 109.8,458877.776736998 5438782.82158281 109.8,458870.063285681 " + \
               "5438773.62904949 109.8))"
        self.assertEqual(corr, result1[0][0][0].ExportToWkt())
        self.assertEqual("Bodenplatte", result1[0][1])
        self.assertEqual([], result1[0][2])
        corr = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[], type="BASESLAB")[0]
        self.assertEqual(str(corr), str(result1[0][3]))
        self.assertEqual(6, len(result2[0]))
        corr = "POLYGON ((458862.40284125 5438780.05692559 110,458862.40284125 5438780.05692559 109.8," + \
               "458870.063285681 5438773.62904949 109.8,458870.063285681 5438773.62904949 110,458862.40284125 " + \
               "5438780.05692559 110))"
        self.assertEqual(corr, result2[0][0].ExportToWkt())
        corr = "POLYGON ((458870.063285681 5438773.62904949 109.8,458862.40284125 5438780.05692559 109.8," + \
               "458870.116292566 5438789.24945891 109.8,458877.776736998 5438782.82158281 109.8,458870.063285681 " + \
               "5438773.62904949 109.8))"
        self.assertEqual(corr, result3[0][0][0].ExportToWkt())

    def test_2(self):
        lod3Conv = LoD3Converter(Model(), Converter(), ifc2, "Test123", trans2, False)
        result1, result2, result3 = lod3Conv.calcBases(ifcBldg2)
        self.assertEqual(3, len(result1))
        corr = "POLYGON ((479338.600506348 5444171.43024925 -3.3,479338.600506348 5444183.43024925 -3.3," + \
               "479356.600506348 5444183.43024925 -3.3,479356.600506348 5444185.43024925 -3.3,479362.600506348 " + \
               "5444185.43024925 -3.3,479362.600506348 5444183.43024925 -3.3,479380.600506348 5444183.43024925 " + \
               "-3.3,479380.600506348 5444171.43024925 -3.3,479338.600506348 5444171.43024925 -3.3))"
        self.assertEqual(corr, result1[0][0][0].ExportToWkt())
        self.assertEqual("Decke-002", result1[0][1])
        self.assertEqual([], result1[0][2])
        corr = UtilitiesIfc.findElement(ifc2, ifcBldg2, "IfcSlab", result=[], type="FLOOR")[0]
        self.assertEqual(str(corr), str(result1[0][3]))
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
        self.assertEqual(corr, result3[0][0][0].ExportToWkt())

    def test_3(self):
        lod3Conv = LoD3Converter(Model(), Converter(), ifc3, "Test123", trans2, False)
        result1, result2, result3 = lod3Conv.calcBases(ifcBldg3)
        self.assertEqual(40, len(result1))
        corr = "POLYGON ((479338.600506348 5444169.43024925 -3.06,479338.600506348 5444176.34024925 -3.06," + \
               "479346.075506348 5444176.34024925 -3.06,479346.075506348 5444169.43024925 -3.06,479338.600506348 " + \
               "5444169.43024925 -3.06))"
        self.assertEqual(corr, result1[0][0][0].ExportToWkt())
        self.assertEqual("Keller-Boden-01", result1[0][1])
        self.assertEqual([], result1[0][2])
        corr = UtilitiesIfc.findElement(ifc3, ifcBldg3, "IfcSlab", result=[], type="FLOOR")[0]
        self.assertEqual(str(corr), str(result1[0][3]))
        self.assertEqual(6, len(result2[0]))
        corr = "POLYGON ((479346.075506348 5444169.43024925 -2.81,479346.075506348 5444169.43024925 -3.06," + \
               "479346.075506348 5444176.34024925 -3.06,479346.075506348 5444176.34024925 -2.81,479346.075506348 " + \
               "5444169.43024925 -2.81))"
        self.assertEqual(corr, result2[0][0].ExportToWkt())
        self.assertEqual(100, len(result3))
        corr = "POLYGON ((479338.600506348 5444169.43024925 -3.06,479338.600506348 5444176.34024925 -3.06," + \
               "479346.075506348 5444176.34024925 -3.06,479346.075506348 5444169.43024925 -3.06,479338.600506348 " + \
               "5444169.43024925 -3.06))"
        self.assertEqual(corr, result3[0][0][0].ExportToWkt())


class TestCalcRoofs(unittest.TestCase):

    def test_1(self):
        lod3Conv = LoD3Converter(Model(), Converter(), ifc1, "Test123", trans1, False)
        result1, result2 = lod3Conv.calcRoofs(ifcBldg1)
        self.assertEqual(2, len(result1))
        corr = "POLYGON ((458870.05466415 5438789.95387493 113.14226,458861.698425224 5438779.99529717 113.14226," + \
               "458865.911669661 5438776.45996532 116.31769,458874.267908587 5438786.41854308 116.31769," + \
               "458870.05466415 5438789.95387493 113.14226))"
        self.assertEqual(corr, result1[0][0][0].ExportToWkt())
        self.assertEqual("Dach-1", result1[0][1])
        self.assertEqual([], result1[0][2])
        corr = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcSlab", result=[], type="ROOF")[0]
        self.assertEqual(str(corr), str(result1[0][3]))
        self.assertEqual(6, len(result2[0]))
        corr = "POLYGON ((458865.911669661 5438776.45996532 116.31769,458865.911669661 5438776.45996532 116.08675," + \
               "458874.267908587 5438786.41854308 116.08675,458874.267908587 5438786.41854308 116.31769," + \
               "458865.911669661 5438776.45996532 116.31769))"
        self.assertEqual(corr, result2[0][0].ExportToWkt())

    def test_2(self):
        lod3Conv = LoD3Converter(Model(), Converter(), ifc2, "Test123", trans2, False)
        result1, result2 = lod3Conv.calcRoofs(ifcBldg2)
        self.assertEqual(21, len(result1))
        corr = "POLYGON ((479356.600506348 5444182.54302925 10.09998,479337.600506348 5444182.54302925 10.09998," + \
               "479337.600506348 5444180.54352925 10.71118,479356.600506348 5444180.54352925 10.71118," + \
               "479356.600506348 5444182.54302925 10.09998))"
        self.assertEqual(corr, result1[0][0][0].ExportToWkt())
        self.assertEqual("Dach-001", result1[0][1])
        self.assertEqual([], result1[0][2])
        corr = UtilitiesIfc.findElement(ifc2, ifcBldg2, "IfcSlab", result=[], type="ROOF")[0]
        self.assertEqual(str(corr), str(result1[0][3]))
        self.assertEqual(6, len(result2[0]))
        corr = "POLYGON ((479356.600506348 5444182.54302925 10.09998,479337.600506348 5444182.54302925 10.09998," + \
               "479337.600506348 5444180.54352925 10.71118,479356.600506348 5444180.54352925 10.71118," + \
               "479356.600506348 5444182.54302925 10.09998))"
        self.assertEqual(corr, result2[0][0].ExportToWkt())

    def test_3(self):
        lod3Conv = LoD3Converter(Model(), Converter(), ifc3, "Test123", trans3, False)
        result1, result2 = lod3Conv.calcRoofs(ifcBldg3)
        self.assertEqual(20, len(result1))
        corr = "POLYGON ((455480.005320756 5431327.26161912 112.77785,455483.082417578 5431329.22194599 112.77785," + \
               "455482.161518287 5431330.66746833 112.41355,455479.084421465 5431328.70714145 112.41355," + \
               "455480.005320756 5431327.26161912 112.77785))"
        self.assertEqual(corr, result1[0][0][0].ExportToWkt())
        self.assertEqual("EG-Vordach-01", result1[0][1])
        self.assertEqual([], result1[0][2])
        corr = UtilitiesIfc.findElement(ifc3, ifcBldg3, "IfcSlab", result=[], type="ROOF")[0]
        self.assertEqual(str(corr), str(result1[0][3]))
        self.assertEqual(6, len(result2[0]))
        corr = "POLYGON ((455482.161518287 5431330.66746833 112.41355,455482.161518287 5431330.66746833 112.31355," + \
               "455479.084421465 5431328.70714145 112.31355,455479.084421465 5431328.70714145 112.41355," + \
               "455482.161518287 5431330.66746833 112.41355))"
        self.assertEqual(corr, result2[0][0].ExportToWkt())


class TestCalcWalls(unittest.TestCase):

    def test_1(self):
        lod3Conv = LoD3Converter(Model(), Converter(), ifc4, "Test123", trans4, False)
        result = lod3Conv.calcWalls(ifcBldg4)
        self.assertEqual(4, len(result))
        self.assertEqual(18, len(result[0][0]))
        self.assertEqual("Wand-Ext-ERDG-1", result[0][1])
        self.assertEqual([], result[0][2])
        corr = UtilitiesIfc.findElement(ifc4, ifcBldg4, "IfcWall", result=[])[5]
        self.assertEqual(corr, result[0][3])
        self.assertEqual(18, len(result[1][0]))
        self.assertEqual("Wand-Ext-ERDG-4", result[1][1])
        self.assertEqual([], result[1][2])
        corr = UtilitiesIfc.findElement(ifc4, ifcBldg4, "IfcWall", result=[])[6]
        self.assertEqual(corr, result[1][3])


class TestCalcOpenings(unittest.TestCase):

    def test_1(self):
        lod3Conv = LoD3Converter(Model(), Converter(), ifc1, "Test123", trans1, False)
        result = lod3Conv.calcOpenings(ifcBldg1, "ifcDoor")
        self.assertEqual(2, len(result))
        self.assertEqual(44, len(result[0][0]))
        self.assertEqual("Haustuer", result[0][1])
        self.assertEqual("ifcDoor", result[0][2])
        corr = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcDoor", result=[])[3]
        self.assertEqual(corr, result[0][3])
        self.assertEqual(28, len(result[1][0]))
        self.assertEqual("Terrassentuer", result[1][1])
        self.assertEqual("ifcDoor", result[1][2])
        corr = UtilitiesIfc.findElement(ifc1, ifcBldg1, "IfcDoor", result=[])[4]
        self.assertEqual(corr, result[1][3])

    def test_2(self):
        lod3Conv = LoD3Converter(Model(), Converter(), ifc1, "Test123", trans1, False)
        result = lod3Conv.calcOpenings(ifcBldg1, "ifcWindow")
        self.assertEqual(11, len(result))
        self.assertEqual(12, len(result[0][0]))
        self.assertEqual("EG-Fenster-6", result[0][1])
        self.assertEqual("ifcWindow", result[0][2])
        corr = UtilitiesIfc.findElement(ifc1, ifcBldg1, "ifcWindow", result=[])[0]
        self.assertEqual(corr, result[0][3])
        self.assertEqual(12, len(result[1][0]))
        self.assertEqual("EG-Fenster-7", result[1][1])
        self.assertEqual("ifcWindow", result[1][2])
        corr = UtilitiesIfc.findElement(ifc1, ifcBldg1, "ifcWindow", result=[])[1]
        self.assertEqual(corr, result[1][3])

    def test_3(self):
        lod3Conv = LoD3Converter(Model(), Converter(), ifc2, "TestABC", trans2, False)
        result = lod3Conv.calcOpenings(ifcBldg2, "ifcDoor")
        self.assertEqual(1, len(result))
        self.assertEqual(70, len(result[0][0]))
        self.assertEqual("Tür-019", result[0][1])
        self.assertEqual("ifcDoor", result[0][2])
        corr = UtilitiesIfc.findElement(ifc2, ifcBldg2, "IfcDoor", result=[])[16]
        self.assertEqual(corr, result[0][3])


class TestAssignOpenings(unittest.TestCase):

    def test_1(self):
        lod3Conv = LoD3Converter(Model(), Converter(), ifc1, "Test123", trans1, False)
        result = lod3Conv.assignOpenings([door], [wall, wall2])
        self.assertEqual(2, len(result))
        self.assertEqual(1, len(result[0][2]))
        self.assertEqual(door, result[0][2][0])
        self.assertEqual(0, len(result[1][2]))


class TestSetElementGroup(unittest.TestCase):

    def test_1(self):
        root = etree.Element("root")
        lod3Conv = LoD3Converter(Model(), Converter(), ifc1, "Test123", trans1, False)
        result1, result2, result3 = lod3Conv.setElementGroup(root, [baseGeom], "GroundSurface", 3, "Bodenplatte", [])
        self.assertEqual(744, len(etree.tostring(root)))
        self.assertEqual(42, len(result1[0]))
        self.assertEqual(40, len(result2))
        self.assertEqual(0, len(result3))

    def test_2(self):
        root = etree.Element("root")
        lod3Conv = LoD3Converter(Model(), Converter(), ifc1, "Test123", trans1, False)
        result1, result2, result3 = lod3Conv.setElementGroup(root, [wallGeom], "WallSurface", 3, "Wall-Ext-12", [door2])
        self.assertEqual(1281, len(etree.tostring(root)))
        self.assertEqual(42, len(result1[0]))
        self.assertEqual(40, len(result2))
        self.assertEqual(1, len(result3))

    def test_3(self):
        root = etree.Element("root")
        lod3Conv = LoD3Converter(Model(), Converter(), ifc1, "Test123", trans1, False)
        result1, result2, result3 = lod3Conv.setElementGroup(root, [wallGeom2], "WallSurface", 3, "Wall-Ext-23", [])
        self.assertEqual(744, len(etree.tostring(root)))
        self.assertEqual(42, len(result1[0]))
        self.assertEqual(40, len(result2))
        self.assertEqual(0, len(result3))


# convert, convertBldgBound, adjustWallOpenings und adjustWallSize sind aufgrund der langen, mehrminütigen Rechenzeit
#   sowie des komplexen In- und Outpus nicht vernünftig testbar.

if __name__ == '__main__':
    unittest.main()
