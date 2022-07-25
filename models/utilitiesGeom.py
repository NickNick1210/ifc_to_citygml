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
import sys

import numpy as np

# XML-Bibliotheken
from lxml import etree
# noinspection PyUnresolvedReferences
from lxml.etree import QName

# Geo-Bibliotheken
from osgeo import ogr
from sympy import Point3D, Plane, Line
from shapely.geometry import Point, Polygon


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
    def sortPoints(points, fromPoint, toPoint):
        """ Sortieren von Punkten

        Args:
            points: Die zu sortierenden Punkte als Liste
            fromPoint: Punkt, von dessen Richtung aus sortiert werden soll
            toPoint: Punkt, in dessen Richtung hin sortiert werden soll

        Returns:
            Die sortierten Punkte als Liste
        """
        # Sortierung nach X, dann Y, dann Z
        # Z-Sortierung immer in positive Richtung

        # in positive X-Richtung
        if toPoint[0] > fromPoint[0]:
            # in positive Y-Richtung
            if toPoint[1] > fromPoint[1]:
                points.sort(key=lambda elem: (elem[0], elem[1], elem[2]))
            # in negative Y-Richtung
            else:
                points.sort(key=lambda elem: (elem[0], -elem[1], elem[2]))

        # in negative X-Richtung
        else:
            # in positive Y-Richtung
            if toPoint[1] > fromPoint[1]:
                points.sort(key=lambda elem: (-elem[0], elem[1], elem[2]))
            # in negative Y-Richtung
            else:
                points.sort(key=lambda elem: (-elem[0], -elem[1], elem[2]))

        return points

    @staticmethod
    def sortLines(lines, fromPoint, toPoint):
        """ Sortieren von Linien

        Args:
            lines: Die zu sortierenden Linien als Liste
            fromPoint: Punkt, von dessen Richtung aus sortiert werden soll
            toPoint: Punkt, in dessen Richtung hin sortiert werden soll

        Returns:
            Die sortierten Linien als Liste
        """
        # Sortierung nach X, dann Y, dann Z
        # Z-Sortierung immer in positive Richtung

        # in positive X-Richtung
        if toPoint[0] > fromPoint[0]:
            # in positive Y-Richtung
            if toPoint[1] > fromPoint[1]:
                lines.sort(key=lambda elem: (
                    min(elem[0][0], elem[1][0]), min(elem[0][1], elem[1][1]), min(elem[0][2], elem[1][2])))
            # in negative Y-Richtung
            else:
                lines.sort(key=lambda elem: (
                    min(elem[0][0], elem[1][0]), -max(elem[0][1], elem[1][1]), min(elem[0][2], elem[1][2])))

        # in negative X-Richtung
        else:
            # in positive Y-Richtung
            if toPoint[1] > fromPoint[1]:
                lines.sort(key=lambda elem: (
                    -max(elem[0][0], elem[1][0]), min(elem[0][1], elem[1][1]), min(elem[0][2], elem[1][2])))
            # in negative Y-Richtung
            else:
                lines.sort(key=lambda elem: (
                    -max(elem[0][0], elem[1][0]), -max(elem[0][1], elem[1][1]), min(elem[0][2], elem[1][2])))

        return lines

    @staticmethod
    def getPlane(pt1, pt2, pt3):
        """ Erstellen einer Ebene aus drei Punkten

        Args:
            pt1: Erster Punkt in der Ebene
            pt2: Zweiter Punkt in der Ebene
            pt3: Dritter Punkt in der Ebene

        Returns:
            Die erstellte Ebene
        """
        return Plane(Point3D(pt1[0], pt1[1], pt1[2]), Point3D(pt2[0], pt2[1], pt2[2]), Point3D(pt3[0], pt3[1], pt3[2]))

    @staticmethod
    def simplify(geom, distTol, angTol, zd=False):
        """ Vereinfachen von OGR-Geometrien (Polygone und LineStrings)

        Args:
            geom: Die zu vereinfachende Geometrie, einzeln oder als Liste
            zd: Ob nur zweidimensional vereinfacht werden soll
                default: False
            distTol: Die erlaubte Toleranz bei der Vereinfachung der Punktnähe (in Einheit der Geometrie)
                default: 0.1

        Returns:
            Die vereinfachte Geometrie, einzeln oder als Liste, oder None falls ungültig
        """
        supported = ["POLYGON", "LINESTRING"]
        geomList = geom if isinstance(geom, list) else [geom]
        simpList = []

        for geom in geomList:

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
                    ptEnd, ptMid, ptSt = ring.GetPoint(i), ring.GetPoint(i - 1), ring.GetPoint(i - 2)

                    # Abstand zwischen erstem und mittlerem Punkt: Unter Toleranz = Überspringen
                    sqXY = np.square(ptMid[0] - ptSt[0]) + np.square(ptMid[1] - ptSt[1])
                    dist = np.sqrt(sqXY) if zd else np.sqrt(sqXY + np.square(ptMid[2] - ptSt[2]))
                    if dist < distTol:
                        continue

                    # Parallelität der Linien von Startpunkt zu Mittelpunkt und Mittelpunkt zu Endpunkt prüfen
                    tol = angTol
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
                            gradYZEnd = -1 if ptEnd[1] - ptMid[1] == 0 else (ptEnd[2] - ptMid[2]) / abs(
                                ptEnd[1] - ptMid[1])
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
                    geomNewLine = ogr.Geometry(ogr.wkbLineString)
                    geomNewLine.AddPoint(geomNew.GetPoint(0)[0], geomNew.GetPoint(0)[1], geomNew.GetPoint(0)[2])
                    geomNewLine.AddPoint(geomNew.GetPoint(1)[0], geomNew.GetPoint(1)[1], geomNew.GetPoint(1)[2])
                    simpList.append(geomNewLine)

                    print(ringNew)
                    print(distTol)
                    print(tol)

                # Wenn es noch weiter vereinfacht werden kann: Iterativer Vorgang über rekursive Aufrufe
                elif ringNew.GetPointCount() < count:
                    simpList.append(UtilitiesGeom.simplify(geomNew, distTol, angTol))

                # Wenn fertig: Zurückgeben
                else:
                    simpList.append(geomNew)

        # Rückgabe
        if len(simpList) == 0:
            return None
        elif len(simpList) == 1:
            return simpList[0]
        else:
            return simpList

    @staticmethod
    def union3D(geomsIn, count=1):
        """ Vereinigen von OGR-Polygonen, sofern möglich

        Args:
            geomsIn: Die zu vereinfachenden Polygone als Liste

        Returns:
            Die vereinigten Polygone in einer Liste
        """
        geomsOut = []
        done = []

        # Alle Geometrie miteinander auf Berührung testen
        for i in range(0, len(geomsIn)):
            if i in done:
                continue
            geom1 = geomsIn[i]
            if geom1 is None or geom1.GetGeometryName() != "POLYGON" or geom1.IsEmpty():
                done.append(i)
                continue
            ring1 = geom1.GetGeometryRef(0)

            for j in range(i + 1, len(geomsIn)):
                if j in done:
                    continue
                geom2 = geomsIn[j]
                if geom2 is None or geom2.GetGeometryName() != "POLYGON" or geom2.IsEmpty():
                    done.append(j)
                    continue
                ring2 = geom2.GetGeometryRef(0)

                # Alle Eckpunkte miteinander vergleichen
                samePts = []
                firstK, lastK = None, None
                ks = []
                for k in range(0, ring1.GetPointCount() - 1):
                    for m in range(0, ring2.GetPointCount() - 1):
                        if ring1.GetPoint(k) == ring2.GetPoint(m):
                            if firstK is None:
                                firstK = k
                            lastK = k
                            ks.append(k)
                            samePts.append(ring1.GetPoint(k))

                # Wenn mehrere gleiche Punkte gefunden
                if len(samePts) > 1:

                    # Auf Parallität prüfen
                    geom1Simp = UtilitiesGeom.simplify(geom1, 0.001, .001)
                    ring1Simp = geom1Simp.GetGeometryRef(0)
                    geom2Simp = UtilitiesGeom.simplify(geom2, 0.001, 0.001)
                    ring2Simp = geom2Simp.GetGeometryRef(0)
                    pt11, pt12, pt13 = ring1Simp.GetPoint(0), ring1Simp.GetPoint(1), ring1Simp.GetPoint(2)
                    pt21, pt22, pt23 = ring2Simp.GetPoint(0), ring2Simp.GetPoint(1), ring2Simp.GetPoint(2)
                    r11 = [pt12[0] - pt11[0], pt12[1] - pt11[1], pt12[2] - pt11[2]]
                    r12 = [pt13[0] - pt11[0], pt13[1] - pt11[1], pt13[2] - pt11[2]]
                    r21 = [pt22[0] - pt21[0], pt22[1] - pt21[1], pt22[2] - pt21[2]]
                    r22 = [pt23[0] - pt21[0], pt23[1] - pt21[1], pt23[2] - pt21[2]]
                    norm1, norm2 = np.cross(r11, r12), np.cross(r21, r22)
                    unit1, unit2 = norm1 / np.linalg.norm(norm1), norm2 / np.linalg.norm(norm2)
                    unit2Neg = np.negative(unit2)

                    tol = 0.000001
                    if (unit1[0] - tol < unit2[0] < unit1[0] + tol and unit1[1] - tol < unit2[1] < unit1[1] + tol and \
                        unit1[2] - tol < unit2[2] < unit1[2] + tol) or (
                            unit1[0] - tol < unit2Neg[0] < unit1[0] + tol and unit1[1] - tol < unit2Neg[1] < unit1[
                        1] + tol and unit1[2] - tol < unit2Neg[2] < unit1[2] + tol):

                        # Vereinigungs-Geometrie erstellen
                        geometry = ogr.Geometry(ogr.wkbPolygon)
                        ring = ogr.Geometry(ogr.wkbLinearRing)

                        # Testen, ob alle übereinstimmenden Eckpunkte hintereinander liegen
                        row = True
                        if firstK == 0 and lastK == ring1.GetPointCount() - 2:
                            for p in range(0, len(ks)):
                                if ks[p] + 1 != ks[p + 1]:
                                    for q in range(p + 1, len(ks)):
                                        if q + 1 != len(ks) and ks[q] + 1 != ks[q + 1]:
                                            row = False
                                            break
                                break
                        else:
                            if firstK + len(samePts) - 1 != lastK:
                                row = False

                        if len(samePts) < 4 or row:
                            for k in range(0, ring1.GetPointCount() - 1):
                                point1 = ring1.GetPoint(k)
                                ring.AddPoint(point1[0], point1[1], point1[2])

                                # Wenn gleicher Eckpunkt: Anbinden der zweiten Geometrie
                                if point1 in samePts:
                                    for m in range(0, ring2.GetPointCount() - 1):
                                        point2 = ring2.GetPoint(m)
                                        if point2 == point1:
                                            if ring2.GetPoint(m + 1) in samePts:
                                                break
                                            else:
                                                for n in range(m + 1, ring2.GetPointCount() - 1):
                                                    point3 = ring2.GetPoint(n)
                                                    if point3 in samePts:
                                                        break
                                                    else:
                                                        ring.AddPoint(point3[0], point3[1], point3[2])
                                                for o in range(0, m):
                                                    point3 = ring2.GetPoint(o)
                                                    if point3 in samePts:
                                                        break
                                                    else:
                                                        ring.AddPoint(point3[0], point3[1], point3[2])
                                                break

                            # Geometrie abschließen
                            ring.CloseRings()
                            geometry.AddGeometry(ring)
                            for m in range(1, geom1.GetGeometryCount()):
                                geometry.AddGeometry(geom1.GetGeometryRef(m))
                            for n in range(1, geom2.GetGeometryCount()):
                                geometry.AddGeometry(geom2.GetGeometryRef(n))
                            geomsOut.append(geometry)
                            done.append(i)
                            done.append(j)
                            break

                        # Spezialfall: Loch zwischen den beiden Polygonen
                        else:
                            print("Hier")
                            print(ks)
                            print(samePts)
                            print(ring1.GetPointCount())

                            maxHeightX = -sys.maxsize
                            maxHeightXK = None
                            for x in range(0, ring1.GetPointCount() - 1):
                                pt = ring1.GetPoint(x)
                                if pt[2] > maxHeightX:
                                    maxHeightX = pt[2]
                                    maxHeightXK = x
                            maxHeightY = -sys.maxsize
                            maxHeightYK = None
                            for y in range(0, ring1.GetPointCount() - 1):
                                pt = ring1.GetPoint(y)
                                if pt[2] > maxHeightY:
                                    maxHeightY = pt[2]
                                    maxHeightYK = y
                            if maxHeightX >= maxHeightY:
                                maxHeightK = maxHeightXK
                            else:
                                maxHeightK = maxHeightYK
                                geomTemp = geom1
                                geom1 = geom2
                                geom2 = geomTemp
                                ringTemp = ring1
                                ring1 = ring2
                                ring2 = ringTemp

                            # Zwei k-m-Paare mit unterschied zwischen k2-k1 und m2-m1
                            sameKMs = []
                            for k in range(0, ring1.GetPointCount() - 1):
                                point1 = ring1.GetPoint(k)
                                if point1 in samePts:
                                    for m in range(0, ring2.GetPointCount() - 1):
                                        point2 = ring2.GetPoint(m)
                                        if point2 == point1:
                                            sameKMs.append([k, m])

                            print("SameKMs: " + str(sameKMs))

                            ringsHole = []
                            for r in range(0, len(sameKMs)):
                                currKM = sameKMs[r]
                                if r == 0:
                                    lastKM = sameKMs[len(sameKMs) - 1]
                                else:
                                    lastKM = sameKMs[r - 1]

                                if currKM[0] > lastKM[0]:
                                    kDiff = currKM[0] - lastKM[0]
                                else:
                                    kDiff = ring1.GetPointCount() - lastKM[0] + currKM[0] - 1
                                if currKM[1] < lastKM[1]:
                                    mDiff = abs(currKM[1] - lastKM[1])
                                else:
                                    mDiff = ring2.GetPointCount() - currKM[1] + lastKM[1] - 1

                                if kDiff != mDiff or kDiff > 1:
                                    print("Loch zwischen k" + str(lastKM[0]) + "/m" + str(lastKM[1]) + " und k" + str(
                                        currKM[0]) + "/m" + str(currKM[1]))
                                    ringHole = ogr.Geometry(ogr.wkbLinearRing)
                                    if currKM[0] > lastKM[0]:
                                        for s in range(lastKM[0], currKM[0]):
                                            pt = ring1.GetPoint(s)
                                            ringHole.AddPoint(pt[0], pt[1], pt[2])
                                        if currKM[1] < lastKM[1]:
                                            for t in range(currKM[1], lastKM[1]):
                                                pt = ring2.GetPoint(t)
                                                ringHole.AddPoint(pt[0], pt[1], pt[2])
                                        else:
                                            for t in range(currKM[1], ring2.GetPointCount() - 1):
                                                pt = ring2.GetPoint(t)
                                                ringHole.AddPoint(pt[0], pt[1], pt[2])
                                            for u in range(0, lastKM[1] + 1):
                                                pt = ring2.GetPoint(u)
                                                ringHole.AddPoint(pt[0], pt[1], pt[2])
                                    else:
                                        for s in range(lastKM[0], ring1.GetPointCount() - 1):
                                            pt = ring1.GetPoint(s)
                                            ringHole.AddPoint(pt[0], pt[1], pt[2])
                                        for t in range(0, currKM[0]):
                                            pt = ring1.GetPoint(t)
                                            ringHole.AddPoint(pt[0], pt[1], pt[2])
                                        if currKM[1] < lastKM[1]:
                                            for u in range(currKM[1], lastKM[1]):
                                                pt = ring2.GetPoint(u)
                                                ringHole.AddPoint(pt[0], pt[1], pt[2])
                                        else:
                                            for u in range(currKM[1], ring2.GetPointCount() - 1):
                                                pt = ring2.GetPoint(u)
                                                ringHole.AddPoint(pt[0], pt[1], pt[2])
                                            for v in range(0, lastKM[1] + 1):
                                                pt = ring2.GetPoint(v)
                                                ringHole.AddPoint(pt[0], pt[1], pt[2])

                                    ringHole.CloseRings()
                                    ringsHole.append(ringHole)

                            fin = False
                            startK = maxHeightK
                            while True:
                                if not fin:
                                    for k in range(startK, ring1.GetPointCount() - 1):
                                        point1 = ring1.GetPoint(k)
                                        ring.AddPoint(point1[0], point1[1], point1[2])
                                        print("k" + str(k) + ": " + str(point1) + " gesetzt")

                                        # Wenn gleicher Eckpunkt: Anbinden der zweiten Geometrie
                                        if point1 in samePts and k != maxHeightK:
                                            for m in range(0, ring2.GetPointCount() - 1):
                                                point2 = ring2.GetPoint(m)
                                                if point2 == point1:
                                                    stop = False
                                                    for n in range(m + 1, ring2.GetPointCount()):
                                                        point3 = ring2.GetPoint(n)
                                                        if point3 == ring1.GetPoint(maxHeightK):
                                                            stop = True
                                                            break
                                                        ring.AddPoint(point3[0], point3[1], point3[2])
                                                        print("n" + str(n) + ": " + str(point3) + " gesetzt")
                                                        if point3 in samePts:
                                                            for p in range(0, ring1.GetPointCount() - 1):
                                                                point4 = ring1.GetPoint(p)
                                                                if point3 == point4:
                                                                    print("p" + str(p) + " zu max" + str(maxHeightK))
                                                                    if p <= maxHeightK:
                                                                        for q in range(p + 1, maxHeightK):
                                                                            point5 = ring1.GetPoint(q)
                                                                            ring.AddPoint(point5[0], point5[1],
                                                                                          point5[2])
                                                                            print("q" + str(q) + ": " + str(
                                                                                point5) + " gesetzt")
                                                                    else:
                                                                        for q in range(p + 1,
                                                                                       ring1.GetPointCount() - 1):
                                                                            point5 = ring1.GetPoint(q)
                                                                            ring.AddPoint(point5[0], point5[1],
                                                                                          point5[2])
                                                                            print("q" + str(q) + ": " + str(
                                                                                point5) + " gesetzt")
                                                                        for q in range(0, maxHeightK):
                                                                            point5 = ring1.GetPoint(q)
                                                                            ring.AddPoint(point5[0], point5[1],
                                                                                          point5[2])
                                                                            print("q" + str(q) + ": " + str(
                                                                                point5) + " gesetzt")
                                                                    break
                                                            stop = True
                                                            break
                                                    if not stop:
                                                        for o in range(0, m):
                                                            point3 = ring2.GetPoint(o)
                                                            ring.AddPoint(point3[0], point3[1], point3[2])
                                                            print("o" + str(o) + ": " + str(point3) + " gesetzt")
                                                            if point3 in samePts:
                                                                for p in range(0, ring1.GetPointCount() - 1):
                                                                    point4 = ring1.GetPoint(p)
                                                                    if point3 == point4:
                                                                        if p <= maxHeightK:
                                                                            for q in range(p + 1, maxHeightK):
                                                                                point5 = ring1.GetPoint(q)
                                                                                ring.AddPoint(point5[0], point5[1],
                                                                                              point5[2])
                                                                                print("q" + str(q) + ": " + str(
                                                                                    point5) + " gesetzt")
                                                                        else:
                                                                            for q in range(p + 1,
                                                                                           ring1.GetPointCount() - 1):
                                                                                point5 = ring1.GetPoint(q)
                                                                                ring.AddPoint(point5[0], point5[1],
                                                                                              point5[2])
                                                                                print("q" + str(q) + ": " + str(
                                                                                    point5) + " gesetzt")
                                                                            for q in range(0, maxHeightK):
                                                                                point5 = ring1.GetPoint(q)
                                                                                ring.AddPoint(point5[0], point5[1],
                                                                                              point5[2])
                                                                                print("q" + str(q) + ": " + str(
                                                                                    point5) + " gesetzt")
                                                                        break
                                                                break
                                                        break
                                            fin = True
                                            break
                                    startK = 0
                                else:
                                    break

                            # Geometrie abschließen
                            ring.CloseRings()
                            print("Geom: " + str(ring.Length()))
                            geometry.AddGeometry(ring)
                            for m in range(1, geom1.GetGeometryCount()):
                                geometry.AddGeometry(geom1.GetGeometryRef(m))
                            for n in range(1, geom2.GetGeometryCount()):
                                geometry.AddGeometry(geom2.GetGeometryRef(n))
                            for ringHole in ringsHole:
                                print("Hole: " + str(ringHole.Length()))
                                if not ring.Length() - 0.00001 < ringHole.Length() < ring.Length() + 0.00001:
                                    geometry.AddGeometry(ringHole)
                            geomsOut.append(geometry)
                            done.append(i)
                            done.append(j)
                            break

            # Wenn keine berührende Geometrie gefunden
            if i not in done:
                done.append(i)
                geomsOut.append(geomsIn[i])

        # Wenn es noch weiter vereinigt werden kann: Iterativer Vorgang über rekursive Aufrufe
        if len(geomsOut) < len(geomsIn) and count < 5:
            print("von " + str(len(geomsIn)) + " zu " + str(len(geomsOut)))
            return UtilitiesGeom.union3D(geomsOut, count + 1)

        # Wenn fertig: Zurückgeben
        else:
            return geomsOut

    @staticmethod
    def buffer2D(geom, dist):
        """ Puffern von OGR-Polygonen

        Args:
            geom: Die zu puffernden Polygone, einzeln oder als Liste
            dist: Die Pufferdistanz in Einheit der Geometrie

        Returns:
            Die gepufferten Polygone, einzeln oder in einer Liste
        """
        geomList = geom if isinstance(geom, list) else [geom]
        bufferList = []

        for geom in geomList:
            # Wenn nicht unterstützt: Direkt zurückgeben
            if geom is None or geom.IsEmpty() or geom.GetGeometryName() != "POLYGON":
                return geom
            else:
                # Auslesen der Geometrie und Erstellen der neuen Geometrie
                ring = geom.GetGeometryRef(0)
                geomBuffer = ogr.Geometry(ogr.wkbPolygon)
                ringBuffer = ogr.Geometry(ogr.wkbLinearRing)

                # Vereinfachung: Betrachtung von drei Punkten hintereinander
                for i in range(1, ring.GetPointCount()):
                    ptSt = ring.GetPoint(ring.GetPointCount() - 2) if i == 1 else ring.GetPoint(i - 2)
                    ptEnd, ptMid = ring.GetPoint(i), ring.GetPoint(i - 1)

                    # Vektoren senkrecht zu den beiden Linien
                    vStartB = [ptMid[1] - ptSt[1], ptMid[0] - ptSt[0]]
                    vStartBLen = np.sqrt(np.square(vStartB[0]) + np.square(vStartB[1]))
                    vStartBDist = [(vStartB[0] / vStartBLen) * dist, (vStartB[1] / vStartBLen) * dist]
                    vEndB = [ptEnd[1] - ptMid[1], ptEnd[0] - ptMid[0]]
                    vEndBLen = np.sqrt(np.square(vEndB[0]) + np.square(vEndB[1]))
                    vEndBDist = [(vEndB[0] / vEndBLen) * dist, (vEndB[1] / vEndBLen) * dist]

                    # Punkte und Linien zum Mittelpunkt, um Pufferdistanz nach außen verschoben
                    ptMidB1 = [ptMid[0] + vStartBDist[0], ptMid[1] + vStartBDist[1], ptMid[2]]
                    ptMidB2 = [ptMid[0] + vEndBDist[0], ptMid[1] + vEndBDist[1], ptMid[2]]
                    b1Line = Line(Point3D(ptMidB1[0], ptMidB1[1], ptMidB1[2]),
                                  Point3D(ptMidB1[0] + (ptMid[0] - ptSt[0]), ptMidB1[1] + (ptMid[1] - ptSt[1]),
                                          ptMidB1[2]))
                    b2Line = Line(Point3D(ptMidB2[0], ptMidB2[1], ptMidB2[2]),
                                  Point3D(ptMidB2[0] + (ptEnd[0] - ptMid[0]), ptMidB2[1] + (ptEnd[1] - ptMid[1]),
                                          ptMidB2[2]))

                    # Schnittpunkt: Neuer Mittelpunkt
                    sPoint = b1Line.intersection(b2Line)[0]
                    ringBuffer.AddPoint(float(sPoint[0]), float(sPoint[1]), ptMidB1[2])

                # Abschließen der Geometrie
                ringBuffer.CloseRings()
                geomBuffer.AddGeometry(ringBuffer)
                if geomBuffer.GetGeometryRef(0).GetPointCount() > 3:
                    bufferList.append(geomBuffer)

        # Rückgabe
        if len(bufferList) == 0:
            return None
        elif len(bufferList) == 1:
            return bufferList[0]
        else:
            return bufferList
