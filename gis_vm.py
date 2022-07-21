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

# QGIS-Bibliotheken
from qgis.core import QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication

#####

class GisVM:
    """ ViewModel der GIS-View """

    def __init__(self, parent, model):
        """Constructor."""
        self.parent = parent
        self.model = model

    @staticmethod
    def tr(msg):
        """ Übersetzen

        Args:
            msg: zu übersetzender Text

        Returns:
            Übersetzter Text
        """
        return QCoreApplication.translate('Converter', msg)

    def loadIntoGIS(self, path):
        print(path)
        name = path[path.rindex("\\") + 1:-4]
        layer = QgsVectorLayer(path, name, "ogr")
        print(layer.isValid())
        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            self.parent.dlg.log(self.tr(u'CityGML building model added to QGIS'))
        else:
            self.parent.dlg.log(self.tr(u'CityGML bulding model could not be added to QGIS'))
