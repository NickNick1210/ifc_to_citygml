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
from qgis.PyQt.QtCore import QCoreApplication


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
        self.parent.dlg.log(QCoreApplication.translate('IFC-to-CityGML', u'IFC file') + " '" + self.fileName + "' " + QCoreApplication.translate('IFC-to-CityGML', u'is analyzed'))
        schema = QCoreApplication.translate('IFC-to-CityGML', u'Schema') + ": " + ifc.schema
        name = QCoreApplication.translate('IFC-to-CityGML', u'Name') + ": " + ifc.by_type("IfcProject")[0].Name
        if(ifc.by_type("IfcProject")[0].Description is not None):
            descr = QCoreApplication.translate('IFC-to-CityGML', u'Description') + ": " + ifc.by_type("IfcProject")[0].Description
        else:
            descr = QCoreApplication.translate('IFC-to-CityGML', u'Description') + ": -"
        anzBldg = QCoreApplication.translate('IFC-to-CityGML', u'No. of Buildings') + ": " + str(len(ifc.by_type("IfcBuilding")))

        self.parent.dlg.setIfcInfo(schema + "<br>" + name + "<br>" + descr + "<br>" + anzBldg)


    def check(self, ifc, val):

        # Prüfung, ob Gebäude vorhanden
        if len(ifc.by_type("IfcBuilding")) == 0:
            self.parent.valid = False
            self.parent.checkEnable()
            self.parent.dlg.setIfcMsg("<p style='color:red'>" + QCoreApplication.translate('IFC-to-CityGML', u'not valid') + "</p>")
            self.parent.dlg.log(QCoreApplication.translate('IFC-to-CityGML', u'There are no buildings in the IFC file!'))
            return

        if val:
            self.parent.dlg.log(QCoreApplication.translate('IFC-to-CityGML', u'IFC file') + " '" + self.fileName + "' " + QCoreApplication.translate('IFC-to-CityGML', u'is validated'))
            self.valTask = QgsTask.fromFunction(QCoreApplication.translate('IFC-to-CityGML', u'Validation of IFC file'), self.validate,
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
            self.parent.dlg.log(str(len(result.statements)) + " " + QCoreApplication.translate('IFC-to-CityGML', u'errors found'))
            self.parent.dlg.setIfcMsg("<p style='color:orange'>" + QCoreApplication.translate('IFC-to-CityGML', u'conditionally valid') + "</p>")
            stmtList = []
            for stmt in result.statements:
                if stmt["message"] not in stmtList:
                    stmtList.append(str(stmt["message"]))
            for stmt in stmtList:
                self.parent.dlg.log(QCoreApplication.translate('IFC-to-CityGML', u'Error') + ": " + stmt)
        else:
            self.parent.dlg.setIfcMsg(QCoreApplication.translate('IFC-to-CityGML', u'valid'))
        self.parent.valid = True
        self.parent.checkEnable()


