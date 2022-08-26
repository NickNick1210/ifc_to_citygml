# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)
 ***************************************************************************/
"""

#####

# Standard-Bibliotheken
import os
from datetime import datetime

# QGIS-Bibliotheken
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import QCoreApplication

# GUI-Datei
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'dialog.ui'))


#####


class DialogVM(QtWidgets.QDialog, FORM_CLASS):
    """ ViewModel der GUI-View """

    def __init__(self, parent, model):
        """ Konstruktor der GUI-ViewModel-Klasse.

        Args:
            parent: Die zugrunde liegende Base-Klasse
            model: Die zugehörige Model-Klasse, die sich um die Logik kümmert
        """
        # Oberklassenkonstruktor
        super(DialogVM, self).__init__(None)

        # Initialisierung von Attributen
        self.parent = parent
        self.model = model

        # GUI aufbauen
        self.setupUi(self)

        # Datei-Format-Filter für die Dateiauswahlen und ReadOnly für die Textfelder setzen
        self.fileWidget_ifc.setFilter("Industry Foundation Classes (*.ifc)")
        self.fileWidget_ifc.lineEdit().setReadOnly(True)
        self.fileWidget_cgml.setFilter("Geography Markup Language (*.gml)")
        self.fileWidget_cgml.lineEdit().setReadOnly(True)

        # EventListener für den Startknopf
        self.button_run.clicked.connect(model.run)
        self.fileWidget_ifc.fileChanged.connect(model.ifcFileChanged)
        self.fileWidget_cgml.fileChanged.connect(model.cgmlFileChanged)

        self.log(QCoreApplication.translate('DialogVM', u'Tool started'))

        # Deaktivieren von Funktionalität
        self.radioButton_lod4.setDisabled(True)

    def getInputPath(self):
        """ Gibt den Eingabepfad zurück.

        Returns:
            Eingabepfad als String
        """
        return self.fileWidget_ifc.filePath()

    def getOutputPath(self):
        """ Gibt den Ausgabepfad zurück.

        Returns:
            Ausgabepfad als String
        """
        return self.fileWidget_cgml.filePath()

    def getOptionVal(self):
        """ Gibt zurück, ob die Validierung ausgewählt wurde.

        Returns:
            Auswahl als Boolean
        """
        return self.checkBox_val.isChecked()

    def getOptionEade(self):
        """ Gibt zurück, ob die EnergyADE ausgewählt wurde.

        Returns:
            Auswahl als Boolean
        """
        return self.checkBox_eade.isChecked()

    def getOptionIntegr(self):
        """ Gibt zurück, ob die QGIS-Integration ausgewählt wurde.

        Returns:
            Auswahl als Boolean
        """
        return self.checkBox_integr.isChecked()

    def getLod(self):
        """ Gibt die gewählte Level of Detail (LoD)-Stufe zurück.

        Returns:
            Auswahl als Integer
        """
        if self.radioButton_lod0.isChecked():
            return 0
        elif self.radioButton_lod1.isChecked():
            return 1
        elif self.radioButton_lod2.isChecked():
            return 2
        elif self.radioButton_lod3.isChecked():
            return 3
        elif self.radioButton_lod4.isChecked():
            return 4
        else:
            return -1

    def setIfcInfo(self, text):
        """ Setzt das IFC-Beschreibungsfeld auf einen übergebenen Text.

        Args:
            text: Der einzutragende Text
        """
        self.label_ifc_info.setText(text)

    def setIfcMsg(self, msg):
        """ Setzt das IFC-Warnungsfeld auf einen übergebenen Text im HTML-Format.

        Args:
            msg: Der einzutragende Text im HTML-Format
        """
        self.label_ifc_msg.setText(msg)

    def log(self, msg):
        """ Fügt einen Text als weitere Zeile unter Zugabe der Uhrzeit in das Logging-Feld hinzu.

        Args:
            msg: Der zu loggende Text
        """
        currTime = datetime.now().strftime("%H:%M:%S")
        self.textBrowser_log.append(currTime + "   " + msg)

    def enableProgress(self, enable):
        """ Aktiviert oder deaktiviert den Forschrittsbalken.

        Args:
            enable: Ob aktiviert oder deaktiviert werden soll
        """
        self.progressBar.setEnabled(enable)

    def setProgress(self, progr):
        """ Setzt den Fortschrittbalken auf einen bestimmten prozentualen Wert.

        Args:
            progr: Prozentualer Wert, auf den der Fortschritt gesetzt werden soll
        """
        self.progressBar.setValue(progr)

    def enableRun(self, enable):
        """ Aktiviert oder deaktiviert den Ausführen-Button.

        Args:
            enable: Ob aktiviert werden soll, als Boolean
        """
        self.button_run.setEnabled(enable)

    def enableDef(self, enable):
        """ Aktiviert oder deaktiviert die Einstellungsmöglichkeiten.

        Args:
            enable: Ob aktiviert werden soll, als Boolean
        """
        # GroupBoxen
        self.groupBox_ifc.setEnabled(enable)
        self.groupBox_cgml.setEnabled(enable)

        # Farbe des IFC-Warnungsfeldes
        if self.label_ifc_msg.text() != "":
            txt = self.label_ifc_msg.text()[self.label_ifc_msg.text().index(">") + 1:-4]
            self.label_ifc_msg.setText("<p style='color:dimgrey'>" + txt + "</p>")
