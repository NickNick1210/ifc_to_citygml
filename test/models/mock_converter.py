# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)

Mock-Klasse der Model-Klasse Converter
 ***************************************************************************/
"""

# QGIS-Bibliotheken
from qgis.core import QgsTask
from qgis.PyQt.QtCore import pyqtSignal


#####

class Converter(QgsTask):
    logging = pyqtSignal(str)

    def isCanceled(self):
        """ Überschreiben der Oberklassenmethode """
        return False
