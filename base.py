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
import os.path
import pathlib
import sys

# QGIS-Bibliotheken
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

# IFC-to-CityGML
from .resources import *
from .dialog_vm import Dialog_VM
from .model import Model
from .gis_vm import GIS_VM

#####

class Base:
    """ Starter-Klasse des Plugins. """

    def __init__(self, iface):
        """ Konstruktor der Starter-Klasse.

        Args:
            iface: Eine Interface-Instanz, an die sich das Plugin bindet
        """

        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        # locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'base_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&IFC-to-CityGML')

        self.first_start = None

        try:
            import ifcopenshell
        except:
            self.install()


    def install(self):
        plugin_dir = os.path.dirname(os.path.realpath(__file__))

        try:
            import pip
        except ImportError:
            exec(
                open(str(pathlib.Path(plugin_dir, 'scripts', 'get_pip.py'))).read()
            )
            import pip
            # just in case the included version is old
            pip.main(['install', '--upgrade', 'pip'])

        sys.path.append(plugin_dir)

        with open(os.path.join(plugin_dir, 'requirements.txt'), "r") as requirements:
            for dep in requirements.readlines():
                dep = dep.strip().split("==")[0]
                try:
                    __import__(dep)
                except ImportError as e:
                    print("{} not available, installing".format(dep))
                    pip.main(['install', dep])


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """ Übersetzung bekommen

        Args:
            message: String zum Übersetzen.

        Returns:
            Übersetzte Version des Strings
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('IFC-to-CityGML', message)



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

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """ Erstellt die Menü-Einträge und Tools in der QGIS-GUI. """
        icon_path = ':/plugins/ifc_to_citygml/icons/logo.png'
        self.add_action(icon_path, text=self.tr(u'IFC-to-CityGML'), callback=self.run, parent=self.iface.mainWindow())
        self.first_start = True


    def unload(self):
        """ Entfernt die Menü-Einträge und Tools von der QGIS-GUI. """
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&IFC-to-CityGML'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run-Methode, die die Arbeit startet"""

        # Model starten
        self.model = Model()

        # GUI starten
        if self.first_start == True:
            self.first_start = False
            self.dlg = Dialog_VM(self, self.model)
        self.dlg.show()

        # GIS verbinden
        self.gis = GIS_VM(self, self.model)

        self.model.setVM(self.dlg, self.gis)





