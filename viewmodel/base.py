# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (09.09.2022)
 ***************************************************************************/
"""

#####

# Standard-Bibliotheken
import os.path
import pathlib
import sys

# QGIS-Bibliotheken
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon

# Plugin
# noinspection PyUnresolvedReferences
from ..resources import resources
from .model import Model
from ..view.dialog_vm import DialogVM
from ..view.gis_vm import GisVM

#####


class Base:
    """ Starter-Klasse des Plugins. """

    def __init__(self, iface):
        """ Konstruktor der Starter-Klasse.

        Args:
            iface: Die QGIS-Interface-Instanz, an die sich das Plugin bindet
        """

        # Initialisierung von Attributen
        self.model = None
        self.dlg, self.gis = None, None
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        # Übersetzungen, falls vorhanden
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, '../i18n', 'ifc_to_citygml_{}.qm'.format(locale))
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # GUI
        self.actions = []
        self.menu = 'IFC-to-CityGML'

    def initGui(self):
        """ Erstellt die Menü-Einträge und Tools in der QGIS-GUI. """
        icon_path = ':/plugins/ifc_to_citygml/resources/logo.png'
        self.add_action(icon_path, text='IFC-to-CityGML', callback=self.run, parent=self.iface.mainWindow())

    def add_action(self, icon_path, text, callback, enabled_flag=True, add_to_menu=True, add_to_toolbar=True,
                   status_tip=None, whats_this=None, parent=None):
        """ Fügt ein neues Tool zur Toolbar hinzu.

        Args:
            icon_path: Pfad zum Icon des Tools.
            text: Text, der im Menü für dieses Tool angezeigt werden soll.
            callback: Funktion, die bei Aufruf des Tools ausgelöst werden soll.
            enabled_flag: Ob das Tool aktiviert sein soll.
                Default: True.
            add_to_menu: Ob das Tool zum Menü hinzugefügt werden soll.
                Default: True
            add_to_toolbar: Ob das Tool zur Toolbar hinzugefügt werden soll.
                Default: True
            status_tip: Tooltip-Text
                Default: None
            parent: Parent-Widget für das Tool
                Default: None
            whats_this: Statusbar-Text beim Hovern über das Tool
                Default: None

        Returns:
            Das Tool, das erstellt wurde, als QAction. Wird zusätzlich zur self.actions-Liste hinzugefügt
        """

        # Erstellen
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)

        # Einstellungen
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        if status_tip is not None:
            action.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)

        # Hinzufügen
        if add_to_toolbar:
            self.iface.addToolBarIcon(action)
        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)
        self.actions.append(action)

        return action

    def unload(self):
        """ Entfernt die Menü-Einträge und Tools von der QGIS-GUI """
        for action in self.actions:
            self.iface.removePluginMenu('IFC-to-CityGML', action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        """ Run-Methode, die den Ablauf startet """

        # Model starten
        self.model = Model(self.iface)

        # Views und Viewmodels starten
        self.gis = GisVM(self.model)
        self.dlg = DialogVM(self.model)
        self.dlg.show()
        self.model.setVM(self.dlg, self.gis)
