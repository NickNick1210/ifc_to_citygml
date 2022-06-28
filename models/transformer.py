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
import numpy as np

# QGIS-Bibliotheken
import osgeo.osr as osr


#####

class Transformer:
    """ Model-Klasse zum Transformieren vom lokalen in ein projizertes Koordinatensystem """

    @staticmethod
    def getModelContext(proj):
        for context in proj.RepresentationContexts:
            if context.ContextType == "Model":
                return context
        print("No context for model was found in this project")

    @staticmethod
    def getTransformMatrix(project):
        contextForModel = Transformer.getModelContext(project)
        a, b = contextForModel.TrueNorth.DirectionRatios
        transformMatrix = [[b, -a, 0], [a, b, 0], [0, 0, 1]]
        transformMatrix = np.mat(transformMatrix).I
        return transformMatrix

    @staticmethod
    def getOriginShift(site, epsg):
        Lat, Lon = site.RefLatitude, site.RefLongitude
        a, b = Transformer.mergeDegrees(Lat), Transformer.mergeDegrees(Lon)

        source = osr.SpatialReference()
        source.ImportFromEPSG(4326)
        target = osr.SpatialReference()
        target.ImportFromEPSG(epsg)
        transform = osr.CoordinateTransformation(source, target)
        x, y, z = transform.TransformPoint(a, b)
        c = site.RefElevation
        return [x, y, c]

    @staticmethod
    def mergeDegrees(Degrees):
        if len(Degrees) == 4:
            degree = Degrees[0] + Degrees[1] / 60.0 + (Degrees[2] + Degrees[3] / 1000000.0) / 3600.0
        elif len(Degrees) == 3:
            degree = Degrees[0] + Degrees[1] / 60.0 + Degrees[2] / 3600.0
        else:
            degree = -1
        return degree

    @staticmethod
    def getCRS(ifcSite):
        Lat, Lon = ifcSite.RefLatitude, ifcSite.RefLongitude
        a, b = Transformer.mergeDegrees(Lat), Transformer.mergeDegrees(Lon)

        source = osr.SpatialReference()
        source.ImportFromEPSG(4326)
        # Berechnung des EPSG-Codes des Zielkoordinatensystems
        if 18 > b >= 12:
            epsg = 32633
        elif 6 <= b < 12:
            epsg = 32632
        else:
            epsg = -1

        return epsg

    @staticmethod
    def georeferencePoint(transMatrix, originShift, point):
        a = [point[0], point[1], point[2]]
        result = np.mat(a) * np.mat(transMatrix) + np.mat(originShift)
        return np.array(result)[0]
