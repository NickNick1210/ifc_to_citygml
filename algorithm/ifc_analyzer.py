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
import os
import platform

# IFC-Bibliotheken
import sys

try:
    import ifcopenshell
    import ifcopenshell.validate
except ImportError:
    import runpy
    sys.argv = [
        "pip", "install", "ifcopenshell",
    ]
    runpy.run_module("pip", run_name="__main__")
    import ifcopenshell
    import ifcopenshell.validate

# QGIS-Bibliotheken
from qgis.core import QgsTask, QgsApplication
from qgis.PyQt.QtCore import QCoreApplication

# Lokale Importe
from .transformer import Transformer, GeoRefResult

#####


class IfcAnalyzer:
    """ Model-Klasse zum Analysieren von IFC-Dateien """

    def __init__(self, parent, path):
        """ Konstruktor der Model-Klasse zum Analysieren von IFC-Dateien

        Args:
            parent: Die zugrunde liegende zentrale Model-Klasse
            path: Pfad zur IFC-Datei
        """

        # Initialisierung von Attributen
        self.parent = parent
        self.valTask = None

        # IFC-Datei
        self.ifc = self.read(path)
        slash = "/" if platform.system() == "Linux" else "\\"
        self.fileName = path[path.rindex(slash) + 1:-4]

    @staticmethod
    def tr(msg):
        """ Übersetzt den angegebenen Text

        Args:
            msg: zu übersetzender Text

        Returns:
            Übersetzter Text
        """
        return QCoreApplication.translate('IfcAnalyzer', msg)

    def run(self, val):
        """ Führt die Analyse aus

        Args:
            val: Angabe, ob eine Validierung durchgeführt werden soll, als Boolean
        """
        self.printInfo(self.ifc)
        self.check(self.ifc, val)

    @staticmethod
    def read(path):
        """ Liest eine IFC-Datei ein

        Args:
            path: Pfad zur IFC-Datei

        Returns:
            Eingelesene IFC-Datei
        """
        return ifcopenshell.open(path)

    def printInfo(self, ifc):
        """ Stell die grundlegenden Informationen der IFC-Datei dar

        Args:
            ifc: Auszulesende IFC-Datei
        """
        self.parent.dlg.log(self.tr(u'IFC file') + " '" + self.fileName + "' " + self.tr(u'is analyzed'))

        # Eigenschaften
        schema = self.tr(u'Schema') + ": " + ifc.schema
        name = self.tr(u'Name') + ": " + ifc.by_type("IfcProject")[0].Name
        if ifc.by_type("IfcProject")[0].Description is not None:
            descr = self.tr(u'Description') + ": " + ifc.by_type("IfcProject")[0].Description
        else:
            descr = self.tr(u'Description') + ": -"
        anzBldg = self.tr(u'No. of Buildings') + ": " + str(len(ifc.by_type("IfcBuilding")))

        self.parent.dlg.setIfcInfo(schema + "<br>" + name + "<br>" + descr + "<br>" + anzBldg)

    # Hilfsmethode: Orientierung prüfen
    # Level 50: XAxisAbscissa + XAxisOrdinate aus IfcMapConversion
    # Level 40/30/20/10: TrueNorth aus IfcGeometricRepresentationContext
    @staticmethod
    def _check_orientation(ifc, georef: GeoRefResult) -> bool:
        """ Prüft, ob eine korrekte Gebäudeorientierung vorhanden ist

        Args:
            ifc: Die zu prüfende IFC-Datei
            georef: Ergebnis der Georeferenzierungsprüfung als GeoRefResult

        Returns:
            True, wenn eine Orientierung definiert ist, sonst False
        """
        # Level 50: Orientierung über XAxisAbscissa / XAxisOrdinate aus IfcMapConversion
        if (
            georef.level == 50
            and georef.x_axis_abscissa is not None
            and georef.x_axis_ordinate is not None
        ):
            a = georef.x_axis_abscissa
            b = georef.x_axis_ordinate
            # Orientierung gilt als definiert, sobald MapConversion-Werte vorhanden sind.
            # Auch die Einheitsmatrix ist eine gueltige Ausrichtung (keine Rotation).
            return True

        # Level 40 / 30 / 20 / 10: Ausrichtung über TrueNorth aus IfcGeometricRepresentationContext
        projects = ifc.by_type("IfcProject")
        if not projects:
            return False
        project = projects[0]
        for context in getattr(project, "RepresentationContexts", []):
            if getattr(context, "ContextType", None) == "Model":
                tn = getattr(context, "TrueNorth", None)
                if tn is not None:
                    ratios = list(tn.DirectionRatios)
                    if len(ratios) >= 2:
                        a, b = ratios[0], ratios[1]
                        # TrueNorth gilt als gesetzt, wenn es von der Standard-Nordrichtung abweicht
                        # Standard: [0, 1] (Y-Achse zeigt nach Norden)
                        is_default = (abs(a) < 1e-9 and abs(b - 1.0) < 1e-9)
                        return not is_default
                    # TrueNorth ist vorhanden, aber leer → keine Ausrichtung
                    return False
        return False

    def check(self, ifc, val):
        """ Überprüft die IFC-Datei

        Args:
            ifc: Zu überprüfende IFC-Datei
            val: Angabe, ob eine Validierung durchgeführt werden soll, als Boolean
        """
        # Anzahl der Gebäude ermitteln
        anz_gebaeude = len(ifc.by_type("IfcBuilding"))

        # Prüfung, ob Gebäude vorhanden
        if anz_gebaeude == 0:
            self.parent.valid = False
            self.parent.checkEnable()
            self.parent.dlg.setIfcStatus(self.tr(u'not valid'), "red")
            self.parent.dlg.setIfcMsg(
                self.tr(u'There are no buildings in the IFC file!')
            )
            self.parent.dlg.log(self.tr(u'There are no buildings in the IFC file!'))
            self.parent.dlg.prefillSourceCrs(None)
            return

        # Georeferenzierungsprüfung über alle LoGeoRef-Stufen (50 → 10)
        georef = Transformer.check_georef_static(ifc)
        georef_level = georef.level  # 0 = keine Georeferenzierung gefunden

        # Prüfung, ob eine verwertbare Georeferenzierung vorhanden ist (mind. Level 20)
        if georef_level < 20:
            self.parent.valid = False
            self.parent.checkEnable()
            self.parent.dlg.setIfcStatus(self.tr(u'not valid'), "red")
            self.parent.dlg.setIfcMsg(
                self.tr(u"LoGeoRef: ")
                + str(georef_level)
                + " (" + (georef.source or self.tr(u'none')) + ")"
            )
            self.parent.dlg.log(self.tr(u'There is no georeferencing in the IFC file!'))
            self.parent.dlg.prefillSourceCrs(None)
            return

        # Orientierungsprüfung: alle Varianten (XAxis aus MapConversion oder TrueNorth)
        orientation_ok = self._check_orientation(ifc, georef)
        orientation_text = self.tr(u'yes') if orientation_ok else self.tr(u'no')

        # Prüfung, ob Nordrichtung / Orientierung definiert ist
        if not orientation_ok:
            # Orientierung fehlt → nicht gültig
            self.parent.valid = False
            self.parent.checkEnable()
            self.parent.dlg.setIfcStatus(self.tr(u'not valid'), "red")
            self.parent.dlg.setIfcMsg(
                self.tr(u"LoGeoRef: ")
                + str(georef_level)
                + " (" + (georef.source or "") + ")\n"
                + self.tr(u'Orientation')
                + ": " + orientation_text
            )
            self.parent.dlg.log(self.tr(u'There is no orientation in the IFC file!'))
            self.parent.dlg.prefillSourceCrs(None)
            return
        
        detected_epsg = georef.epsg
        self.parent.dlg.prefillSourceCrs(detected_epsg)

        # Validierung über einen QgsTask, der asynchron ausgeführt wird
        # Wichtig, da sonst die QGIS-Oberfläche einfriert
        if val:
            self.parent.dlg.log(
                self.tr(u'IFC file') + " '" + self.fileName + "' " + self.tr(u'is validated'))
            # Muss über Klassenmethode geschehen, da der Task sonst 'vergessen' und deswegen nicht ausgeführt wird
            self.valTask = QgsTask.fromFunction(
                self.tr(u'Validation of IFC file'),
                self.validate,
                on_finished=lambda ex, result: self.valCompleted(
                    ex, result, anz_gebaeude, georef_level, georef.source or "", orientation_text
                ),
            )
            QgsApplication.taskManager().addTask(self.valTask)
        else:
            self.valCompleted(
                None, None, anz_gebaeude, georef_level, georef.source or "", orientation_text
            )
        return

    # noinspection PyUnusedLocal
    def validate(self, task):
        """ Validiert die IFC-Datei

        Args:
            task: QgsTask-Objekt

        Returns:
            Validierungsergebnisse als JSON-Logger
        """
        # Wenn die Validierung einen Fehler wirft, kann das ebenfalls an der IFC-Datei liegen. Deswegen wird abgefangen
        json_logger = None
        # noinspection PyBroadException
        try:
            json_logger = ifcopenshell.validate.json_logger()
            ifcopenshell.validate.validate(self.ifc, json_logger)
        except Exception:
            pass
        finally:
            return json_logger

    # noinspection PyUnusedLocal
    def valCompleted(self, ex=None, result=None,
                     anz_gebaeude: int = 0,
                     georef_level: int = 0,
                     georef_source: str = "",
                     orientation_text: str = ""):
        """ EventListener, wenn der Validierungs-Task erfolgt ist

        Args:
            ex: ggf. Fehlermeldung
                Default: None
            result: Gefundene Fehler, als Liste
                Default: None
            anz_gebaeude: Anzahl der Gebäude in der IFC-Datei
            georef_level: Ermittelter LoGeoRef-Level (10–50, oder 0)
            georef_source: Beschreibung der Georeferenzierungsquelle
            orientation_text: Anzeigetext für korrekte Ausrichtung (ja/nein)
        """
        # Zusatzinformationen, die immer angezeigt werden
        info_text = (
            self.tr(u"LoGeoRef: ")
            + str(georef_level) + " (" + georef_source + ")\n"
            + self.tr(u'Orientation') + ": " + orientation_text
        )

        # Wenn Ergebnis vorhanden und nicht leer: Fehler vorhanden
        statements = getattr(result, "statements", []) if result is not None else []
        if statements:
            # Mitteilen
            self.parent.dlg.log(str(len(statements)) + " " + self.tr(u'errors found'))
            self.parent.dlg.setIfcStatus(
                self.tr(u'conditionally valid'), "orange"
            )
            self.parent.dlg.setIfcMsg(info_text)

        # Wenn kein Ergebnis vorhanden oder leer: kein Fehler vorhanden
        else:
            self.parent.dlg.setIfcStatus(self.tr(u'valid'), "black")
            self.parent.dlg.setIfcMsg(info_text)

        # In beiden Fällen: Freigeben
        self.parent.valid = True
        self.parent.checkEnable()

        