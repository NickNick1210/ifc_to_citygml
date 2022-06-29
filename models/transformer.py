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
        a, b = contextForModel.TrueNorth.DirectionRatios
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
        if 18 > b >= 12:
            epsg = 32633
        elif 6 <= b < 12:
            epsg = 32632
        elif 54 <= b < 60:
            epsg = 32640
        elif 0 <= b < 6:
            epsg = 32631
        else:
            epsg = -1
        # TODO: weitere Zonen

        return epsg

    def georeferencePoint(self, point):
        a = [point[0], point[1], point[2]]
        result = np.mat(a) * np.mat(self.trans) + np.mat(self.originShift)
        return np.array(result)[0]

    def placePoints(self, ifcElement, points):
        ifcLocalPlacement = ifcElement.ObjectPlacement
        shift = self.calcShift(ifcLocalPlacement, [0, 0, 0])
        pointsTr = []
        for point in points:
            pointTr = np.add(point, shift)
            pointTr = self.georeferencePoint(pointTr)
            pointsTr.append(pointTr)
        return np.array(pointsTr).tolist()

    def calcShift(self, ifcLocalPlacement, shift=[0, 0, 0]):
        coords = ifcLocalPlacement.RelativePlacement.Location.Coordinates
        shift[0] += coords[0]
        shift[1] += coords[1]
        shift[2] += coords[2]
        ifcLocalPlacementNext = ifcLocalPlacement.PlacementRelTo
        if ifcLocalPlacementNext is None:
            return shift
        else:
            return self.calcShift(ifcLocalPlacementNext, shift)

