# IFC-Bibliotheken
import ifcopenshell
import ifcopenshell.util.pset

# XML-Bibliotheken
from lxml import etree
# noinspection PyUnresolvedReferences
from lxml.etree import QName

# QGIS-Bibliotheken
from qgis.core import QgsTask
from qgis.PyQt.QtCore import QCoreApplication, pyqtSignal


class Converter:
    logging = pyqtSignal(str)

    def completed(self, result):
        pass
