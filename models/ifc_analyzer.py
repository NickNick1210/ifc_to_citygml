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
import os

# IFC-Bibliotheken
import ifcopenshell
import ifcopenshell.validate
from qgis._core import QgsTask, QgsApplication


class IfcAnalyzer():
    def __init__(self, parent, path):
        """Constructor."""
        self.parent = parent
        self.ifc = self.read(path)
        self.fileName = path[path.rindex("\\") + 1:-4]


    def run(self, val):
        self.printInfo(self.ifc)
        self.check(self.ifc, val)


    def read(self, path):
        ifc = ifcopenshell.open(path)
        return ifc


    def printInfo(self, ifc):
        self.parent.dlg.log("IFC-Datei '" + self.fileName + "' wird analysiert")
        schema = "Schema: " + ifc.schema
        name = "Name: " + ifc.by_type("IfcProject")[0].Name
        if(ifc.by_type("IfcProject")[0].Description is not None):
            descr = "Beschreibung: " + ifc.by_type("IfcProject")[0].Description
        else:
            descr = "Beschreibung: -"
        anzBldg = "Anz. Gebäude: " + str(len(ifc.by_type("IfcBuilding")))

        self.parent.dlg.setIfcInfo(schema + "<br>" + name + "<br>" + descr + "<br>" + anzBldg)


    def check(self, ifc, val):

        # Prüfung, ob Gebäude vorhanden
        if len(ifc.by_type("IfcBuilding")) == 0:
            self.parent.valid = False
            self.parent.checkEnable()
            self.parent.dlg.setIfcMsg("<p style='color:red'>nicht valide</p>")
            self.parent.dlg.log("In der IFC-Datei sind keine Gebäude vorhanden!")
            return

        if val:
            self.parent.dlg.log("IFC-Datei '" + self.fileName + "' wird validiert")
            self.valTask = QgsTask.fromFunction("Validierung der IFC-Datei", self.validate,
                                                on_finished=self.valCompleted)
            QgsApplication.taskManager().addTask(self.valTask)
        else:
            self.parent.valid = True
            self.parent.checkEnable()


    def validate(self, task):
        try:
            json_logger = ifcopenshell.validate.json_logger()
            ifcopenshell.validate.validate(self.ifc, json_logger)
        except:
            pass
        finally:
            return json_logger


    def valCompleted(self, exception, result=None):
        if len(result.statements) != 0:
            self.parent.dlg.log(str(len(result.statements)) + " Fehler gefunden")
            self.parent.dlg.setIfcMsg("<p style='color:orange'>bedingt valide</p>")
            stmtList = []
            for stmt in result.statements:
                if stmt["message"] not in stmtList:
                    stmtList.append(str(stmt["message"]))
            for stmt in stmtList:
                self.parent.dlg.log("Fehler: " + stmt)
        else:
            self.parent.dlg.setIfcMsg("valide")
        self.parent.valid = True
        self.parent.checkEnable()


