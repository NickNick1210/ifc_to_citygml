# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.1 (23.06.2022)
 ***************************************************************************/
"""

#####

# Standard-Bibliotheken
import os

# IFC-Bibliotheken
import ifcopenshell
from qgis.PyQt.QtCore import QCoreApplication
from osgeo import ogr
from lxml import etree


class Converter():
    def __init__(self, parent, inPath, outPath):
        """Constructor."""
        self.parent = parent
        self.inPath = inPath
        self.outPath = outPath





    def run(self, lod, eade, integr):
        ifc = self.readIfc(self.inPath)
        root = self.createSchema()

        if lod == 0:
            root = self.convertLoD0(ifc, root, eade)
        elif lod == 1:
            # TODO
            pass
        elif lod == 2:
            # TODO
            pass
        elif lod == 3:
            # TODO
            pass
        elif lod == 4:
            # TODO
            pass

        self.writeCGML(root)
        if integr:
            # TODO
            pass

        self.parent.completed()


    def readIfc(self, path):
        ifc = ifcopenshell.open(path)
        return ifc


    def createSchema(self):
        root = etree.Element("CityModel", nsmap={'core': "http://www.opengis.net/citygml/2.0"})
        etree.SubElement(root, "boundedBy", nsmap = {'core': "http://www.opengis.net/citygml/2.0"})
        etree.SubElement(root, "cityObjectMember", nsmap={'core': "http://www.opengis.net/citygml/2.0"})
        return root


    def createGeom(self):
        # Test
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(1179091.1646903288, 712782.8838459781)
        ring.AddPoint(1161053.0218226474, 667456.2684348812)
        ring.AddPoint(1214704.933941905, 641092.8288590391)
        ring.AddPoint(1228580.428455506, 682719.3123998424)
        ring.AddPoint(1218405.0658121984, 721108.1805541387)
        ring.AddPoint(1179091.1646903288, 712782.8838459781)
        geom = ogr.Geometry(ogr.wkbPolygon)
        geom.AddGeometry(ring)
        cgml = geom.ExportToGML()
        print(cgml)


    def writeCGML(self, root):
        et = etree.ElementTree(root)
        et.write(self.outPath, xml_declaration = True, encoding = "UTF-8", pretty_print = True)


    def convertLoD0(self, ifc, root):

        return root

