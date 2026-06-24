# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QRadioButton,
    QCheckBox,
    QPushButton,
    QProgressBar,
    QButtonGroup,
    QSizePolicy,
)
from qgis.gui import QgsFileWidget

from qgis.core import QgsCoordinateReferenceSystem, QgsProject
from qgis.gui import QgsProjectionSelectionWidget
from qgis.PyQt.QtWidgets import QComboBox
import json
import os


class IfcToCityGmlDockWidget(QDockWidget):

    def __init__(self, parent=None):
        super().__init__("IFC-to-CityGML", parent)
        
        self._projections_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "view",
        "projections.json",
        )
        
        self.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetClosable
            | QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
        )

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # --- Input group ---
        self.groupBox_ifc = QGroupBox("Eingabeformat: IFC")
        ifc_layout = QVBoxLayout(self.groupBox_ifc)
        ifc_layout.setSpacing(6)

        self.fileWidget_ifc = QgsFileWidget()
        self.fileWidget_ifc.setFilter(
            "Industry Foundation Classes (*.ifc)"
        )
        self.fileWidget_ifc.setUseLink(False)
        self.fileWidget_ifc.lineEdit().setReadOnly(False)
        ifc_layout.addWidget(self.fileWidget_ifc)
        
        # --- Source CRS selection (IFC) ---
        src_crs_title = QLabel("Quell-Koordinatensystem")
        src_crs_font = self.groupBox_ifc.font()
        src_crs_font.setBold(True)
        src_crs_font.setWeight(75)
        src_crs_title.setFont(src_crs_font)
        src_crs_title.setStyleSheet("font-weight: 700;")
        ifc_layout.addWidget(src_crs_title)

        src_crs_layout = QHBoxLayout()
        src_crs_layout.setSpacing(2)

        self.comboBox_src_crs = QComboBox()
        self.comboBox_src_crs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Mapping label -> epsg (None=current project, -1=custom, >=0 fixed EPSG)
        self._src_crs_epsg_map: dict[str, int | None] = {}

        # Special entry: detected from IFC (filled later by analyzer)
        self._src_crs_detected_label_base = "Aus IFC-Datei"
        detected_label = f"{self._src_crs_detected_label_base} (Nicht Erkannt)"
        self.comboBox_src_crs.addItem(detected_label)
        self._src_crs_epsg_map[detected_label] = None  # will be updated when detected

        # self.comboBox_src_crs.addItem("Aktuelles KBS")
        # self._src_crs_epsg_map["Aktuelles KBS"] = None

        # Reuse projections.json
        # if os.path.isfile(self._projections_path):
        #   with open(self._projections_path, "r", encoding="utf-8") as f:
        #       projections: dict[str, int] = json.load(f)
        #   for name, epsg in projections.items():
        #       label = f"{name} (EPSG:{epsg})"
        #       self.comboBox_src_crs.addItem(label)
        #       self._src_crs_epsg_map[label] = epsg

        self.comboBox_src_crs.addItem("Benutzerdefiniert...")
        self._src_crs_epsg_map["Benutzerdefiniert..."] = -1

        src_crs_layout.addWidget(self.comboBox_src_crs)

        self.srcCrsWidget_custom = QgsProjectionSelectionWidget()
        self.srcCrsWidget_custom.setVisible(False)
        src_crs_layout.addWidget(self.srcCrsWidget_custom)

        self.comboBox_src_crs.currentTextChanged.connect(self._on_src_crs_changed)

        ifc_layout.addLayout(src_crs_layout)

        self.label_ifc_info = QLabel("")
        self.label_ifc_info.setAlignment(
            Qt.AlignLeading | Qt.AlignLeft | Qt.AlignTop
        )
        self.label_ifc_info.setWordWrap(True)
        self.label_ifc_info.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )

        right_layout = QVBoxLayout()
        right_layout.setSpacing(0)
        self.checkBox_val = QCheckBox("optionale IFC‑Validierung")
        #self.checkBox_val.setToolTip(
            #"Führt eine optionale IFC‑Validierung mit ifcopenshell.validate aus und protokolliert gefundene Fehler."
        #)
        right_layout.addWidget(self.checkBox_val, 0, Qt.AlignRight)

        self.label_ifc_status = QLabel("")
        status_font = self.checkBox_val.font()
        status_font.setBold(True)
        self.label_ifc_status.setFont(status_font)
        self.label_ifc_status.setTextFormat(Qt.PlainText)
        self.label_ifc_status.setAlignment(Qt.AlignRight | Qt.AlignTop)
        right_layout.addWidget(self.label_ifc_status, 0, Qt.AlignRight)
        right_layout.addStretch()

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        right_widget.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Minimum
        )

        info_row = QHBoxLayout()
        info_row.setSpacing(0)
        info_row.setContentsMargins(0, 0, 0, 0)
        info_row.addWidget(self.label_ifc_info, 1)
        info_row.addWidget(
            right_widget, 0, Qt.AlignTop | Qt.AlignRight
        )
        ifc_layout.addLayout(info_row)

        self.label_ifc_msg = QLabel("")
        self.label_ifc_msg.setTextFormat(Qt.PlainText)
        self.label_ifc_msg.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.label_ifc_msg.setWordWrap(True)
        self.label_ifc_msg.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )
        ifc_layout.addWidget(self.label_ifc_msg)

        main_layout.addWidget(self.groupBox_ifc)
        main_layout.addSpacing(8)

        # --- Output group ---
        self.groupBox_cgml = QGroupBox("Ausgabeformat: CityGML 2.0")
        cgml_layout = QVBoxLayout(self.groupBox_cgml)
        cgml_layout.setSpacing(6)

        self.fileWidget_cgml = QgsFileWidget()
        self.fileWidget_cgml.setFilter(
            "Geography Markup Language (*.gml)"
        )
        self.fileWidget_cgml.setStorageMode(QgsFileWidget.SaveFile)
        self.fileWidget_cgml.setUseLink(False)
        self.fileWidget_cgml.lineEdit().setReadOnly(False)
        cgml_layout.addWidget(self.fileWidget_cgml)
        
        # --- CRS selection ---
        crs_title = QLabel("Ziel-Koordinatensystem")
        crs_font = self.groupBox_cgml.font()
        crs_font.setBold(True)
        crs_font.setWeight(75)
        crs_title.setFont(crs_font)
        crs_title.setStyleSheet("font-weight: 700;")
        cgml_layout.addWidget(crs_title)

        crs_layout = QHBoxLayout()
        crs_layout.setSpacing(2)

        self.comboBox_crs = QComboBox()
        self.comboBox_crs.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )

        self._crs_epsg_map: dict[str, int | None] = {}
        self.comboBox_crs.addItem("Aktuelles KBS")
        self._crs_epsg_map["Aktuelles KBS"] = None

        if os.path.isfile(self._projections_path):
            with open(self._projections_path, "r", encoding="utf-8") as f:
                projections: dict[str, int] = json.load(f)
            for name, epsg in projections.items():
                label = f"{name} (EPSG:{epsg})"
                self.comboBox_crs.addItem(label)
                self._crs_epsg_map[label] = epsg

        self.comboBox_crs.addItem("Benutzerdefiniert...")
        self._crs_epsg_map["Benutzerdefiniert..."] = -1

        crs_layout.addWidget(self.comboBox_crs)

        self.crsWidget_custom = QgsProjectionSelectionWidget()
        self.crsWidget_custom.setVisible(False)
        crs_layout.addWidget(self.crsWidget_custom)

        self.comboBox_crs.currentTextChanged.connect(
            self._on_crs_changed
        )

        cgml_layout.addLayout(crs_layout)

        cgml_layout.addSpacing(12)

        options_layout = QHBoxLayout()
        options_layout.setSpacing(12)

        # LoD radio buttons
        self.groupBox_lod = QGroupBox("Level of Detail")
        lod_layout = QVBoxLayout(self.groupBox_lod)
        lod_layout.setSpacing(2)

        self.lod_button_group = QButtonGroup(self)
        self.radioButton_lod0 = QRadioButton("LoD 0")
        self.radioButton_lod1 = QRadioButton("LoD 1")
        self.radioButton_lod2 = QRadioButton("LoD 2")
        self.radioButton_lod3 = QRadioButton("LoD 3")
        self.radioButton_lod4 = QRadioButton("LoD 4")
        self.radioButton_lod0.setChecked(True)
        self.radioButton_lod4.setDisabled(True)

        for idx, btn in enumerate(
            [
                self.radioButton_lod0,
                self.radioButton_lod1,
                self.radioButton_lod2,
                self.radioButton_lod3,
                self.radioButton_lod4,
            ]
        ):
            self.lod_button_group.addButton(btn, idx)
            lod_layout.addWidget(btn)

        self.groupBox_lod.setMinimumHeight(
            self.groupBox_lod.sizeHint().height()
        )

        options_layout.addWidget(self.groupBox_lod)
        options_layout.addStretch()

        # Extra options
        extra_layout = QVBoxLayout()
        extra_layout.setSpacing(2)
        self.checkBox_eade = QCheckBox("EnergyADE")
        self.checkBox_integr = QCheckBox("Integration in QGIS")
        extra_layout.addWidget(self.checkBox_eade, 0, Qt.AlignRight)
        extra_layout.addWidget(self.checkBox_integr, 0, Qt.AlignRight)
        extra_layout.addStretch()
        options_layout.addLayout(extra_layout)

        cgml_layout.addLayout(options_layout)
        main_layout.addWidget(self.groupBox_cgml)

        # --- Progress bar ---
        self.progressBar = QProgressBar()
        self.progressBar.setEnabled(False)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)
        self.progressBar.setVisible(False)
        main_layout.addWidget(self.progressBar)

        # --- Buttons ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.button_run = QPushButton("Ausführen")
        self.button_run.setEnabled(True)
        self.button_run.setFocusPolicy(Qt.NoFocus)
        button_layout.addWidget(self.button_run)

        self.button_close = QPushButton("Schließen")
        self.button_close.setFocusPolicy(Qt.NoFocus)
        button_layout.addWidget(self.button_close)
        main_layout.addLayout(button_layout)

        main_layout.addStretch()
        container.setMaximumHeight(700)
        self.setWidget(container)

    def _on_crs_changed(self, text: str) -> None:
        is_custom = text == "Benutzerdefiniert..."
        self.crsWidget_custom.setVisible(is_custom)

    def get_selected_crs(self,) -> QgsCoordinateReferenceSystem | None:
        text = self.comboBox_crs.currentText()
        epsg = self._crs_epsg_map.get(text)

        if epsg is None:
            return None
        if epsg == -1:
            return self.crsWidget_custom.crs()
        return QgsCoordinateReferenceSystem(f"EPSG:{epsg}")
    
    def _on_src_crs_changed(self, text: str) -> None:
        is_custom = text == "Benutzerdefiniert..."
        self.srcCrsWidget_custom.setVisible(is_custom)

    def get_selected_source_crs(self) -> QgsCoordinateReferenceSystem | None:
        text = self.comboBox_src_crs.currentText()
        epsg = self._src_crs_epsg_map.get(text)

        if epsg is None:
            return None
        if epsg == -1:
            return self.srcCrsWidget_custom.crs()
        return QgsCoordinateReferenceSystem(f"EPSG:{epsg}")

    def set_source_epsg_prefill(self, epsg: int | None) -> None:
        """
        Updates the 'source CRS' combobox with detected EPSG and selects it.
        """
        old_label = self.comboBox_src_crs.itemText(0)

        if epsg is None:
            new_label = f"{self._src_crs_detected_label_base} (Nicht Erkannt)"
            self.comboBox_src_crs.setItemText(0, new_label)
            self._src_crs_epsg_map.pop(old_label, None)
            self._src_crs_epsg_map[new_label] = None
            self.comboBox_src_crs.setCurrentIndex(0)
            return

        epsg_int = int(epsg)
        new_label = f"{self._src_crs_detected_label_base} (EPSG:{epsg_int})"
        self.comboBox_src_crs.setItemText(0, new_label)

        self._src_crs_epsg_map.pop(old_label, None)
        self._src_crs_epsg_map[new_label] = epsg_int

        self.comboBox_src_crs.setCurrentIndex(0)


