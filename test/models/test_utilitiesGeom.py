# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)

Unit-Test für die Modelklasse UtilitiesGeom
 ***************************************************************************/
"""

# Standard-Bibliotheken
import unittest
import logging
import sys

# XML-Bibliotheken
from lxml import etree

# Geo-Bibliotheken
from osgeo import ogr
from sympy import Plane, Point3D

# Plugin
sys.path.insert(0, '..')
from models.utilitiesGeom import UtilitiesGeom

LOGGER = logging.getLogger('QGIS')

# Geometrien
geom1 = ogr.CreateGeometryFromWkt("Point(10 10 10)")
geom2 = ogr.CreateGeometryFromWkt("LineString (10 10 10, 20 20 20, 30 40 50)")
geom3 = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 20 10, 20 20 10, 20 15 10, 10 10 10))")
geom4 = ogr.CreateGeometryFromWkt("Polygon((0 0, 0 20, 20 20, 20 0, 0 0),(5 5, 5 15, 15 15, 15 5, 5 5))")
geom5 = ogr.CreateGeometryFromWkt("MultiPolygon(((10 10, 10 20, 20 20, 20 15, 10 10)),((60 60, 70 70, 80 60, 60 60 )))")
geom6 = ogr.CreateGeometryFromWkt(
    "MultiPolygon(((0 0, 0 20, 20 20, 20 0, 0 0),(5 5, 5 15, 15 15, 15 5, 5 5)),((30 30, 30 40, 40 40, 40 30, 30 30)))")

pol1 = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 20 15, 20 20 20, 20 10 15, 10 10 10))")
pol2 = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 10 20, 20 10 20, 20 10 10, 10 10 10))")

line1 = [[10, 10, 10], [20, 20, 20], [30, 40, 50]]
line2 = [[-10, -10, -10], [-20, -20, -20], [-30, -40, -50]]
line3 = [[11, 11, 11], [21, 21, 21], [31, 41, 51]]
line4 = [[0, 0, 0], [25, 25, 25], [40, 50, 60]]

ring = geom3.GetGeometryRef(0)
pt1 = ring.GetPoint(0)
pt2 = ring.GetPoint(1)
pt3 = ring.GetPoint(2)
pt4 = ring.GetPoint(3)


class TestGeomToGML(unittest.TestCase):

    def test_1(self):
        result = UtilitiesGeom.geomToGml(geom1)
        result = etree.tostring(result)
        corr = b'<gml:Point xmlns:gml="http://www.opengis.net/gml"><gml:coordinates>10,10,10</gml:coordinates>' + \
               b'</gml:Point>'
        self.assertEqual(corr, result)

    def test_2(self):
        result = UtilitiesGeom.geomToGml(geom2)
        result = etree.tostring(result)
        corr = b'<gml:LineString xmlns:gml="http://www.opengis.net/gml"><gml:coordinates>10,10,10 20,20,20 30,40,50' + \
               b'</gml:coordinates></gml:LineString>'
        self.assertEqual(corr, result)

    def test_3(self):
        result = UtilitiesGeom.geomToGml(geom3)
        result = etree.tostring(result)
        corr = b'<gml:Polygon xmlns:gml="http://www.opengis.net/gml"><gml:outerBoundaryIs><gml:LinearRing>' + \
               b'<gml:coordinates>10,10,10 10,20,10 20,20,10 20,15,10 10,10,10</gml:coordinates></gml:LinearRing>' + \
               b'</gml:outerBoundaryIs></gml:Polygon>'
        self.assertEqual(corr, result)

    def test_4(self):
        result = UtilitiesGeom.geomToGml(geom4)
        result = etree.tostring(result)
        corr = b'<gml:Polygon xmlns:gml="http://www.opengis.net/gml"><gml:outerBoundaryIs><gml:LinearRing>' + \
               b'<gml:coordinates>0,0 0,20 20,20 20,0 0,0</gml:coordinates></gml:LinearRing></gml:outerBoundaryIs>' + \
               b'<gml:innerBoundaryIs><gml:LinearRing><gml:coordinates>5,5 5,15 15,15 15,5 5,5</gml:coordinates>' + \
               b'</gml:LinearRing></gml:innerBoundaryIs></gml:Polygon>'
        self.assertEqual(corr, result)

    def test_5(self):
        result = UtilitiesGeom.geomToGml(geom5)
        result = etree.tostring(result)
        corr = b'<gml:MultiPolygon xmlns:gml="http://www.opengis.net/gml"><gml:polygonMember><gml:Polygon>' + \
               b'<gml:outerBoundaryIs><gml:LinearRing><gml:coordinates>10,10 10,20 20,20 20,15 10,10' + \
               b'</gml:coordinates></gml:LinearRing></gml:outerBoundaryIs></gml:Polygon></gml:polygonMember>' + \
               b'<gml:polygonMember><gml:Polygon><gml:outerBoundaryIs><gml:LinearRing><gml:coordinates>' + \
               b'60,60 70,70 80,60 60,60</gml:coordinates></gml:LinearRing></gml:outerBoundaryIs></gml:Polygon>' + \
               b'</gml:polygonMember></gml:MultiPolygon>'
        self.assertEqual(corr, result)

    def test_6(self):
        result = UtilitiesGeom.geomToGml(geom6)
        result = etree.tostring(result)
        corr = b'<gml:MultiPolygon xmlns:gml="http://www.opengis.net/gml"><gml:polygonMember><gml:Polygon>' + \
               b'<gml:outerBoundaryIs><gml:LinearRing><gml:coordinates>0,0 0,20 20,20 20,0 0,0</gml:coordinates>' + \
               b'</gml:LinearRing></gml:outerBoundaryIs><gml:innerBoundaryIs><gml:LinearRing><gml:coordinates>' + \
               b'5,5 5,15 15,15 15,5 5,5</gml:coordinates></gml:LinearRing></gml:innerBoundaryIs></gml:Polygon>' + \
               b'</gml:polygonMember><gml:polygonMember><gml:Polygon><gml:outerBoundaryIs><gml:LinearRing>' + \
               b'<gml:coordinates>30,30 30,40 40,40 40,30 30,30</gml:coordinates></gml:LinearRing>' + \
               b'</gml:outerBoundaryIs></gml:Polygon></gml:polygonMember></gml:MultiPolygon>'
        self.assertEqual(corr, result)


class TestSortPoints(unittest.TestCase):

    def test_1(self):
        result = UtilitiesGeom.sortPoints([pt4, pt2, pt3, pt1], pt1, pt4)
        corr = [(10, 10, 10), (10, 20, 10), (20, 15, 10), (20, 20, 10)]
        self.assertEqual(corr, result)

    def test_2(self):
        result = UtilitiesGeom.sortPoints([pt3, pt2, pt1, pt4], pt1, pt4)
        corr = [(10, 10, 10), (10, 20, 10), (20, 15, 10), (20, 20, 10)]
        self.assertEqual(corr, result)

    def test_3(self):
        result = UtilitiesGeom.sortPoints([pt4, pt2, pt3, pt1], pt4, pt1)
        corr = [(20, 20, 10), (20, 15, 10), (10, 20, 10), (10, 10, 10)]
        self.assertEqual(corr, result)

    def test_4(self):
        result = UtilitiesGeom.sortPoints([pt3, pt2, pt1, pt4], pt4, pt1)
        corr = [(20, 20, 10), (20, 15, 10), (10, 20, 10), (10, 10, 10)]
        self.assertEqual(corr, result)


class TestSortLines(unittest.TestCase):

    def test_1(self):
        result = UtilitiesGeom.sortLines([line1, line2, line3, line4], pt1, pt4)
        corr = [[[-10, -10, -10], [-20, -20, -20], [-30, -40, -50]], [[0, 0, 0], [25, 25, 25], [40, 50, 60]],
                [[10, 10, 10], [20, 20, 20], [30, 40, 50]], [[11, 11, 11], [21, 21, 21], [31, 41, 51]]]
        self.assertEqual(corr, result)

    def test_2(self):
        result = UtilitiesGeom.sortLines([line3, line2, line4, line1], pt1, pt4)
        corr = [[[-10, -10, -10], [-20, -20, -20], [-30, -40, -50]], [[0, 0, 0], [25, 25, 25], [40, 50, 60]],
                [[10, 10, 10], [20, 20, 20], [30, 40, 50]], [[11, 11, 11], [21, 21, 21], [31, 41, 51]]]
        self.assertEqual(corr, result)

    def test_3(self):
        result = UtilitiesGeom.sortLines([line1, line2, line3, line4], pt4, pt1)
        corr = [[[0, 0, 0], [25, 25, 25], [40, 50, 60]], [[11, 11, 11], [21, 21, 21], [31, 41, 51]],
                [[10, 10, 10], [20, 20, 20], [30, 40, 50]], [[-10, -10, -10], [-20, -20, -20], [-30, -40, -50]]]
        self.assertEqual(corr, result)

    def test_4(self):
        result = UtilitiesGeom.sortLines([line3, line2, line4, line1], pt4, pt1)
        corr = [[[0, 0, 0], [25, 25, 25], [40, 50, 60]], [[11, 11, 11], [21, 21, 21], [31, 41, 51]],
                [[10, 10, 10], [20, 20, 20], [30, 40, 50]], [[-10, -10, -10], [-20, -20, -20], [-30, -40, -50]]]
        self.assertEqual(corr, result)


class TestGetPlane(unittest.TestCase):

    def test_1(self):
        result = UtilitiesGeom.getPlane(pt1, pt2, pt3)
        corr = Plane(Point3D(pt1[0], pt1[1], pt1[2]), Point3D(pt2[0], pt2[1], pt2[2]), Point3D(pt3[0], pt3[1], pt3[2]))
        self.assertEqual(corr, result)

    def test_2(self):
        result = UtilitiesGeom.getPlane(pt2, pt3, pt4)
        corr = Plane(Point3D(pt2[0], pt2[1], pt2[2]), Point3D(pt3[0], pt3[1], pt3[2]), Point3D(pt4[0], pt4[1], pt4[2]))
        self.assertEqual(corr, result)

    def test_3(self):
        result = UtilitiesGeom.getPlane(pt4, pt2, pt1)
        corr = Plane(Point3D(pt4[0], pt4[1], pt4[2]), Point3D(pt2[0], pt2[1], pt2[2]), Point3D(pt1[0], pt1[1], pt1[2]))
        self.assertEqual(corr, result)

    def test_4(self):
        result = UtilitiesGeom.getPlane(pt3, pt4, pt1)
        corr = Plane(Point3D(pt3[0], pt3[1], pt3[2]), Point3D(pt4[0], pt4[1], pt4[2]), Point3D(pt1[0], pt1[1], pt1[2]))
        self.assertEqual(corr, result)


class TestCalcArea3D(unittest.TestCase):

    def test_1(self):
        result = UtilitiesGeom.calcArea3D([geom3])
        corr = 75
        self.assertEqual(corr, result)

    def test_2(self):
        result = UtilitiesGeom.calcArea3D([geom4])
        corr = 300
        self.assertEqual(corr, result)

    def test_3(self):
        result = UtilitiesGeom.calcArea3D([geom3, geom4])
        corr = 375
        self.assertEqual(corr, result)

    def test_4(self):
        result = UtilitiesGeom.calcArea3D([pol1])
        corr = 122.47448713915891
        self.assertEqual(corr, result)


class TestCalcInclination(unittest.TestCase):

    def test_1(self):
        result = UtilitiesGeom.calcInclination(geom3)
        corr = 3.141592653589793
        self.assertEqual(corr, result)

    def test_2(self):
        result = UtilitiesGeom.calcInclination(geom4)
        corr = 3.141592653589793
        self.assertEqual(corr, result)

    def test_3(self):
        result = UtilitiesGeom.calcInclination(pol1)
        corr = 2.5261129449194057
        self.assertEqual(corr, result)

    def test_4(self):
        result = UtilitiesGeom.calcInclination(pol2)
        corr = 1.5707963267948966
        self.assertEqual(corr, result)


class TestCalcAzimuth(unittest.TestCase):

    def test_1(self):
        result = UtilitiesGeom.calcAzimuth(geom3)
        corr = 0
        self.assertEqual(corr, result)

    def test_2(self):
        result = UtilitiesGeom.calcAzimuth(geom4)
        corr = 0
        self.assertEqual(corr, result)

    def test_3(self):
        result = UtilitiesGeom.calcAzimuth(pol1)
        corr = 45
        self.assertEqual(corr, result)

    def test_4(self):
        result = UtilitiesGeom.calcAzimuth(pol2)
        corr = 90
        self.assertEqual(corr, result)


simpl1 = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 20 10, 10.0001 20.0001 10, 20 20 10, 20 15 10, 10 10 10))")
simpl2 = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 10 20 10, 15 20.001 10, 20 20 10, 20 15 10, 10 10 10))")
simpl3 = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 15 15 10, 20 20 10, 20.001 20.001 10, 10 10 10))")
simpl4 = ogr.CreateGeometryFromWkt("LineString (10 10 10, 20 20 20, 30 30 30)")
simpl5 = ogr.CreateGeometryFromWkt("LineString (10 10 10, 20 20 20, 20.001 20.001 20.001, 30 20 25)")


class TestSimplify(unittest.TestCase):

    def test_1(self):
        result = UtilitiesGeom.simplify(simpl1, 0.001, 0.001)
        result = result.ExportToWkt()
        corr = "POLYGON ((10 10 10,10 20 10,20 20 10,20 15 10,10 10 10))"
        self.assertEqual(corr, result)

    def test_2(self):
        result = UtilitiesGeom.simplify(simpl1, 0.0001, 0.001)
        result = result.ExportToWkt()
        corr = "POLYGON ((10 10 10,10 20 10,10.0001 20.0001 10,20 20 10,20 15 10,10 10 10))"
        self.assertEqual(corr, result)

    def test_3(self):
        result = UtilitiesGeom.simplify(simpl2, 0.001, 0.001)
        result = result.ExportToWkt()
        corr = "POLYGON ((10 10 10,10 20 10,20 20 10,20 15 10,10 10 10))"
        self.assertEqual(corr, result)

    def test_4(self):
        result = UtilitiesGeom.simplify(simpl2, 0.001, 0.0001)
        result = result.ExportToWkt()
        corr = "POLYGON ((10 10 10,10 20 10,15.0 20.001 10,20 20 10,20 15 10,10 10 10))"
        self.assertEqual(corr, result)

    def test_5(self):
        result = UtilitiesGeom.simplify(simpl3, 0.001, 0.001)
        result = result.ExportToWkt()
        corr = "LINESTRING (10 10 10,0 0 0)"
        self.assertEqual(corr, result)

    def test_6(self):
        result = UtilitiesGeom.simplify(simpl4, 0.001, 0.001)
        result = result.ExportToWkt()
        corr = "LINESTRING (10 10 10,30 30 30)"
        self.assertEqual(corr, result)

    def test_7(self):
        result = UtilitiesGeom.simplify(simpl5, 0.001, 0.001)
        result = result.ExportToWkt()
        corr = "LINESTRING (10 10 10,20.001 20.001 20.001,30 20 25)"
        self.assertEqual(corr, result)

    def test_8(self):
        result = UtilitiesGeom.simplify([simpl1, simpl4], 0.001, 0.001)
        result = result[0].ExportToWkt() + ", " + result[1].ExportToWkt()
        corr = "POLYGON ((10 10 10,10 20 10,20 20 10,20 15 10,10 10 10)), LINESTRING (10 10 10,30 30 30)"
        self.assertEqual(corr, result)


union1 = ogr.CreateGeometryFromWkt("Polygon((10 10 10, 20 10 10, 20 20 15, 15 20 15, 10 20 15, 10 10 10))")
union2 = ogr.CreateGeometryFromWkt("Polygon((20 10 10, 30 10 10, 30 20 15, 20 20 15, 20 10 10))")
union3 = ogr.CreateGeometryFromWkt("Polygon((20 10 10, 30 10 10, 30 20 10, 20 20 10, 20 10 10))")
union4 = ogr.CreateGeometryFromWkt(
    "Polygon((15 20 15, 15 22.5 16.25, 15 25 17.5, 5 25 17.5, 5 20 15, 10 20 15, 15 20 15))")
union5 = ogr.CreateGeometryFromWkt("Polygon((15 22.5 16.25, 15 25 17.5, 15 27.5 18.75, 30 27.5 18.75, 30 20 15, " +
                                   "20 20 15, 20 22.5 16.25, 15 22.5 16.25))")


class TestUnion3D(unittest.TestCase):

    def test_1(self):
        result = UtilitiesGeom.union3D([union1, union2])
        result = result[0].ExportToWkt()
        corr = "POLYGON ((10 10 10,20 10 10,30 10 10,30 20 15,20 20 15,15 20 15,10 20 15,10 10 10))"
        self.assertEqual(corr, result)

    def test_2(self):
        result = UtilitiesGeom.union3D([union1, union3])
        result1 = result[0].ExportToWkt()
        corr1 = "POLYGON ((10 10 10,20 10 10,20 20 15,15 20 15,10 20 15,10 10 10))"
        self.assertEqual(corr1, result1)
        result2 = result[1].ExportToWkt()
        corr2 = "POLYGON ((20 10 10,30 10 10,30 20 10,20 20 10,20 10 10))"
        self.assertEqual(corr2, result2)

    def test_3(self):
        result = UtilitiesGeom.union3D([union1, union2, union4])
        result = result[0].ExportToWkt()
        corr = "POLYGON ((10 10 10,20 10 10,30 10 10,30 20 15,20 20 15,15 20 15,15.0 22.5 16.25,15 25 17.5," + \
               "5 25 17.5,5 20 15,10 20 15,10 10 10))"
        self.assertEqual(corr, result)

    def test_4(self):
        result = UtilitiesGeom.union3D([union1, union2, union4, union5])
        result = result[0].ExportToWkt()
        corr = "POLYGON ((20 20 15,20.0 22.5 16.25,15.0 22.5 16.25,15 25 17.5,5 25 17.5,5 20 15,10 20 15,10 10 10," + \
               "20 10 10,30 10 10,30 20 15,20 20 15),(15.0 22.5 16.25,15 25 17.5,5 25 17.5,5 20 15,10 20 15," + \
               "10 10 10,20 10 10,30 10 10,30 20 15,20 20 15,15 20 15,15.0 22.5 16.25),(15 25 17.5,15.0 27.5 18.75," + \
               "30.0 27.5 18.75,30 20 15,20 20 15,15 20 15,15.0 22.5 16.25,15 25 17.5),(30 20 15,20 20 15,15 20 15," + \
               "15.0 22.5 16.25,15 25 17.5,5 25 17.5,5 20 15,10 20 15,10 10 10,20 10 10,30 10 10,30 20 15))"
        self.assertEqual(corr, result)

    def test_5(self):
        result = UtilitiesGeom.union3D([union1, union2, union3, union4, union5])
        result1 = result[0].ExportToWkt()
        corr1 = "POLYGON ((20 20 15,20.0 22.5 16.25,15.0 22.5 16.25,15 25 17.5,5 25 17.5,5 20 15,10 20 15,10 10 10," + \
                "20 10 10,30 10 10,30 20 15,20 20 15),(15.0 22.5 16.25,15 25 17.5,5 25 17.5,5 20 15,10 20 15," + \
                "10 10 10,20 10 10,30 10 10,30 20 15,20 20 15,15 20 15,15.0 22.5 16.25),(15 25 17.5," + \
                "15.0 27.5 18.75,30.0 27.5 18.75,30 20 15,20 20 15,15 20 15,15.0 22.5 16.25,15 25 17.5)," + \
                "(30 20 15,20 20 15,15 20 15,15.0 22.5 16.25,15 25 17.5,5 25 17.5,5 20 15,10 20 15,10 10 10," + \
                "20 10 10,30 10 10,30 20 15))"
        self.assertEqual(corr1, result1)
        result2 = result[1].ExportToWkt()
        corr2 = "POLYGON ((20 10 10,30 10 10,30 20 10,20 20 10,20 10 10))"
        self.assertEqual(corr2, result2)


if __name__ == '__main__':
    unittest.main()
