# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (09.09.2022)

Mock-Klasse der ViewModel-Klasse DialogVM
 ***************************************************************************/
"""


#####

class DialogVM:

    # noinspection PyUnusedLocal
    def __init__(self, parent, model):
        """ Konstruktor der GUI-ViewModel-Klasse.

        Args:
            parent: Die zugrunde liegende Base-Klasse
            model: Die zugehörige Model-Klasse, die sich um die Logik kümmert
        """
        self.logText = ""
        self.ifcInfo = ""
        self.ifcMsg = ""
        self.ifcStatus = ""

    def log(self, msg):
        """ Fügt einen Text als weitere Zeile unter Zugabe der Uhrzeit in das Logging-Feld hinzu.

        Args:
            msg: Der zu loggende Text
        """
        self.logText = msg

    def setIfcInfo(self, text):
        """ Setzt das IFC-Beschreibungsfeld auf einen übergebenen Text.

        Args:
            text: Der einzutragende Text
        """
        self.ifcInfo = text

    def setIfcMsg(self, msg):
        """ Setzt das IFC-Informationsfeld auf einen übergebenen Text.

        Args:
            msg: Der einzutragende Text
        """
        self.ifcMsg = msg

    def setIfcStatus(self, text, color="black"):
        """ Setzt den Status-Text der IFC-Validierung.

        Args:
            text: Status-Text
            color: Textfarbe
        """
        self.ifcStatus = text

    def prefillSourceCrs(self, epsg):
        """ Befüllt das Quell-CRS-Feld.

        Args:
            epsg: EPSG-Code oder None
        """
        pass
