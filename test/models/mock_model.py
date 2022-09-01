# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)

Mock-Klasse der Modelklasse Model
 ***************************************************************************/
"""

# Plugin
from mock_dialog_vm import DialogVM


#####

class Model:

    def __init__(self):
        self.dlg = DialogVM(None, self)
        self.completedTest = False
        self.valid = None

    def completed(self, result):
        """ Beendet die Konvertierung

            Args:
                result: Ob die Konvertierung erfolgreich war, als Boolean
        """
        self.completedTest = True

    def checkEnable(self):
        """ Überprüft, ob beide Dateien angegeben und valide sind und gibt ggf. Konvertierung frei """
        pass
