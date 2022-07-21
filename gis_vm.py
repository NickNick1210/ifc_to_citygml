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
import sys

from qgis.core import QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication

from lxml import etree

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
        return QCoreApplication.translate('GisVM', msg)

    def loadIntoGIS(self, path):
        print(path)
        name = path[path.rindex("\\") + 1:-4]
        layer = QgsVectorLayer(path, name, "ogr")
        print(layer.isValid())
        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            self.parent.dlg.log(self.tr(u'CityGML building model added to QGIS'))
            self.set3dProperties(layer)
        else:
            self.parent.dlg.log(self.tr(u'CityGML bulding model could not be added to QGIS'))

    def set3dProperties(self, layer):
        qml = etree.parse("C:/Users/nickl/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/ifc_to_citygml/resources/3D.qml")
        minV = qml.xpath("//Option[@name='minValue']")[0]
        maxV = qml.xpath("//Option[@name='maxValue']")[0]

        minHeight = sys.maxsize
        maxHeight = -sys.maxsize
        ix = layer.fields().indexFromName('measuredHeight')
        for feature in layer.getFeatures():
            height = feature.attributes()[ix]
            if height < minHeight:
                minHeight = height
            if height > maxHeight:
                maxHeight = height

        minV.set("value", str(minHeight))
        maxV.set("value", str(maxHeight))

        qml.write("C:/Users/nickl/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/ifc_to_citygml/resources/3D.qml", xml_declaration=True, encoding="UTF-8", pretty_print=True)

        layer.loadNamedStyle("C:/Users/nickl/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/ifc_to_citygml/resources/3D.qml")
        layer.triggerRepaint()
        self.parent.dlg.log(self.tr(u'3D properties adjusted to display the building model'))
