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

# IFC-Bibliotheken
import ifcopenshell
import ifcopenshell.validate

# QGIS-Bibliotheken
from qgis.core import QgsTask, QgsApplication

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
        self.fileName = path[path.rindex("\\") + 1:-4]

    def run(self, val):
        """ Ausführen der Analyse

        Args:
            val: Angabe, ob eine Validierung durchgeführt werden soll
        """
        self.printInfo(self.ifc)
        self.check(self.ifc, val)

    @staticmethod
    def read(path):
        """ Einlesen einer IFC-Datei

        Args:
            path: Pfad zur IFC-Datei

        Returns:
            Eingelesene IFC-Datei
        """
        return ifcopenshell.open(path)

    def printInfo(self, ifc):
        """ Einlesen einer IFC-Datei

        Args:
            ifc: Auszulesende IFC-Datei
        """
        self.parent.dlg.log(self.parent.tr(u'IFC file') + " '" + self.fileName + "' " + self.parent.tr(u'is analyzed'))

        # Eigenschaften
        schema = self.parent.tr(u'Schema') + ": " + ifc.schema
        name = self.parent.tr(u'Name') + ": " + ifc.by_type("IfcProject")[0].Name
        if ifc.by_type("IfcProject")[0].Description is not None:
            descr = self.parent.tr(u'Description') + ": " + ifc.by_type("IfcProject")[0].Description
        else:
            descr = self.parent.tr(u'Description') + ": -"
        anzBldg = self.parent.tr(u'No. of Buildings') + ": " + str(len(ifc.by_type("IfcBuilding")))

        self.parent.dlg.setIfcInfo(schema + "<br>" + name + "<br>" + descr + "<br>" + anzBldg)

    def check(self, ifc, val):
        """ Überprüfung der IFC-Datei

        Args:
            ifc: Zu überprüfende IFC-Datei
            val: Angabe, ob eine Validierung durchgeführt werden soll
        """
        # Prüfung, ob Gebäude vorhanden
        if len(ifc.by_type("IfcBuilding")) == 0:
            self.parent.valid = False
            self.parent.checkEnable()
            self.parent.dlg.setIfcMsg("<p style='color:red'>" + self.parent.tr(u'not valid') + "</p>")
            self.parent.dlg.log(self.parent.tr(u'There are no buildings in the IFC file!'))
            return

        # Validierung über einen QgsTask, der asynchron ausgeführt wird
        # Wichtig, da sonst die QGIS-Oberfläche einfriert
        if val:
            self.parent.dlg.log(
                self.parent.tr(u'IFC file') + " '" + self.fileName + "' " + self.parent.tr(u'is validated'))
            # Muss über Klassenmethode geschehen, da der Task sonst 'vergessen' und deswegen nicht ausgeführt wird
            self.valTask = QgsTask.fromFunction(self.parent.tr(u'Validation of IFC file'), self.validate,
                                                on_finished=self.valCompleted)
            QgsApplication.taskManager().addTask(self.valTask)
        else:
            self.valCompleted()

    # noinspection PyUnusedLocal
    def validate(self, task):
        """ Validierung der IFC-Datei

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
    def valCompleted(self, ex=None, result=None):
        """ EventListener, wenn der Validierungs-Task erfolgt ist

        Args:
            ex: ggf. Exception
                Default: None
            result: Ergebniss der Validierung
                Default: None
        """
        # Wenn Ergebnis vorhanden und nicht leer: Fehler vorhanden
        if result is not None and len(result.statements) != 0:
            # Mitteilen
            self.parent.dlg.log(
                str(len(result.statements)) + " " + self.parent.tr(u'errors found'))
            self.parent.dlg.setIfcMsg("<p style='color:orange'>" + self.parent.tr(u'conditionally valid') + "</p>")

            # Fehler in redundanzfreie Liste umformen und mitteilen
            stmtList = []
            for stmt in result.statements:
                if stmt["message"] not in stmtList:
                    stmtList.append(str(stmt["message"]))
            for stmt in stmtList:
                self.parent.dlg.log(self.parent.tr(u'Error') + ": " + stmt)

        # Wenn kein Ergebnis vorhanden oder leer: kein Fehler vorhanden
        else:
            self.parent.dlg.setIfcMsg("<p style='color:black'>" + self.parent.tr(u'valid') + "</p>")

        # In beiden Fällen: Freigeben
        self.parent.valid = True
        self.parent.checkEnable()
