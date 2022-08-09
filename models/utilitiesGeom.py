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
            distTol: Die erlaubte Toleranz bei der Vereinfachung der Punktnähe (in Einheit der Geometrie)
            angTol: Die erlaubte Toleranz bei der Vereinfachung von Punkten auf vorhandenen Linien
            zd: Ob nur zweidimensional vereinfacht werden soll
                default: False

        Returns:
            Die vereinfachte Geometrie, einzeln oder als Liste, oder None falls ungültig
        """
        supported = ["POLYGON", "LINESTRING", "MULTILINESTRING"]
        geomList = geom if isinstance(geom, list) else [geom]
        simpList = []

        for geom in geomList:

            # UNGÜLTIG #
            if geom is None or geom.IsEmpty() or geom.GetGeometryName() not in supported:
                return geom

            # POLYGON oder LINESTRING #
            elif geom.GetGeometryName() == "POLYGON" or geom.GetGeometryName() == "LINESTRING":
                # Auslesen der Geometrie und Erstellen der neuen Geometrie
                if geom.GetGeometryName() == "POLYGON":
                    geomNew = ogr.Geometry(ogr.wkbPolygon)
                    ring0 = geom.GetGeometryRef(0)
                ringCount = geom.GetGeometryCount() if geom.GetGeometryName() == "POLYGON" else 1
                count = ring0.GetPointCount() if geom.GetGeometryName() == "POLYGON" else geom.GetPointCount()

                # Über die verschiedenen Ringe iterieren (falls Polygone Löcher haben)
                for h in range(0, ringCount):
                    ring = geom.GetGeometryRef(h) if geom.GetGeometryName() == "POLYGON" else geom
                    ringNew = ogr.Geometry(ogr.wkbLinearRing) if geom.GetGeometryName() == "POLYGON" else ogr.Geometry(
                        ogr.wkbLineString)

                    # Anfangspunkt
                    ringNew.AddPoint(ring.GetPoint(0)[0], ring.GetPoint(0)[1], ring.GetPoint(0)[2])
                    ptSt = ring.GetPoint(0)

                    # Vereinfachung: Betrachtung von drei Punkten hintereinander
                    for i in range(2, ring.GetPointCount()):
                        ptEnd, ptMid = ring.GetPoint(i), ring.GetPoint(i - 1)

                        # Abstand zwischen erstem und mittlerem Punkt: Unter Toleranz = Überspringen
                        sqXY = np.square(ptMid[0] - ptSt[0]) + np.square(ptMid[1] - ptSt[1])
                        dist = np.sqrt(sqXY) if zd else np.sqrt(sqXY + np.square(ptMid[2] - ptSt[2]))
                        if dist < distTol:
                            continue

                        # Parallelität der Linien von Startpunkt zu Mittelpunkt und Mittelpunkt zu Endpunkt prüfen
                        tol = angTol
                        # Y-Steigung in Bezug auf X-Verlauf
                        gradYSt = -1 if ptMid[0] - ptSt[0] == 0 else (ptMid[1] - ptSt[1]) / (ptMid[0] - ptSt[0])
                        gradYEnd = -1 if ptEnd[0] - ptMid[0] == 0 else (ptEnd[1] - ptMid[1]) / (ptEnd[0] - ptMid[0])
                        if gradYSt - tol < gradYEnd < gradYSt + tol:
                            # Z-Steigung in Bezug auf X-Verlauf
                            gradZSt = -1 if ptMid[0] - ptSt[0] == 0 else (ptMid[2] - ptSt[2]) / (ptMid[0] - ptSt[0])
                            gradZEnd = -1 if ptEnd[0] - ptMid[0] == 0 else (ptEnd[2] - ptMid[2]) / (
                                ptEnd[0] - ptMid[0])
                            if gradZSt - tol < gradZEnd < gradZSt + tol:
                                # Z-Steigung in Bezug auf Y-Verlauf
                                gradYZSt = -1 if ptMid[1] - ptSt[1] == 0 else (ptMid[2] - ptSt[2]) / (
                                    ptMid[1] - ptSt[1])
                                gradYZEnd = -1 if ptEnd[1] - ptMid[1] == 0 else (ptEnd[2] - ptMid[2]) / (
                                    ptEnd[1] - ptMid[1])
                                if gradYZSt - tol < gradYZEnd < gradYZSt + tol:
                                    continue

                        # Wenn keine Vereinfachung: Mittelpunkt setzen
                        ringNew.AddPoint(ptMid[0], ptMid[1], ptMid[2])
                        ptSt = ptMid

                    # Abschließen der Geometrie
                    if geom.GetGeometryName() == "POLYGON":
                        ringNew.CloseRings()
                        geomNew.AddGeometry(ringNew)
                    else:
                        ptLineEnd = geom.GetPoint(geom.GetPointCount() - 1)
                        ringNew.AddPoint(ptLineEnd[0], ptLineEnd[1], ptLineEnd[2])
                        geomNew = ringNew
                ringTest = geomNew.GetGeometryRef(0) if geom.GetGeometryName() == "POLYGON" else geomNew

                # Wenn Polygon weniger als vier Eckpunkte hat: Eigentlich ein LineString
                if ringTest.GetPointCount() < 4 and geom.GetGeometryName() == "POLYGON":
                    geomNewLine = ogr.Geometry(ogr.wkbLineString)
                    geomNewLine.AddPoint(ringTest.GetPoint(0)[0], ringTest.GetPoint(0)[1], ringTest.GetPoint(0)[2])
                    geomNewLine.AddPoint(ringTest.GetPoint(1)[0], ringTest.GetPoint(1)[1], ringTest.GetPoint(1)[2])
                    simpList.append(geomNewLine)

                # Wenn es noch weiter vereinfacht werden kann: Iterativer Vorgang über rekursive Aufrufe
                elif ringTest.GetPointCount() < count:
                    simpList.append(UtilitiesGeom.simplify(geomNew, distTol, angTol))

                # Wenn fertig: Zurückgeben
                else:
                    simpList.append(geomNew)

            # MULTILINESTRING #
            else:
                count = geom.GetGeometryCount()
                geomNew = ogr.Geometry(ogr.wkbMultiLineString)
                skip = False
                for i in range(0, geom.GetGeometryCount()):
                    if skip:
                        continue
                    line = geom.GetGeometryRef(i)
                    if i != geom.GetGeometryCount() - 1 and line.GetPoint(
                            line.GetPointCount() - 1) == geom.GetGeometryRef(i + 1).GetPoint(0):
                        lineNext = geom.GetGeometryRef(i + 1)
                        lineNew = ogr.Geometry(ogr.wkbLineString)
                        for j in range(0, line.GetPointCount()):
                            lineNew.AddPoint(line.GetPoint(j)[0], line.GetPoint(j)[1], line.GetPoint(j)[2])
                        for j in range(1, lineNext.GetPointCount()):
                            lineNew.AddPoint(lineNext.GetPoint(j)[0], lineNext.GetPoint(j)[1], lineNext.GetPoint(j)[2])
                        skip = True
                        geomNew.AddGeometry(lineNew)
                    else:
                        lineNew = ogr.Geometry(ogr.wkbLineString)
                        for j in range(0, line.GetPointCount()):
                            lineNew.AddPoint(line.GetPoint(j)[0], line.GetPoint(j)[1], line.GetPoint(j)[2])
                        skip = False
                        geomNew.AddGeometry(lineNew)

                # Wenn MultiLineString weniger als vier Eckpunkte hat: Eigentlich ein LineString
                if geomNew.GetGeometryCount() == 1:
                    geomLine = geomNew.GetGeometryRef(0)
                    geomNewLine = ogr.Geometry(ogr.wkbLineString)
                    for j in range(0, geomLine.GetPointCount()):
                        geomNewLine.AddPoint(geomLine.GetPoint(0)[0], geomLine.GetPoint(0)[1], geomLine.GetPoint(0)[2])
                    simpList.append(geomNewLine)

                # Wenn es noch weiter vereinfacht werden kann: Iterativer Vorgang über rekursive Aufrufe
                elif geomNew.GetGeometryCount() < count:
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
        geomsOut, done = [], []

        # Alle Geometrie miteinander auf Berührung testen
        for i in range(0, len(geomsIn)):

            # Testen, ob die Geometrien in diesem Durchlauf zur Vereinigung genutzt wurden und ob sie valide sind
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

                # Auf Parallität prüfen
                geom1Simp = UtilitiesGeom.simplify(geom1, 0.001, 0.0001)
                geom2Simp = UtilitiesGeom.simplify(geom2, 0.001, 0.0001)
                ring1Simp, ring2Simp = geom1Simp.GetGeometryRef(0), geom2Simp.GetGeometryRef(0)
                pt11, pt12, pt13 = ring1Simp.GetPoint(0), ring1Simp.GetPoint(1), ring1Simp.GetPoint(2)
                pt21, pt22, pt23 = ring2Simp.GetPoint(0), ring2Simp.GetPoint(1), ring2Simp.GetPoint(2)
                r11 = [pt12[0] - pt11[0], pt12[1] - pt11[1], pt12[2] - pt11[2]]
                r12 = [pt13[0] - pt11[0], pt13[1] - pt11[1], pt13[2] - pt11[2]]
                r21 = [pt22[0] - pt21[0], pt22[1] - pt21[1], pt22[2] - pt21[2]]
                r22 = [pt23[0] - pt21[0], pt23[1] - pt21[1], pt23[2] - pt21[2]]
                norm1, norm2 = np.cross(r11, r12), np.cross(r21, r22)
                unit1, unit2 = norm1 / np.linalg.norm(norm1), norm2 / np.linalg.norm(norm2)
                unit2Neg = np.negative(unit2)
                tol = 0.0001
                if UtilitiesGeom.isEqual(unit1, unit2, tol) or UtilitiesGeom.isEqual(unit1, unit2Neg, tol):

                    # Alle Eckpunkte miteinander vergleichen
                    samePts = []
                    firstK, lastK = None, None
                    ks, ms = [], []
                    for k in range(0, ring1.GetPointCount() - 1):
                        for m in range(0, ring2.GetPointCount() - 1):
                            if ring1.GetPoint(k) == ring2.GetPoint(m):
                                if firstK is None:
                                    firstK = k
                                lastK = k
                                ks.append(k)
                                if m not in ms:
                                    ms.append(m)
                                samePts.append(ring1.GetPoint(k))

                    # Wenn mehrere gleiche Punkte gefunden
                    if len(samePts) > 1:

                        # Vereinigungs-Geometrie erstellen
                        geometry, ring = ogr.Geometry(ogr.wkbPolygon), ogr.Geometry(ogr.wkbLinearRing)

                        # Testen, ob alle übereinstimmenden Eckpunkte hintereinander liegen
                        if len(samePts) > 2:
                            row = True
                            if firstK == 0 and lastK == ring1.GetPointCount() - 2:
                                for p in range(0, len(ks) - 1):
                                    if ks[p] + 1 != ks[p + 1]:
                                        for q in range(p + 1, len(ks)):
                                            if q + 1 != len(ks) and ks[q] + 1 != ks[q + 1]:
                                                row = False
                                                break
                                        break
                            else:
                                if firstK + len(samePts) - 1 != lastK:
                                    row = False

                            if row:
                                ms.sort()
                                print("ms: " + str(ms))
                                if ms[0] == 0 and ms[-1] == ring2.GetPointCount()-2:
                                    jumps = 0
                                    for p in range(1, len(ms)):
                                        if ms[p-1] + 1 != ms[p]:
                                            jumps += 1
                                    if jumps > 1:
                                        row = False
                                else:
                                    if ms[0] + len(ms) - 1 != ms[len(ms)-1]:
                                        row = False
                                print("row: " + str(row))

                        # Normalfall: Zwei Polygone grenzen mit einer Schnittgeraden aneinander
                        if len(samePts) < 3 or row:
                            for k in range(0, ring1.GetPointCount() - 1):
                                point1 = ring1.GetPoint(k)

                                if point1 in samePts and k != firstK and k!= lastK:
                                    continue
                                
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

                            # Geometrie abschließen und Löcher aus Ursprungsgeometrie übernehmen
                            ring.CloseRings()
                            geometry.AddGeometry(ring)
                            for m in range(1, geom1.GetGeometryCount()):
                                geometry.AddGeometry(geom1.GetGeometryRef(m))
                            for n in range(1, geom2.GetGeometryCount()):
                                geometry.AddGeometry(geom2.GetGeometryRef(n))
                            geomsOut.append(geometry)
                            
                            lastPt = None
                            for o in range(0, ring.GetPointCount()):
                                pt = ring.GetPoint(o)
                                if lastPt is not None:
                                    if abs(pt[2] - lastPt[2]) > 2.3 and abs(pt[0] - lastPt[0]) > 10:
                                        print("HIER")
                                        print(geometry)
                                        print(geom1)
                                        print(geom2)
                                        # TODO: Mit diesen Flächen passiert was komisches
                                lastPt = pt
                            
                            done.append(i)
                            done.append(j)
                            break

                        # Spezialfall: Loch zwischen den beiden Polygonen
                        else:
                            # Höhere Geometrie herausfinden, ggf. tauschen
                            maxHeightX, maxHeightY = -sys.maxsize, -sys.maxsize
                            maxHeightXK, maxHeightYK = None, None
                            for x in range(0, ring1.GetPointCount() - 1):
                                pt = ring1.GetPoint(x)
                                if pt[2] > maxHeightX:
                                    maxHeightX = pt[2]
                                    maxHeightXK = x
                            for y in range(0, ring2.GetPointCount() - 1):
                                pt = ring2.GetPoint(y)
                                if pt[2] > maxHeightY:
                                    maxHeightY = pt[2]
                                    maxHeightYK = y
                            maxHeightK = maxHeightXK if maxHeightX >= maxHeightY else maxHeightYK
                            if maxHeightX < maxHeightY:
                                geom1, geom2 = geom2, geom1
                                ring1, ring2 = ring2, ring1

                            # Neue Löcher finden
                            # Liste aller Kontaktpunkte machen
                            sameKMs = []
                            for k in range(0, ring1.GetPointCount() - 1):
                                point1 = ring1.GetPoint(k)
                                if point1 in samePts:
                                    for m in range(0, ring2.GetPointCount() - 1):
                                        point2 = ring2.GetPoint(m)
                                        if point2 == point1:
                                            sameKMs.append([k, m])

                            # Kontaktpunkt-Differenz ohne Schnitt dazwischen
                            ringsHole = []
                            for r in range(0, len(sameKMs)):
                                currKM = sameKMs[r]
                                lastKM = sameKMs[len(sameKMs) - 1] if r == 0 else sameKMs[r - 1]
                                kDiff = currKM[0] - lastKM[0] if currKM[0] > lastKM[0] \
                                    else ring1.GetPointCount() - lastKM[0] + currKM[0] - 1
                                mDiff = abs(currKM[1] - lastKM[1]) if currKM[1] < lastKM[1] \
                                    else ring2.GetPointCount() - currKM[1] + lastKM[1] - 1
                                if kDiff != mDiff or kDiff > 1:

                                    # Loch-Geometrie erstellen
                                    ringHole = ogr.Geometry(ogr.wkbLinearRing)
                                    # Erste Geometrie entlang gehen, dann zweite
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

                                    # Loch-Geometrie abschließen
                                    ringHole.CloseRings()
                                    ringsHole.append(ringHole)

                            # Eigentliche Geometrie erstellen
                            fin, startK = False, maxHeightK
                            while True:
                                if not fin:
                                    for k in range(startK, ring1.GetPointCount() - 1):
                                        point1 = ring1.GetPoint(k)
                                        ring.AddPoint(point1[0], point1[1], point1[2])

                                        # Wenn gleicher Eckpunkt: Anbinden der zweiten Geometrie
                                        if point1 in samePts and k != maxHeightK:
                                            for m in range(0, ring2.GetPointCount() - 1):
                                                point2 = ring2.GetPoint(m)
                                                if point2 == point1:
                                                    stop = False
                                                    rangeS, rangeE = m + 1, ring2.GetPointCount()
                                                    while True:
                                                        for n in range(rangeS, rangeE):
                                                            point3 = ring2.GetPoint(n)
                                                            if point3 == ring1.GetPoint(maxHeightK):
                                                                stop = True
                                                                break
                                                            ring.AddPoint(point3[0], point3[1], point3[2])
                                                            if point3 in samePts:
                                                                for p in range(0, ring1.GetPointCount() - 1):
                                                                    point4 = ring1.GetPoint(p)
                                                                    if point3 == point4:
                                                                        if p <= maxHeightK:
                                                                            for q in range(p + 1, maxHeightK):
                                                                                point5 = ring1.GetPoint(q)
                                                                                ring.AddPoint(point5[0], point5[1],
                                                                                              point5[2])
                                                                        else:
                                                                            for q in range(p + 1,
                                                                                           ring1.GetPointCount() - 1):
                                                                                point5 = ring1.GetPoint(q)
                                                                                ring.AddPoint(point5[0], point5[1],
                                                                                              point5[2])
                                                                            for q in range(0, maxHeightK):
                                                                                point5 = ring1.GetPoint(q)
                                                                                ring.AddPoint(point5[0], point5[1],
                                                                                              point5[2])
                                                                        break
                                                                stop = True
                                                                break
                                                        if stop:
                                                            break
                                                        else:
                                                            stop = True
                                                            rangeS, rangeE = 0, m
                                            fin = True
                                            break
                                    startK = 0
                                else:
                                    break

                            # Geometrie abschließen und Löcher der ursprünglichen Geometrien hinzufügen
                            ring.CloseRings()
                            geometry.AddGeometry(ring)
                            for m in range(1, geom1.GetGeometryCount()):
                                geometry.AddGeometry(geom1.GetGeometryRef(m))
                            for n in range(1, geom2.GetGeometryCount()):
                                geometry.AddGeometry(geom2.GetGeometryRef(n))

                            # Neue Löcher hinzufügen
                            for ringHole in ringsHole:
                                if not ring.Length() - 0.00001 < ringHole.Length() < ring.Length() + 0.00001:
                                    geometry.AddGeometry(ringHole)
                            geomsOut.append(geometry)
                            done.append(i)
                            done.append(j)
                            break

                    else:
                        # Prüfen, ob Fläche innerhalb eines Loches ist: ggf. aus Loch entfernen
                        found = False
                        # Über alle Löcher gehen
                        for h in range(1, geom1.GetGeometryCount()):
                            innerRing1 = geom1.GetGeometryRef(h)

                            # Alle Eckpunkte miteinander vergleichen
                            samePts = []
                            firstK, lastK = None, None
                            ks = []
                            for k in range(0, innerRing1.GetPointCount() - 1):
                                for m in range(0, ring2.GetPointCount() - 1):
                                    if innerRing1.GetPoint(k) == ring2.GetPoint(m):
                                        if firstK is None:
                                            firstK = k
                                        lastK = k
                                        ks.append(k)
                                        samePts.append(innerRing1.GetPoint(k))

                            # Wenn min. zwei gleiche Eckpunkte gefunden: Neue Lochgeometrie erzeugen
                            if len(samePts) > 1:
                                newRing = ogr.Geometry(ogr.wkbLinearRing)
                                for n in range(0, innerRing1.GetPointCount()):
                                    point1 = innerRing1.GetPoint(n)
                                    newRing.AddPoint(point1[0], point1[1], point1[2])
                                    if point1 in samePts:
                                        for o in range(0, ring2.GetPointCount()):
                                            point2 = ring2.GetPoint(o)
                                            if point2 == point1:
                                                stop = False
                                                for p in range(o+1, ring2.GetPointCount()):
                                                    point3 = ring2.GetPoint(p)
                                                    if point3 in samePts:
                                                        stop = True
                                                        break
                                                    else:
                                                        newRing.AddPoint(point3[0], point3[1], point3[2])
                                                if not stop:
                                                    for q in range(0, o):
                                                        point3 = ring2.GetPoint(q)
                                                        if point3 in samePts:
                                                            break
                                                        else:
                                                            newRing.AddPoint(point3[0], point3[1], point3[2])

                                # Geometrie abschließen und hinzufügen
                                newRing.CloseRings()
                                newGeom1 = ogr.Geometry(ogr.wkbPolygon)
                                for n in range(0, geom1.GetGeometryCount()):
                                    ring = newRing if n == h else geom1.GetGeometryRef(n)
                                    newGeom1.AddGeometry(ring)
                                geomsOut.append(newGeom1)

                                # Weiteres Vorgehen abbrechen
                                done.append(i)
                                done.append(j)
                                found = True
                                break
                            if found:
                                break
                        if found:
                            break
            # Wenn keine berührende Geometrie gefunden
            if i not in done:
                done.append(i)
                geomsOut.append(geomsIn[i])

        # Wenn es noch weiter vereinigt werden kann: Iterativer Vorgang über rekursive Aufrufe
        if len(geomsOut) < len(geomsIn) and count < 3:
            return UtilitiesGeom.union3D(geomsOut, count+1)

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

    @staticmethod
    def isEqual(pt1, pt2, tol):
        """ Prüfen auf Gleichheit zweier Punkte, mit gegebener Toleranz

        Args:
            pt1: Erster Punkt, der verglichen werden soll
            pt2: Zweiter Punkt, der verglichen werden soll
            tol: Toleranz, um die die beiden Punkte verschieden sein dürfen

        Returns:
            Ob die Punkte gleich sind oder nicht, als Boolean
        """
        return pt1[0] - tol < pt2[0] < pt1[0] + tol and pt1[1] - tol < pt2[1] < pt1[1] + tol and \
               pt1[2] - tol < pt2[2] < pt1[2] + tol
