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

# XML-Bibliotheken
from lxml import etree
# noinspection PyUnresolvedReferences
from lxml.etree import QName

# Geo-Bibliotheken
from osgeo import ogr
from sympy import Point3D, Plane, Line


#####

class UtilitiesGeom:
    """ Model-Klasse mit nützlichen Geometrie-Tools """

    @staticmethod
    def geomToGml(geom):
        """ Umwandeln von Geometrien in ein XML-Objekt

        Args:
            geom: Die umzuwandelnde Geometrie

        Returns:
            Das daraus erzeugte XML-Objekt
        """
        gmlGeom = geom.ExportToGML()
        gmlGeom = gmlGeom[0:gmlGeom.find(">")] + " xmlns:gml='http://www.opengis.net/gml'" + gmlGeom[gmlGeom.find(">"):]
        xml = etree.XML(gmlGeom)
        return xml

    @staticmethod
    def simplify(geom, zd=False, distTol=0.1):
        """ Vereinfachen von OGR-Geometrien (Polygone und LineStrings)

        Args:
            geom: Die zu vereinfachende Geometrie
            zd: Ob nur zweidimensional vereinfacht werden soll
                default: False
            distTol: Die erlaubte Toleranz bei der Vereinfachung der Punktnähe (in Einheit der Geometrie)
                default: 0.1

        Returns:
            Die vereinfachte Geometrie oder None falls ungültig
        """
        supported = ["POLYGON", "LINESTRING"]
        # Wenn nicht unterstützt: Direkt zurückgeben
        if geom is None or geom.IsEmpty() or geom.GetGeometryName() not in supported:
            return geom
        else:
            # Auslesen der Geometrie und Erstellen der neuen Geometrie
            if geom.GetGeometryName() == "POLYGON":
                ring = geom.GetGeometryRef(0)
                geomNew = ogr.Geometry(ogr.wkbPolygon)
                ringNew = ogr.Geometry(ogr.wkbLinearRing)
            else:
                ring = geom
                ringNew = ogr.Geometry(ogr.wkbLineString)
            count = ring.GetPointCount()

            # Anfangspunkt
            ringNew.AddPoint(ring.GetPoint(0)[0], ring.GetPoint(0)[1], ring.GetPoint(0)[2])

            # Vereinfachung: Betrachtung von drei Punkten hintereinander
            for i in range(2, ring.GetPointCount()):
                ptEnd = ring.GetPoint(i)
                ptMid = ring.GetPoint(i - 1)
                ptSt = ring.GetPoint(i - 2)

                # Abstand zwischen erstem und mittlerem Punkt: Unter Toleranz = Überspringen
                sqXY = np.square(ptMid[0] - ptSt[0]) + np.square(ptMid[1] - ptSt[1])
                dist = np.sqrt(sqXY) if zd else np.sqrt(sqXY + np.square(ptMid[2] - ptSt[2]))
                if dist < distTol:
                    continue

                # Parallelität der Linien von Startpunkt zu Mittelpunkt und Mittelpunkt zu Endpunkt prüfen
                tol = 0.05
                # Y-Steigung in Bezug auf X-Verlauf
                gradYSt = -1 if ptMid[0] - ptSt[0] == 0 else (ptMid[1] - ptSt[1]) / abs(ptMid[0] - ptSt[0])
                gradYEnd = -1 if ptEnd[0] - ptMid[0] == 0 else (ptEnd[1] - ptMid[1]) / abs(ptEnd[0] - ptMid[0])
                if gradYSt - tol < gradYEnd < gradYSt + tol:
                    # Z-Steigung in Bezug auf X-Verlauf
                    gradZSt = -1 if ptMid[0] - ptSt[0] == 0 else (ptMid[2] - ptSt[2]) / abs(ptMid[0] - ptSt[0])
                    gradZEnd = -1 if ptEnd[0] - ptMid[0] == 0 else (ptEnd[2] - ptMid[2]) / abs(ptEnd[0] - ptMid[0])
                    if gradZSt - tol < gradZEnd < gradZSt + tol:
                        # Z-Steigung in Bezug auf Y-Verlauf
                        gradYZSt = -1 if ptMid[1] - ptSt[1] == 0 else (ptMid[2] - ptSt[2]) / abs(ptMid[1] - ptSt[1])
                        gradYZEnd = -1 if ptEnd[1] - ptMid[1] == 0 else (ptEnd[2] - ptMid[2]) / abs(ptEnd[1] - ptMid[1])
                        if gradYZSt - tol < gradYZEnd < gradYZSt + tol:
                            continue

                # Wenn keine Vereinfachung: Mittelpunkt setzen
                ringNew.AddPoint(ptMid[0], ptMid[1], ptMid[2])

            # Abschließen der Geometrie
            if geom.GetGeometryName() == "POLYGON":
                ringNew.CloseRings()
                geomNew.AddGeometry(ringNew)
            else:
                ptLineEnd = geom.GetPoint(geom.GetPointCount() - 1)
                ringNew.AddPoint(ptLineEnd[0], ptLineEnd[1], ptLineEnd[2])
                geomNew = ringNew

            # Wenn Polygon weniger als vier Eckpunkte hat: Eigentlich ein LineString
            if ringNew.GetPointCount() < 4 and geom.GetGeometryName() == "POLYGON":
                geomNewLine = ogr.Geometry(ogr.wkbPolygon)
                geomNewLine.AddPoint(geomNew.GetPoint(0)[0], geomNew.GetPoint(0)[1], geomNew.GetPoint(0)[2])
                geomNewLine.AddPoint(geomNew.GetPoint(1)[0], geomNew.GetPoint(1)[1], geomNew.GetPoint(1)[2])
                return geomNewLine

            # Wenn es noch weiter vereinfacht werden kann: Iterativer Vorgang über rekursive Aufrufe
            elif ringNew.GetPointCount() < count:
                return UtilitiesGeom.simplify(geomNew)

            # Wenn fertig: Zurückgeben
            else:
                return geomNew

    @staticmethod
    def union3D(geomsIn):
        geomsOut = []
        done = []
        for i in range(0, len(geomsIn)):
            if i in done:
                continue
            geom1 = UtilitiesGeom.simplify(geomsIn[i])
            if geom1 is None or geom1.GetGeometryName() != "POLYGON":
                done.append(i)
                continue
            ring1 = geom1.GetGeometryRef(0)
            if ring1 is None:
                done.append(i)
                continue
            for j in range(i + 1, len(geomsIn)):
                if j in done:
                    continue
                geom2 = UtilitiesGeom.simplify(geomsIn[j])
                if geom2 is None or geom2.GetGeometryName() != "POLYGON":
                    done.append(j)
                    continue
                ring2 = geom2.GetGeometryRef(0)
                if ring2 is None:
                    done.append(j)
                    continue
                samePts = []
                for k in range(0, ring1.GetPointCount() - 1):
                    point1 = ring1.GetPoint(k)
                    for l in range(0, ring2.GetPointCount() - 1):
                        point2 = ring2.GetPoint(l)
                        if point1 == point2:
                            samePts.append(point1)
                if len(samePts) > 1:
                    plane1 = Plane(Point3D(ring1.GetPoint(0)[0], ring1.GetPoint(0)[1], ring1.GetPoint(0)[2]),
                                   Point3D(ring1.GetPoint(1)[0], ring1.GetPoint(1)[1], ring1.GetPoint(1)[2]),
                                   Point3D(ring1.GetPoint(2)[0], ring1.GetPoint(2)[1], ring1.GetPoint(2)[2]))
                    plane2 = Plane(Point3D(ring2.GetPoint(0)[0], ring2.GetPoint(0)[1], ring2.GetPoint(0)[2]),
                                   Point3D(ring2.GetPoint(1)[0], ring2.GetPoint(1)[1], ring2.GetPoint(1)[2]),
                                   Point3D(ring2.GetPoint(2)[0], ring2.GetPoint(2)[1], ring2.GetPoint(2)[2]))
                    if plane1.is_parallel(plane2):
                        geometry = ogr.Geometry(ogr.wkbPolygon)
                        ring = ogr.Geometry(ogr.wkbLinearRing)
                        for k in range(0, ring1.GetPointCount() - 1):
                            point1 = ring1.GetPoint(k)
                            if point1 in samePts:
                                ring.AddPoint(point1[0], point1[1], point1[2])
                                for l in range(0, ring2.GetPointCount() - 1):
                                    point2 = ring2.GetPoint(l)
                                    if point2 == point1:
                                        if ring2.GetPoint(l + 1) in samePts:
                                            break
                                        else:
                                            for m in range(l + 1, ring2.GetPointCount() - 1):
                                                point3 = ring2.GetPoint(m)
                                                if point3 in samePts:
                                                    break
                                                else:
                                                    ring.AddPoint(point3[0], point3[1], point3[2])
                                            for o in range(0, l):
                                                point3 = ring2.GetPoint(o)
                                                if point3 in samePts:
                                                    break
                                                else:
                                                    ring.AddPoint(point3[0], point3[1], point3[2])
                                            break

                            else:
                                ring.AddPoint(point1[0], point1[1], point1[2])
                        ring.CloseRings()
                        geometry.AddGeometry(ring)
                        geomsOut.append(geometry)
                        done.append(i)
                        done.append(j)
                        break

            if i not in done:
                done.append(i)
                geomsOut.append(geomsIn[i])

        if len(geomsOut) < len(geomsIn):
            return UtilitiesGeom.union3D(geomsOut)
        else:
            return geomsOut

    @staticmethod
    def buffer2D(geom, dist):
        if geom is None or geom.IsEmpty() or geom.GetGeometryName() != "POLYGON":
            return geom
        else:
            ring = geom.GetGeometryRef(0)

            geomBuffer = ogr.Geometry(ogr.wkbPolygon)
            ringBuffer = ogr.Geometry(ogr.wkbLinearRing)

            for i in range(1, ring.GetPointCount()):
                if i == 1:
                    ptStart = ring.GetPoint(ring.GetPointCount() - 2)
                else:
                    ptStart = ring.GetPoint(i - 2)
                ptEnd = ring.GetPoint(i)
                ptMid = ring.GetPoint(i - 1)

                vStart = [ptMid[0] - ptStart[0], ptMid[1] - ptStart[1]]
                vStartB = [vStart[1], vStart[0]]
                vStartBLen = np.sqrt(np.square(vStartB[0]) + np.square(vStartB[1]))
                vStartBNorm = [vStartB[0] / vStartBLen, vStartB[1] / vStartBLen]
                vStartBDist = [vStartBNorm[0] * dist, vStartBNorm[1] * dist]

                vEnd = [ptEnd[0] - ptMid[0], ptEnd[1] - ptMid[1]]
                vEndB = [vEnd[1], vEnd[0]]
                vEndBLen = np.sqrt(np.square(vEndB[0]) + np.square(vEndB[1]))
                vEndBNorm = [vEndB[0] / vEndBLen, vEndB[1] / vEndBLen]
                vEndBDist = [vEndBNorm[0] * dist, vEndBNorm[1] * dist]

                ptMidB1 = [ptMid[0] + vStartBDist[0], ptMid[1] + vStartBDist[1], ptMid[2]]
                ptMidB2 = [ptMid[0] + vEndBDist[0], ptMid[1] + vEndBDist[1], ptMid[2]]

                b1Line = Line(Point3D(ptMidB1[0], ptMidB1[1], ptMidB1[2]),
                              Point3D(ptMidB1[0] + (ptMid[0] - ptStart[0]), ptMidB1[1] + (ptMid[1] - ptStart[1]),
                                      ptMidB1[2]))
                b2Line = Line(Point3D(ptMidB2[0], ptMidB2[1], ptMidB2[2]),
                              Point3D(ptMidB2[0] + (ptEnd[0] - ptMid[0]), ptMidB2[1] + (ptEnd[1] - ptMid[1]),
                                      ptMidB2[2]))
                sPoint = b1Line.intersection(b2Line)[0]
                ringBuffer.AddPoint(float(sPoint[0]), float(sPoint[1]), ptMidB1[2])

            ringBuffer.CloseRings()
            geomBuffer.AddGeometry(ringBuffer)
            if geomBuffer.GetGeometryRef(0).GetPointCount() < 4:
                return None
            else:
                return geomBuffer
