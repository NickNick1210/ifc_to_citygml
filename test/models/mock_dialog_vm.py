# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)

Mock-Klasse der ViewModel-Klasse DialogVM
 ***************************************************************************/
"""


#####

class DialogVM:

    def __init__(self, parent, model):
        """ Konstruktor der GUI-ViewModel-Klasse.

        Args:
            parent: Die zugrunde liegende Base-Klasse
            model: Die zugehörige Model-Klasse, die sich um die Logik kümmert
        """
        self.logText = ""
        self.ifcInfo = ""
        self.ifcMsg = ""

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
        """ Setzt das IFC-Warnungsfeld auf einen übergebenen Text im HTML-Format.

        Args:
            msg: Der einzutragende Text im HTML-Format
        """
        self.ifcMsg = msg
