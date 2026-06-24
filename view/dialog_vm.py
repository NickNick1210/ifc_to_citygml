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
from datetime import datetime

# QGIS-Bibliotheken
from qgis.PyQt.QtCore import Qt, QCoreApplication
from qgis.core import QgsMessageLog, Qgis, QgsProject

# Lokale Importe
from .dialog import IfcToCityGmlDockWidget

TAG = "IFC-to-CityGML"


class DialogVM:
    """ViewModel der GUI-View."""

    def __init__(self, model, iface):
        """Konstruktor der GUI-ViewModel-Klasse.

        Args:
            model: Die zugehörige Model-Klasse, die sich um die Logik kümmert.
            iface: QGIS-Interface für Docking und Logging.
        """
        # Initialisierung von Attributen
        self.model = model
        self.iface = iface
        self.dock = IfcToCityGmlDockWidget(iface.mainWindow())

        self._connect_signals()
        self._log_info(
            QCoreApplication.translate("DialogVM", u"Tool started")
        )

    def _connect_signals(self) -> None:
        """Verknüpft UI-Signale mit Model/VM-Handlern."""
        d = self.dock

        # EventListener für die Knöpfe
        d.button_run.clicked.connect(self.model.run)
        d.button_close.clicked.connect(self._close)
        # EventListener für die Dateiangaben
        d.fileWidget_ifc.fileChanged.connect(
            self.model.ifcFileChanged
        )
        d.fileWidget_cgml.fileChanged.connect(
            self.model.cgmlFileChanged
        )

        # EventListener für die Einstellungen
        d.radioButton_lod0.clicked.connect(self._activate_integr)
        d.radioButton_lod1.clicked.connect(self._activate_integr)
        d.radioButton_lod2.clicked.connect(self._deactivate_integr)
        d.radioButton_lod3.clicked.connect(self._deactivate_integr)
        d.radioButton_lod4.clicked.connect(self._deactivate_integr)

    def show(self) -> None:
        """Zeigt das Dock-Widget und öffnet das Log-Panel."""
        self.iface.addDockWidget(
            Qt.RightDockWidgetArea, self.dock
        )
        self.dock.show()
        self._open_log_panel()

    def close(self) -> None:
        """Schließt das Dock-Widget."""
        self._close()

    def getInputPath(self) -> str:
        """Gibt den Eingabepfad zurück.

        Returns:
            Eingabepfad als String.
        """
        return self.dock.fileWidget_ifc.filePath()

    def getOutputPath(self) -> str:
        """Gibt den Ausgabepfad zurück.

        Returns:
            Ausgabepfad als String.
        """
        return self.dock.fileWidget_cgml.filePath()

    def getOptionVal(self) -> bool:
        """Gibt zurück, ob die Validierung ausgewählt ist.

        Returns:
            Auswahl als Boolean.
        """
        return self.dock.checkBox_val.isChecked()

    def getOptionEade(self) -> bool:
        """Gibt zurück, ob die EnergyADE ausgewählt ist.

        Returns:
            Auswahl als Boolean.
        """
        return self.dock.checkBox_eade.isChecked()

    def getOptionIntegr(self) -> bool:
        """Gibt zurück, ob die QGIS-Integration ausgewählt ist.

        Returns:
            Auswahl als Boolean.
        """
        return self.dock.checkBox_integr.isChecked()

    def getLod(self) -> int:
        """Gibt die gewählte Level of Detail (LoD)-Stufe zurück.

        Returns:
            Auswahl als Integer.
        """
        return self.dock.lod_button_group.checkedId()

    def setIfcInfo(self, text: str) -> None:
        """Setzt das IFC-Beschreibungsfeld auf einen übergebenen Text.

        Args:
            text: Der einzutragende Text.
        """
        self.dock.label_ifc_info.setText(text)

    def setIfcMsg(self, msg: str) -> None:
        """Setzt das IFC-Informationsfeld auf einen übergebenen Text.

        Args:
            msg: Der einzutragende Text.
        """
        self.dock.label_ifc_msg.setText(msg)

    def setIfcStatus(self, text: str, color: str = "black") -> None:
        """Setzt den Status-Text der IFC-Validierung.

        Args:
            text: Status-Text (z.B. "valid", "not valid").
            color: Textfarbe als CSS-Name oder Hex-Wert.
        """
        self.dock.label_ifc_status.setText(text)
        self.dock.label_ifc_status.setStyleSheet(
            f"color: {color};"
        )

    def log(self, msg: str) -> None:
        """Fügt einen Text als weitere Zeile unter Zugabe der Uhrzeit in das Logging-Feld hinzu.

        Args:
            msg: Der zu loggende Text.
        """
        curr_time = datetime.now().strftime("%H:%M:%S")
        self._log_info(f"{curr_time}   {msg}")

    def logWarning(self, msg: str) -> None:
        """Loggt eine Warnmeldung.

        Args:
            msg: Warnmeldung.
        """
        self._log_warning(msg)

    def logError(self, msg: str) -> None:
        """Loggt eine Fehlermeldung.

        Args:
            msg: Fehlermeldung.
        """
        self._log_error(msg)

    def enableProgress(self, enable: bool) -> None:
        """Aktiviert oder deaktiviert den Fortschrittsbalken.

        Args:
            enable: Ob aktiviert oder deaktiviert werden soll.
        """
        self.dock.progressBar.setEnabled(enable)

    def setProgress(self, progr: float) -> None:
        """Setzt den Fortschrittsbalken auf einen bestimmten prozentualen Wert.

        Args:
            progr: Prozentualer Wert, auf den der Fortschritt gesetzt werden soll.
        """
        self.dock.progressBar.setValue(int(progr))

    def enableRun(self, enable: bool) -> None:
        """Aktiviert oder deaktiviert den Ausführen-Button.

        Args:
            enable: Ob aktiviert werden soll, als Boolean.
        """
        self.dock.button_run.setEnabled(enable)

    def enableDef(self, enable: bool) -> None:
        """Aktiviert oder deaktiviert die Einstellungsmöglichkeiten.

        Args:
            enable: Ob aktiviert werden soll, als Boolean.
        """
        self.dock.groupBox_ifc.setEnabled(enable)
        self.dock.groupBox_cgml.setEnabled(enable)

    def _close(self) -> None:
        """Behandelt das Schließen des Dock-Widgets."""
        self.model.cancel()
        self.iface.removeDockWidget(self.dock)

    def _activate_integr(self, _: bool) -> None:
        """Aktiviert die QGIS-Integration-Option (LoD 0/1)."""
        self.dock.checkBox_integr.setDisabled(False)

    def _deactivate_integr(self, _: bool) -> None:
        """Deaktiviert die QGIS-Integration-Option (LoD 2/3/4)."""
        self.dock.checkBox_integr.setDisabled(True)
        self.dock.checkBox_integr.setChecked(False)

    def _open_log_panel(self) -> None:
        """Zeigt das QGIS-Log-Panel, falls vorhanden."""
        log_dock = self.iface.mainWindow().findChild(
            type(self.dock), "MessageLog"
        )
        if log_dock is not None:
            log_dock.setVisible(True)

    @staticmethod
    def _log_info(msg: str) -> None:
        """Schreibt eine Info in das QGIS-Log."""
        QgsMessageLog.logMessage(msg, TAG, Qgis.Info)

    @staticmethod
    def _log_warning(msg: str) -> None:
        """Schreibt eine Warnung in das QGIS-Log."""
        QgsMessageLog.logMessage(msg, TAG, Qgis.Warning)

    @staticmethod
    def _log_error(msg: str) -> None:
        """Schreibt einen Fehler in das QGIS-Log."""
        QgsMessageLog.logMessage(msg, TAG, Qgis.Critical)

    def getTargetCrs(self) -> int | None:
        """Gibt den ausgewählten CRS EPSG-SRID oder das Projekt-KBS zurück.

        Returns:
            EPSG-SRID als int, oder None wenn nicht verfügbar.
        """
        crs = self.dock.get_selected_crs()
        if crs is None:
            crs = QgsProject.instance().crs()
        return crs.postgisSrid()
    
    def getSourceCrs(self) -> int | None:
        """
        Returns the selected source CRS EPSG SRID, or None if 'automatic'.
        """
        crs = self.dock.get_selected_source_crs()
        if crs is None:
            return None
        return crs.postgisSrid()
    
    def prefillSourceCrs(self, epsg: int | None) -> None:
        """
        Prefills the source CRS UI using an EPSG code detected from IFC analysis.
        """
        self.dock.set_source_epsg_prefill(epsg)
