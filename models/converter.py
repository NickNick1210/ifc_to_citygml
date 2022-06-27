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
import os, sys
import numpy as np
import osgeo.osr as osr
import osgeo.ogr as ogr
import uuid

# IFC-Bibliotheken
import ifcopenshell
from ifcopenshell import geom
from ifcopenshell.util import element
from qgis.PyQt.QtCore import QCoreApplication
from osgeo import ogr
from lxml import etree
from lxml.etree import Element, SubElement, QName, tounicode

from .xmlns import XmlNs


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
        root = etree.Element(QName(XmlNs.core, "CityModel"),
                             nsmap={'schemaLocation': XmlNs.schemaLocation, 'core': XmlNs.core, 'xmlns': XmlNs.xmlns,
                                    'bdlg': XmlNs.bldg, 'gen': XmlNs.gen, 'grp': XmlNs.grp, 'app': XmlNs.app,
                                    'gml': XmlNs.gml, 'xAL': XmlNs.xAL, 'xlink': XmlNs.xlink, 'xsi': XmlNs.xsi})
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
        et.write(self.outPath, xml_declaration=True, encoding="UTF-8", pretty_print=True)

    def getTransformMatrix(self, project):
        def getModelContext(project):
            flag = False
            for context in project.RepresentationContexts:
                if context.ContextType == "Model":
                    flag = True
                    return context
            if flag == False:
                print("No context for model was found in this project")

        contextForModel = getModelContext(project)
        a, b = contextForModel.TrueNorth.DirectionRatios
        transformMatrix = [[b, -a, 0], [a, b, 0], [0, 0, 1]]
        transformMatrix = np.mat(transformMatrix).I
        return transformMatrix

    def getOriginShift(self, site):
        def mergeDegrees(Degrees):
            if len(Degrees) == 4:
                degree = Degrees[0] + Degrees[1] / 60.0 + (Degrees[2] + Degrees[3] / 1000000.0) / 3600.0
            elif len(Degrees) == 3:
                degree = Degrees[0] + Degrees[1] / 60.0 + Degrees[2] / 3600.0
            else:
                print("Wrong input of degrees")
            return degree

        Lat, Lon = site.RefLatitude, site.RefLongitude
        a, b = mergeDegrees(Lat), mergeDegrees(Lon)

        source = osr.SpatialReference()
        source.ImportFromEPSG(4326)
        # Berechnung des EPSG-Codes des Zielkoordinatensystems
        # Die WGS84-Grenzen für die UTM-Zone 32N (EPSG-Code 32632) liegen
        # zwischen 6° und 12°
        # Die WGS84-Grenzen für die UTM-Zone 33N (EPSG-Code 32633) liegen
        # zwischen 12° und 18°
        if 18 > b >= 12:
            EPSG = 32633
        elif 6 <= b < 12:
            EPSG = 32632
        target = osr.SpatialReference()
        target.ImportFromEPSG(EPSG)
        transform = osr.CoordinateTransformation(source, target)
        x, y, z = transform.TransformPoint(a, b)
        c = site.RefElevation
        return [x, y, c]

    def georeferencingPoint(self, transMatrix, originShift, inX, inY):
        a = [inX, inY, 0]
        result = np.mat(a) * np.mat(transMatrix) + np.mat(originShift)
        return result

    def convertLoD0(self, ifc, root, eade):
        root.set("name", "")

        # BoundedBy
        chBound = etree.SubElement(root, QName(XmlNs.core, "boundedBy"))
        chBoundEnv = etree.SubElement(chBound, QName(XmlNs.gml, "Envelope"))
        chBoundEnv.set("srsDimension", "3")
        chBoundEnv.set("srsName", "TODO!!!")
        chBoundEnvLC = etree.SubElement(chBoundEnv, QName(XmlNs.gml, "lowerCorner"))
        chBoundEnvLC.set("srsDimension", "3")
        chBoundEnvUC = etree.SubElement(chBoundEnv, QName(XmlNs.gml, "upperCorner"))
        chBoundEnvUC.set("srsDimension", "3")

        ifcProject = ifc.by_type("IfcProject")[0]
        ifcSite = ifc.by_type("IfcSite")[0]
        ifcBuilding = ifc.by_type("IfcBuilding")[0]

        originShift = self.getOriginShift(ifcSite)
        trans = self.getTransformMatrix(ifcProject)

        if ifcBuilding.Representation != None:
            settings = geom.settings()
            settings.set(settings.INCLUDE_CURVES, True)
            settings.set(settings.USE_WORLD_COORDS, True)
            bldgShape = geom.create_shape(settings, ifcBuilding)
            verts = bldgShape.geometry.verts
            print(str(verts))

            grouped_verts = []
            for i in range(0, len(verts), 3):
                result = self.georeferencingPoint(trans, originShift, verts[i], verts[i + 1])
                array = np.array(result)
                grouped_verts.append((array[0][0], array[0][1]))
            print(str(grouped_verts))
        # TODO: BoundedBy

        # Building
        chCOM = etree.SubElement(root, QName(XmlNs.core, "cityObjectMember"))
        chBldg = etree.SubElement(chCOM, QName(XmlNs.bldg, "Building"))
        chBldg.set("id", "UUID_" + str(uuid.uuid4()))
        chBldgName = etree.SubElement(chBldg, QName(XmlNs.gml, "name"))
        chBldgName.text = ifcBuilding.Name
        chBldgDescr = etree.SubElement(chBldg, QName(XmlNs.gml, "description"))
        chBldgDescr.text = ifcBuilding.Description
        # TODO: Weitere Gebäude-Attribute

        # FootPrint
        chBldgFootPrint = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod0FootPrint"))
        # TODO: FootPrint-Geometrie

        # RoofEdge
        chBldgRoofEdge = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod0RoofEdge"))
        # TODO: RoofEdge-Geometrie

        chBldgAdr = etree.SubElement(chBldg, QName(XmlNs.bldg, "address"))
        chBldgAdrObj = etree.SubElement(chBldgAdr, QName(XmlNs.core, "Address"))
        chBldgAdrXal = etree.SubElement(chBldgAdrObj, QName(XmlNs.core, "xalAddress"))
        chBldgAdrDetails = etree.SubElement(chBldgAdrXal, QName(XmlNs.xAL, "AddressDetails"))
        chBldgAdrLocality = etree.SubElement(chBldgAdrDetails, QName(XmlNs.xAL, "AddressDetails"))
        # TODO: Addresse

        return root
