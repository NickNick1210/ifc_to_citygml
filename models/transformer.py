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
import numpy as np

# Geo-Bibliotheken
import osgeo.osr as osr

#####


class Transformer:
    """ Model-Klasse zum Transformieren vom lokalen in ein projizertes Koordinatensystem """

    def __init__(self, ifc):
        """ Konstruktor der Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien

        Args:
            ifc: Die zugrunde liegende IFC-Datei
        """
        # Initialisierung von Attributen
        self.ifc = ifc

        # Transformationsparameter
        self.epsg = self.getCRS()
        self.originShift = self.getOriginShift()
        self.trans = self.getTransformMatrix()

    def getCRS(self):
        """ Berechnung des UTM-Koordinatensystems, in dem sich die Szenerie befindet

        Returns:
            Das UTM-Koordinatensystem als EPSG-Code
        """
        # Geographische Koordinaten
        site = self.ifc.by_type("IfcSite")[0]
        a, b = self.mergeDegrees(site.RefLatitude), self.mergeDegrees(site.RefLongitude)
        source = osr.SpatialReference()
        source.ImportFromEPSG(4326)

        # Einordnung in die UTM-Zonen und Berechnung des EPSG-Codes
        zone = math.ceil((b + 180) / 6)
        epsg = (zone + 32600) if b >= 0 else (zone + 32700)
        return epsg

    def getOriginShift(self):
        """ Berechnung der Datumsverschiebung zwischen Urpsrungs- und Zielkoordinatensystem

        Returns:
            Die Datumsverschiebung als Vektor
        """
        # Geographische Koordinaten
        site = self.ifc.by_type("IfcSite")[0]
        a, b = self.mergeDegrees(site.RefLatitude), self.mergeDegrees(site.RefLongitude)

        # Ursprungs-CRS
        source = osr.SpatialReference()
        source.ImportFromEPSG(4326)

        # Ziel-CRS
        target = osr.SpatialReference()
        target.ImportFromEPSG(self.epsg)

        # Transformation
        transform = osr.CoordinateTransformation(source, target)
        x, y, z = transform.TransformPoint(a, b)
        c = site.RefElevation
        return [x, y, c]

    @staticmethod
    def mergeDegrees(degrees):
        """ Konvertierung von geographischen Koordinaten aus dem Sexagesimalformat in das Dezimalformat

        Args:
            degrees: Geographische Koordinate im Sexagesimalformat als Array

        Returns:
            Geographische Koordinate im Dezimalformat als float
        """
        if len(degrees) == 4:
            degree = degrees[0] + degrees[1] / 60.0 + (degrees[2] + degrees[3] / 1000000.0) / 3600.0
        elif len(degrees) == 3:
            degree = degrees[0] + degrees[1] / 60.0 + degrees[2] / 3600.0
        else:
            degree = -1
        return degree

    def getTransformMatrix(self):
        """ Berechnungs der Transformationsmatrix zwischen dem lokalen und dem übergeordneten Koordinatensystem

        Returns:
            Die Transformationsmatrix
        """
        # Northing
        project = self.ifc.by_type("IfcProject")[0]
        contextForModel = None
        for context in project.RepresentationContexts:
            if context.ContextType == "Model":
                contextForModel = context
        a = contextForModel.TrueNorth.DirectionRatios[0]
        b = contextForModel.TrueNorth.DirectionRatios[1]

        # Matrix
        transformMatrix = [[b, -a, 0], [a, b, 0], [0, 0, 1]]
        transformMatrix = np.mat(transformMatrix).I
        return transformMatrix

    def georeferencePoint(self, point):
        """ Georeferenziert einen Punkt

        Args:
            point: Der zu georeferenzierende Punkt als Vektor

        Returns:
            Der georeferenzierte Punkt als Vektor
        """
        result = np.mat(point) * np.mat(self.trans) + np.mat(self.originShift)
        return np.array(result)[0]
