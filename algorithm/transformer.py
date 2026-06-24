# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (09.09.2022)
 ***************************************************************************/
"""

#####

# Standard-Bibliotheken
import math
import re
from dataclasses import dataclass, field
import numpy as np
from typing import Optional

# QGIS-Bibliotheken
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsMessageLog,
    QgsPoint,
    Qgis,
)
from qgis.PyQt.QtCore import QCoreApplication
from osgeo import osr

#####

# Gauss-Krueger-Zone -> EPSG-Zuordnung (DHDN-basiert)
GK_EPSG = {2: 31466, 3: 31467, 4: 31468, 5: 31469}

# Datenklasse zur Speicherung der Georeferenzierungsinformationen
@dataclass
class GeoRefResult:
    level: int = 0
    epsg: Optional[int] = None
    crs_name: Optional[str] = None
    eastings: Optional[float] = None
    northings: Optional[float] = None
    height: Optional[float] = None
    x_axis_abscissa: Optional[float] = None
    x_axis_ordinate: Optional[float] = None
    scale: Optional[float] = None
    true_north: Optional[list] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    address: Optional[dict] = field(default_factory=dict)
    source: str = ""
    guessed_crs: Optional[str] = None


class Transformer:
    """Modell-Klasse zum Transformieren vom lokalen in ein projiziertes Koordinatensystem.

    IFC speichert Geometrie in einem lokalen kartesischen Modellkoordinatensystem
    (IfcCartesianPoint, IfcDirection, IfcLocalPlacement). Eine globale Verortung ist
    optional und kommt entweder ueber IfcSite.RefLatitude/RefLongitude (grob) oder
    praezise ueber IfcMapConversion + IfcProjectedCRS.

    """

    # Konstruktor und Einstiegspunkte 
    @staticmethod
    def tr(msg):
        return QCoreApplication.translate('Transformer', msg)

    def __init__(self, ifc, targetCrs=None, sourceEpsgOverride=None, task=None):
        """Konstruktor der Modell-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien.

        Args:
            ifc: Die zugrunde liegende IFC-Datei.
            targetCrs: Ziel-CRS des projizierten Koordinatensystems. Kann als EPSG-Code,
                als CRS-String oder als osgeo.osr.SpatialReference uebergeben werden.
            sourceEpsgOverride: Optionaler EPSG-Code, der das automatisch erkannte Quell-CRS
                ueberschreibt.
            task: Optionales Task-Objekt fuer Logging-Signale.
        """
        # Attribute initialisieren
        self.ifc = ifc
        self.task = task

        self._warn_if_non_meter_unit()

        self.sourceEpsgOverride = sourceEpsgOverride

        # Georeferenzierung ermitteln und loggen
        self.georef = self.check_georef()
        
        if self.sourceEpsgOverride is not None:
            self.georef.epsg = self.sourceEpsgOverride
            
        self.sourceCrs = self.georef.epsg
        
        self._log(
            self.tr("Georef result: Level={level}, Source CRS={src_crs}, Source={source}, Guessed CRS={guessed}").format(
                level=self.georef.level,
                src_crs=self.sourceCrs,
                source=self.georef.source,
                guessed=self.georef.guessed_crs,
            )
        )

        if targetCrs is None:
            raise ValueError(
                "No target CRS specified. "
                f"Detected source CRS: EPSG:{self.sourceCrs} "
                f"(Level {self.georef.level}, {self.georef.source})"
            )

        self.targetCrs = targetCrs
        self.epsg = self.targetCrs

        # Transformationsparameter berechnen
        self.metricCrs = self._resolve_to_metric_crs()
        self.originShift = self.getOriginShift()
        self.trans = self.getTransformMatrix()
        self.originShiftArray = np.asarray(self.originShift, dtype=float)
        self.transArray = np.asarray(self.trans, dtype=float)

        # OSR-Transformation fuer metrisches -> Ziel-CRS vorberechnen
        self._metricOsr = self._make_osr_srs(self.metricCrs) if self.metricCrs is not None else None
        self._targetOsr = self._make_osr_srs(self.targetCrs)

        if self._metricOsr is None:
            raise ValueError(f"Ungueltiges metrisches Koordinatensystem: EPSG:{self.metricCrs}")
        if self._targetOsr is None:
            raise ValueError(f"Ungueltiges Ziel-Koordinatensystem: {self.targetCrs}")

        self._needsReproject = not bool(self._metricOsr.IsSame(self._targetOsr))
        self._osrTransform = (
            osr.CoordinateTransformation(self._metricOsr, self._targetOsr)
            if self._needsReproject
            else None
        )

    def check_georef(self) -> GeoRefResult:
        """Ermittelt den Georeferenzierungslevel der IFC-Datei (LoGeoRef 50 -> 10).

        Die IFC-Modellgeometrie bleibt lokal kartesisch; hier werden nur die optionalen
        Georeferenzierungsangaben ausgewertet (IfcMapConversion/IfcProjectedCRS fuer
        eine praezise Zuordnung oder IfcSite RefLatitude/RefLongitude fuer eine grobe Lage).

        Returns:
            GeoRefResult mit Level, EPSG und Quellinformationen.
        """
        result = self._check_logeoref50()
        if result and result.epsg is not None:
            return result

        result = self._check_logeoref40(result)
        if result and result.level == 40:
            return result

        result = self._check_logeoref30(result)
        if result and result.level == 30:
            return result

        result = self._check_logeoref20(result)
        if result and result.epsg is not None:
            return result

        result = self._check_logeoref10(result)
        if result and result.level == 10:
            return result

        return result if result else GeoRefResult(source="not georeferenced")

    @classmethod
    def check_georef_static(cls, ifc) -> GeoRefResult:
        """Klassenmethode fuer check_georef() – kann ohne vollstaendige Transformer-Instanz
        aufgerufen werden. Wird vom IfcAnalyzer genutzt, um den Georeferenzierungslevel
        vor der Transformation zu ermitteln.

        Args:
            ifc: Die zu pruefende IFC-Datei.

        Returns:
            GeoRefResult mit Level, EPSG und Quellinformationen.
        """
        checker = object.__new__(cls)
        checker.ifc = ifc
        checker.task = None
        return checker.check_georef()

    # Kern-Methoden 
    def _resolve_to_metric_crs(self) -> Optional[int]:
        """Ermittelt ein metrisches CRS fuer die Transformation.

        Returns:
            EPSG-Code des metrischen CRS oder None, wenn nicht ermittelbar.
        """
        g = self.georef

        if self.sourceCrs is None:
            if self._looks_like_metric_xy(g.eastings, g.northings):
                return self.targetCrs if isinstance(self.targetCrs, int) else None
            return None

        src_srs = self._make_osr_srs(self.sourceCrs)
        if src_srs is None:
            return self.sourceCrs

        # Quell-CRS ist bereits metrisch -> direkt verwenden
        if not src_srs.IsGeographic():
            return self.sourceCrs

        # Geographisches Quell-CRS -> passendes UTM ableiten
        if g.lat is not None and g.lon is not None:
            return self._utm_epsg_from_latlon(g.lat, g.lon)

        site = self.ifc.by_type("IfcSite")[0]
        lat = self.mergeDegrees(site.RefLatitude)
        lon = self.mergeDegrees(site.RefLongitude)
        return self._utm_epsg_from_latlon(lat, lon)

    def getOriginShift(self) -> list:
        """Berechnet die Ursprungsverschiebung zwischen Quell- und Zielkoordinatensystem.

        Returns:
            Die Verschiebung als Vektor [x, y, z].
        """
        g = self.georef

        if g.level == 20 and g.lat is not None and g.lon is not None:
            # Geographische Koordinaten aus LoGeoRef 20
            src_x, src_y = g.lon, g.lat
        elif g.eastings is not None and g.northings is not None:
            src_x, src_y = g.eastings, g.northings
        else:
            # Fallback: Koordinaten direkt aus IfcSite lesen
            sites = self.ifc.by_type("IfcSite")
            if not sites:
                self._log(self.tr("Warning: No IfcSite found – origin shift is [0, 0, 0]."), Qgis.Warning)
                return [0.0, 0.0, 0.0]
            site = sites[0]
            src_x = self.mergeDegrees(site.RefLongitude)
            src_y = self.mergeDegrees(site.RefLatitude)

        src_z = g.height if g.height is not None else 0.0

        self._log(self.tr("Target CRS: {crs}").format(crs=self.targetCrs))

        # Quell- und metrisches CRS sind identisch -> keine Transformation noetig
        if self.sourceCrs == self.metricCrs and self.sourceCrs is not None:
            return [src_x, src_y, src_z]

        # Nur affine Transformation moeglich, kein OSR-Zugriff
        if not isinstance(self.sourceCrs, int) or not isinstance(self.metricCrs, int):
            return [src_x, src_y, src_z]

        # OSR-Punkttransformation
        pt = self._transform_point(src_x, src_y, src_z, self.sourceCrs, self.metricCrs)
        return [pt.x(), pt.y(), pt.z()]

    def getTransformMatrix(self):
        """Berechnet die Transformationsmatrix zwischen dem lokalen und dem globalen Koordinatensystem.

        Returns:
            Die Transformationsmatrix als NumPy-Array.
        """
        g = self.georef
        if (
            g.level == 50
            and g.x_axis_abscissa is not None
            and g.x_axis_ordinate is not None
        ):
            a = g.x_axis_abscissa
            b = g.x_axis_ordinate
            scale = g.scale if g.scale not in (None, 0) else 1.0
            
            transform_matrix = [
                [a * scale,  b * scale, 0],
                [-b * scale, a * scale, 0],
                [0,          0,         1],
            ]
            return np.asarray(transform_matrix)

        # TrueNorth aus dem Modell-Kontext lesen
        project = self.ifc.by_type("IfcProject")[0]
        context_for_model = self._get_model_context(project)
        tn = getattr(context_for_model, "TrueNorth", None)
        if tn and getattr(tn, "DirectionRatios", None):
            a = tn.DirectionRatios[0]
            b = tn.DirectionRatios[1]
        else:
            a, b = 0.0, 1.0

        # Inverse der TrueNorth-Rotationsmatrix
        transform_matrix = np.linalg.inv(np.asarray([[b, -a, 0], [a, b, 0], [0, 0, 1]]))
        return transform_matrix

    # Transformation 
    def georeferencePoint(self, point, reproject=True) -> np.ndarray:
        """Georeferenziert einen Punkt oder mehrere Punkte.

        Args:
            point: Lokaler IFC-Punkt als (x, y, z) oder Array mit Form (n, 3).
            reproject: Wenn False, erfolgt nur die Transformation ins metrische CRS.

        Returns:
            NumPy-Array der Punkt(e) im Ziel-CRS oder im metrischen CRS.

        Raises:
            ValueError: Wenn die Eingabe keine Form (3,) oder (n, 3) hat.
        """
        arr = np.asarray(point, dtype=float)
        metric = arr @ self.transArray + self.originShiftArray

        if not reproject or not self._needsReproject:
            return metric

        if metric.ndim == 1:
            x, y, z = self._osrTransform.TransformPoint(
                float(metric[0]), float(metric[1]), float(metric[2])
            )
            return np.array([x, y, z], dtype=float)

        if metric.ndim == 2:
            out = np.empty_like(metric, dtype=float)
            for i in range(metric.shape[0]):
                x, y, z = self._osrTransform.TransformPoint(
                    float(metric[i, 0]), float(metric[i, 1]), float(metric[i, 2])
                )
                out[i, 0] = x
                out[i, 1] = y
                out[i, 2] = z
            return out

        raise ValueError(f"Ungueltige Punkt-Form (3,) oder (n,3) erwartet, erhalten: {metric.shape}")

    def reproject_geometry(self, geom):
        """Reprojiziiert eine OGR-Geometrie vom metrischen ins Ziel-CRS.

        Args:
            geom: OGR-Geometrieobjekt oder None.

        Returns:
            Transformierte Geometrie oder None.
        """
        if geom is None:
            return None
        if not self._needsReproject:
            return geom.Clone()

        # Vorberechnete OSR-Transformation wiederverwenden
        out = geom.Clone()
        out.Transform(self._osrTransform)
        return out

    # Georeferenzierungs-Level (hoch -> niedrig)
    def _check_logeoref50(self) -> Optional[GeoRefResult]:
        """LoGeoRef 50: IfcMapConversion + IfcProjectedCRS (IFC4+).

        EPSG wird aus den TargetCRS-Informationen (Name/Beschreibung) abgeleitet.

        Returns:
            GeoRefResult oder None, wenn kein IfcMapConversion vorhanden.
        """
        try:
            conversions = self.ifc.by_type("IfcMapConversion")
        except RuntimeError as e:
            self._log(self.tr("Could not read IfcMapConversion: {error}").format(error=e), Qgis.Warning)
            conversions = None

        if not conversions:
            return None

        conv = conversions[0]
        res = GeoRefResult(level=50, source="IfcMapConversion")
        res.eastings = getattr(conv, "Eastings", None)
        res.northings = getattr(conv, "Northings", None)
        res.height = getattr(conv, "OrthogonalHeight", None)
        res.x_axis_abscissa = getattr(conv, "XAxisAbscissa", None)
        res.x_axis_ordinate = getattr(conv, "XAxisOrdinate", None)
        res.scale = getattr(conv, "Scale", None)

        target_crs = getattr(conv, "TargetCRS", None)
        if target_crs:
            crs_name = getattr(target_crs, "Name", None)
            res.crs_name = crs_name
            res.epsg = self._parse_epsg_from_name(crs_name)

        # Falls kein EPSG aus Name ableitbar, heuristisch aus Koordinaten schaetzen
        if not res.epsg and res.eastings is not None:
            res.guessed_crs, res.epsg = self._guess_epsg_from_coords(res.eastings, res.northings)

        return res

    def _check_logeoref40(self, prev: Optional[GeoRefResult]) -> Optional[GeoRefResult]:
        """LoGeoRef 40: WorldCoordinateSystem + TrueNorth aus dem Modell-Kontext.

        Args:
            prev: Vorheriges Ergebnis (wird zurueckgegeben, wenn kein Level-40-Fund).

        Returns:
            GeoRefResult (Level 40) oder prev.
        """
        project = self._get_project()
        if not project:
            return prev

        context = self._get_model_context(project)
        if not context:
            return prev

        wcs = getattr(context, "WorldCoordinateSystem", None)
        if not wcs:
            return prev

        loc = getattr(wcs, "Location", None)
        if not loc:
            return prev

        coords = list(loc.Coordinates)
        if all(c == 0.0 for c in coords):
            return prev

        res = GeoRefResult(level=40, source="IfcGeometricRepresentationContext")
        res.eastings = coords[0] if len(coords) > 0 else None
        res.northings = coords[1] if len(coords) > 1 else None
        res.height = coords[2] if len(coords) > 2 else None

        tn = getattr(context, "TrueNorth", None)
        if tn:
            res.true_north = list(tn.DirectionRatios)

        res.guessed_crs, res.epsg = self._guess_epsg_from_coords(res.eastings, res.northings)
        return res

    def _check_logeoref30(self, prev: Optional[GeoRefResult]) -> Optional[GeoRefResult]:
        """LoGeoRef 30: Absolutes IfcLocalPlacement des IfcSite.

        Args:
            prev: Vorheriges Ergebnis (wird zurueckgegeben, wenn kein Level-30-Fund).

        Returns:
            GeoRefResult (Level 30) oder prev.
        """
        sites = self.ifc.by_type("IfcSite")
        if not sites:
            return prev

        site = sites[0]
        placement = getattr(site, "ObjectPlacement", None)
        if not placement:
            return prev

        # Nur absolutes Placement beruecksichtigen (kein PlacementRelTo)
        if getattr(placement, "PlacementRelTo", None) is not None:
            return prev

        rel = getattr(placement, "RelativePlacement", None)
        if not rel:
            return prev

        loc = getattr(rel, "Location", None)
        if not loc:
            return prev

        coords = list(loc.Coordinates)
        if all(c == 0.0 for c in coords):
            return prev

        res = GeoRefResult(level=30, source="IfcLocalPlacement (IfcSite)")
        res.eastings = coords[0] if len(coords) > 0 else None
        res.northings = coords[1] if len(coords) > 1 else None
        res.height = coords[2] if len(coords) > 2 else None

        res.guessed_crs, res.epsg = self._guess_epsg_from_coords(res.eastings, res.northings)
        return res

    def _check_logeoref20(self, prev: Optional[GeoRefResult]) -> Optional[GeoRefResult]:
        """LoGeoRef 20: IfcSite RefLatitude / RefLongitude (WGS84).

        Hinweis: Es wird angenommen, dass die Koordinaten in WGS84 vorliegen.

        Args:
            prev: Vorheriges Ergebnis (wird zurueckgegeben, wenn kein Level-20-Fund).

        Returns:
            GeoRefResult (Level 20) oder prev.
        """
        sites = self.ifc.by_type("IfcSite")
        if not sites:
            return prev

        site = sites[0]
        if not getattr(site, "RefLatitude", None):
            return prev

        lat = self.mergeDegrees(site.RefLatitude)
        lon = self.mergeDegrees(site.RefLongitude)

        # None-Rueckgabe von mergeDegrees signalisiert ungueltiges Format
        if lat is None or lon is None:
            return prev

        res = GeoRefResult(level=20, source="IfcSite RefLatitude/RefLongitude")
        res.lat = lat
        res.lon = lon
        res.height = getattr(site, "RefElevation", None)
        res.crs_name = "WGS84"
        res.epsg = 4326
        return res

    def _check_logeoref10(self, prev: Optional[GeoRefResult]) -> Optional[GeoRefResult]:
        """LoGeoRef 10: Adressinformation aus IfcPostalAddress.

        Args:
            prev: Vorheriges Ergebnis (wird zurueckgegeben, wenn kein Level-10-Fund).

        Returns:
            GeoRefResult (Level 10) oder prev.
        """
        for entity_type in ("IfcSite", "IfcBuilding"):
            for entity in self.ifc.by_type(entity_type):
                addr = getattr(entity, "SiteAddress", None) or getattr(
                    entity, "BuildingAddress", None
                )
                if not addr:
                    continue
                res = GeoRefResult(level=10, source=f"IfcPostalAddress ({entity_type})")
                res.address = {
                    "AddressLines": str(getattr(addr, "AddressLines", "")),
                    "PostalCode": str(getattr(addr, "PostalCode", "")),
                    "Town": str(getattr(addr, "Town", "")),
                    "Region": str(getattr(addr, "Region", "")),
                    "Country": str(getattr(addr, "Country", "")),
                }
                return res
        return prev

    # Hilfsmethoden 
    @staticmethod
    def _parse_epsg_from_name(name: Optional[str]) -> Optional[int]:
        """Extrahiert einen EPSG-Code aus einem Text wie 'EPSG:25832'.

        Args:
            name: Text, der einen EPSG-Code enthalten kann.

        Returns:
            EPSG-Code als int oder None, wenn nicht gefunden.
        """
        if not name:
            return None
        match = re.search(r"EPSG[:\s]*(\d+)", name, re.IGNORECASE)
        return int(match.group(1)) if match else None

    @staticmethod
    def _make_osr_srs(crs) -> Optional[osr.SpatialReference]:
        """Erstellt eine OSR-SpatialReference aus einem CRS-Bezeichner oder -Objekt.

        Args:
            crs: CRS-Bezeichner (EPSG int), QGIS-CRS oder OSR-String.

        Returns:
            SpatialReference oder None bei Fehler.
        """
        if crs is None:
            return None

        srs = osr.SpatialReference()
        if isinstance(crs, QgsCoordinateReferenceSystem):
            err = srs.ImportFromWkt(crs.toWkt())
        elif isinstance(crs, int):
            err = srs.ImportFromEPSG(crs)
        else:
            err = srs.SetFromUserInput(str(crs))

        # 0 = OGRERR_NONE (Erfolg); jeder andere Wert signalisiert einen Fehler
        if err != 0:
            return None

        if hasattr(srs, "SetAxisMappingStrategy"):
            srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        return srs

    @staticmethod
    def _transform_point(x: float, y: float, z: float, src_epsg: int, dst_epsg: int) -> QgsPoint:
        """Transformiert einen Punkt zwischen zwei EPSG-Koordinatensystemen.

        Args:
            x: Quell-X (Easting oder Laenge).
            y: Quell-Y (Northing oder Breite).
            z: Quell-Z (Hoehe).
            src_epsg: EPSG-Code des Quell-CRS.
            dst_epsg: EPSG-Code des Ziel-CRS.

        Returns:
            Transformierter Punkt als QgsPoint.
        """
        src = osr.SpatialReference()
        dst = osr.SpatialReference()
        src.ImportFromEPSG(src_epsg)
        dst.ImportFromEPSG(dst_epsg)
        if hasattr(src, "SetAxisMappingStrategy"):
            src.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        if hasattr(dst, "SetAxisMappingStrategy"):
            dst.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        transform = osr.CoordinateTransformation(src, dst)
        tx, ty, tz = transform.TransformPoint(x, y, z)
        return QgsPoint(tx, ty, tz)

    @staticmethod
    def _guess_epsg_from_coords(
        easting: Optional[float],
        northing: Optional[float],
    ) -> tuple[Optional[str], Optional[int]]:
        """Ermittelt heuristisch CRS-Familie und EPSG-Code aus Koordinatenwerten.

        Die Erkennung basiert auf charakteristischen Wertebereichen:
        - WGS84:    |easting| <= 360
        - GK (DHDN): 2.000.000 <= |easting| < 6.000.000 (erste Ziffer = Zone 2-5)
        - UTM mit Zonenpräfix: 10.000.000 <= |easting| < 100.000.000 (erste zwei Ziffern = Zone)
        - UTM ohne Praefix:   100.000 <= |easting| < 1.000.000

        Args:
            easting: Rechtswert zur CRS-Erkennung.
            northing: Hochwert zur Halbkugel-Bestimmung.

        Returns:
            Tupel (crs_bezeichnung, epsg_code) – beide koennen None sein.
        """
        if easting is None or easting == 0:
            return None, None

        abs_x = abs(easting)

        # Geographische Koordinaten (WGS84)
        if abs_x <= 360:
            return "WGS84", 4326

        # Gauss-Krueger (DHDN) – erste Ziffer ist die Streifennummer
        if 2_000_000 <= abs_x < 6_000_000:
            zone = int(str(int(abs_x))[0])
            if 2 <= zone <= 5:
                return f"GK{zone}", GK_EPSG.get(zone)

        # UTM mit kodierter Zone im Easting (z.B. 32XXXXXX -> Zone 32)
        if 10_000_000 <= abs_x < 100_000_000:
            zone = int(str(int(abs_x))[:2])
            if 1 <= zone <= 60:
                label = f"UTM Zone {zone}"
                epsg = (zone + 32700) if (northing is not None and northing < 0) else (zone + 32600)
                return label, epsg

        # Standard-UTM-Easting ohne Zonenkodierung
        if 100_000 <= abs_x < 1_000_000:
            zone = int(round(abs_x / 1_000_000)) or 1
            if 1 <= zone <= 60:
                epsg = (zone + 32700) if (northing is not None and northing < 0) else (zone + 32600)
                return "UTM", epsg
            return "UTM", None

        return None, None

    @staticmethod
    def _utm_epsg_from_latlon(lat: float, lon: float) -> int:
        """Leitet den UTM-EPSG-Code aus Breite und Laenge ab.

        Args:
            lat: Breite in Dezimalgrad.
            lon: Laenge in Dezimalgrad.

        Returns:
            EPSG-Code der UTM-Zone (Nord- oder Suedhalbkugel).
        """
        zone = math.ceil((lon + 180) / 6)
        return (zone + 32600) if lat >= 0 else (zone + 32700)

    @staticmethod
    def _looks_like_degrees_xy(x: Optional[float], y: Optional[float]) -> bool:
        """Prueft heuristisch, ob ein Koordinatenpaar geographische Grad darstellt.

        Args:
            x: Laengenwert (Longitude).
            y: Breitenwert (Latitude).

        Returns:
            True, wenn die Werte im Bereich geographischer Koordinaten liegen.
        """
        if x is None or y is None:
            return False
        return abs(float(x)) <= 360 and abs(float(y)) <= 90

    @staticmethod
    def _looks_like_metric_xy(x: Optional[float], y: Optional[float]) -> bool:
        """Prueft heuristisch, ob ein Koordinatenpaar metrische Werte darstellt.

        Args:
            x: Easting-Wert.
            y: Northing-Wert.

        Returns:
            True, wenn die Werte im Bereich metrischer Koordinaten (UTM oder GK) liegen.
        """
        if x is None or y is None:
            return False
        ax, ay = abs(float(x)), abs(float(y))

        # Offensichtliche Gradangaben ausschliessen
        if ax <= 360 and ay <= 90:
            return False

        # UTM-typischer Bereich
        if 100_000 <= ax <= 900_000 and 0 <= ay <= 10_500_000:
            return True

        # GK-typischer Bereich (Deutschland)
        if 2_000_000 <= ax <= 6_000_000 and 4_000_000 <= ay <= 7_500_000:
            return True

        # Allgemein grosse Zahlenwerte
        return ax > 10_000 and ay > 10_000

    # Allgemeine Hilfsmethode 
    @staticmethod
    def mergeDegrees(degrees) -> Optional[float]:
        """Konvertiert geographische Koordinaten aus dem Sexagesimalformat in das Dezimalformat.

        Args:
            degrees: Geographische Koordinate im Sexagesimalformat als Sequenz
                     mit 3 (Grad, Minuten, Sekunden) oder 4 Elementen
                     (Grad, Minuten, Sekunden, Mikrosekunden).

        Returns:
            Koordinate als Dezimalzahl oder None bei ungueltigem Format.
        """
        if len(degrees) == 4:
            return (
                degrees[0]
                + degrees[1] / 60.0
                + (degrees[2] + degrees[3] / 1_000_000.0) / 3600.0
            )
        if len(degrees) == 3:
            return degrees[0] + degrees[1] / 60.0 + degrees[2] / 3600.0
        return None  # Ungueltiges Format

    # IFC-Navigationshilfsmethoden
    def _get_project(self):
        """Gibt das erste IfcProject der IFC-Datei zurueck oder None.

        Returns:
            IfcProject-Objekt oder None.
        """
        projects = self.ifc.by_type("IfcProject")
        return projects[0] if projects else None

    @staticmethod
    def _get_model_context(project):
        """Gibt den 'Model'-Repraesentation-Kontext des Projekts zurueck.

        Args:
            project: IfcProject-Objekt.

        Returns:
            IfcGeometricRepresentationContext mit ContextType 'Model' oder None.
        """
        for ctx in getattr(project, "RepresentationContexts", []):
            if getattr(ctx, "ContextType", None) == "Model":
                return ctx
        return None

    # Einheitenpruefung 
    def _warn_if_non_meter_unit(self) -> None:
        """Gibt eine Warnung aus, wenn die IFC-Laengeneinheit nicht Meter ist."""
        project = self._get_project()
        if not project:
            return

        units = getattr(project, "UnitsInContext", None)
        if not units:
            return

        for unit in getattr(units, "Units", []):
            if getattr(unit, "UnitType", None) != "LENGTHUNIT":
                continue

            if unit.is_a("IfcSIUnit"):
                name = str(getattr(unit, "Name", "")).strip().strip(".").upper()
                prefix = str(getattr(unit, "Prefix", "")).strip().strip(".").upper()
                if name == "METRE" and prefix in ("", "NONE"):
                    return
                label = f"{prefix}METRE" if name == "METRE" and prefix else name or self.tr("UNKNOWN")
                self._log(
                    self.tr("Warning: IFC length unit is {label}. This implementation expects meters.").format(label=label),
                    Qgis.Warning,
                )
                return

            if unit.is_a("IfcConversionBasedUnit"):
                label = str(getattr(unit, "Name", "")).strip() or "CONVERSION_BASED_UNIT"
                self._log(
                    self.tr("Warning: IFC length unit is {label}. This implementation expects meters.").format(label=label),
                    Qgis.Warning,
                )
                return

            self._log(
                self.tr("Warning: IFC length unit is not IfcSIUnit(METRE). This implementation expects meters."),
                Qgis.Warning,
            )
            return

    # Logging 
    def _log(self, msg: str, level: Qgis.MessageLevel = Qgis.Info) -> None:
        """Gibt eine Meldung ueber den Task-Logger oder den QGIS-Nachrichtenlog aus.

        Args:
            msg: Die zu loggende Nachricht.
            level: Schweregrad der Meldung (Standard: Info).
        """
        if self.task is not None and hasattr(self.task, "logging"):
            self.task.logging.emit(msg)
            return
        QgsMessageLog.logMessage(msg, level)