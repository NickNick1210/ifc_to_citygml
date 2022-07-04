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
import math

import numpy
import numpy as np

# QGIS-Bibliotheken
import osgeo.osr as osr


#####

class Transformer:
    """ Model-Klasse zum Transformieren vom lokalen in ein projizertes Koordinatensystem """
    def __init__(self, ifc):
        """ Konstruktor der Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien

        Args:
            parent: Die zugrunde liegende zentrale Model-Klasse
            inPath: Pfad zur IFC-Datei
            outPath: Pfad zur CityGML-Datei
        """

        self.ifc = ifc
        self.epsg = self.getCRS()
        self.originShift = self.getOriginShift()
        self.trans = self.getTransformMatrix()

    def getModelContext(self):
        project = self.ifc.by_type("IfcProject")[0]
        print(project)
        for context in project.RepresentationContexts:
            print(context)
            if context.ContextType == "Model":
                return context
        print("No context for model was found in this project")

    def getTransformMatrix(self):
        contextForModel = self.getModelContext()
        a = contextForModel.TrueNorth.DirectionRatios[0]
        b = contextForModel.TrueNorth.DirectionRatios[1]
        transformMatrix = [[b, -a, 0], [a, b, 0], [0, 0, 1]]
        transformMatrix = np.mat(transformMatrix).I
        return transformMatrix

    def getOriginShift(self):
        site = self.ifc.by_type("IfcSite")[0]
        Lat, Lon = site.RefLatitude, site.RefLongitude
        a, b = self.mergeDegrees(Lat), self.mergeDegrees(Lon)

        source = osr.SpatialReference()
        source.ImportFromEPSG(4326)
        target = osr.SpatialReference()
        target.ImportFromEPSG(self.epsg)
        transform = osr.CoordinateTransformation(source, target)
        x, y, z = transform.TransformPoint(a, b)
        c = site.RefElevation
        return [x, y, c]

    def mergeDegrees(self, Degrees):
        if len(Degrees) == 4:
            degree = Degrees[0] + Degrees[1] / 60.0 + (Degrees[2] + Degrees[3] / 1000000.0) / 3600.0
        elif len(Degrees) == 3:
            degree = Degrees[0] + Degrees[1] / 60.0 + Degrees[2] / 3600.0
        else:
            degree = -1
        return degree

    def getCRS(self):
        site = self.ifc.by_type("IfcSite")[0]
        Lat, Lon = site.RefLatitude, site.RefLongitude
        a, b = self.mergeDegrees(Lat), self.mergeDegrees(Lon)

        source = osr.SpatialReference()
        source.ImportFromEPSG(4326)
        # Berechnung des EPSG-Codes des Zielkoordinatensystems
        zone = math.ceil((b+180)/6)
        if b >= 0:
            epsg = zone + 32600
        else:
            epsg = zone + 32700
        return epsg

    def georeferencePoint(self, point):
        a = [point[0], point[1], point[2]]
        result = np.mat(a) * np.mat(self.trans) + np.mat(self.originShift)
        return np.array(result)[0]
