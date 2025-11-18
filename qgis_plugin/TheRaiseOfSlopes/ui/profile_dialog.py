# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                                 QLabel, QComboBox, QFileDialog, QTabWidget,
                                 QWidget, QFormLayout, QDoubleSpinBox, QSpinBox,
                                 QGroupBox, QTextEdit, QListWidget, QListWidgetItem,
                                 QCheckBox, QRadioButton, QButtonGroup)
from qgis.core import QgsProject

# Matplotlib embedding
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ProfileDialog(QDialog):
    """Dialog principale per configurare e visualizzare il profilo.

    Segnali:
      - startSelectionRequested: l'utente chiede di selezionare i due punti sulla mappa
      - computeProfileRequested: richiesto il calcolo del profilo (passa layer raster e punti)
      - exportRequested: richiesto export CSV
    """
    startSelectionRequested = pyqtSignal()
    computeProfileRequested = pyqtSignal(object, object, object)  # raster_layer, p1, p2
    exportRequested = pyqtSignal(str)
    gridStabilityAnalysisRequested = pyqtSignal(dict)  # parametri per analisi griglia
    simplexStabilityAnalysisRequested = pyqtSignal(dict)  # parametri per analisi simplex
    clearSurfacesRequested = pyqtSignal()  # richiesta pulizia superfici dal grafico

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Profilo Terreno - The Raise Of Slopes")
        self._raster_layer = None
        self._p1 = None
        self._p2 = None
        self._last_profile_distances = []
        self._last_profile_elevations = []
        self._last_surfaces_list = None
        self._plugin = None  # Riferimento al plugin per accedere ai metodi di calcolo
        self._build_ui()
    
    def set_plugin(self, plugin):
        """Imposta il riferimento al plugin principale."""
        self._plugin = plugin

    def _build_ui(self):
        """Costruisce i widget dell'interfaccia con schede per profilo e analisi stabilità."""
        layout = QVBoxLayout(self)
        
        # Crea il widget a schede
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Prima scheda: Profilo altimetrico
        self._create_profile_tab()
        
        # Seconda scheda: Parametri geotecnici (condivisi)
        self._create_soil_parameters_tab()
        
        # Terza scheda: Stratigrafia e Falda
        self._create_stratigraphy_tab()
        
        # Quarta scheda: Analisi di stabilità con Griglia
        self._create_grid_stability_tab()
        
        # Quinta scheda: Analisi di stabilità con Simplex
        self._create_simplex_stability_tab()
        
        # Status bar comune
        self.lblStatus = QLabel("")
        layout.addWidget(self.lblStatus)
        
        self._reload_rasters()

    def _create_profile_tab(self):
        """Crea la scheda per il calcolo del profilo altimetrico."""
        profile_widget = QWidget()
        layout = QVBoxLayout(profile_widget)

        # Selezione DEM
        hl = QHBoxLayout()
        hl.addWidget(QLabel("DEM:"))
        self.cboRaster = QComboBox()
        hl.addWidget(self.cboRaster)
        self.btnReload = QPushButton("Aggiorna")
        self.btnReload.clicked.connect(self._reload_rasters)
        hl.addWidget(self.btnReload)
        layout.addLayout(hl)

        # Selezione punti
        self.btnSelect = QPushButton("Seleziona 2 punti")
        self.btnSelect.clicked.connect(self.startSelectionRequested.emit)
        layout.addWidget(self.btnSelect)

        self.lblPoints = QLabel("P1: -  P2: -")
        layout.addWidget(self.lblPoints)

        # Calcolo profilo: rimosso il pulsante, calcolo automatico al secondo punto

        # Grafico
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Azioni profilo
        hl_actions = QHBoxLayout()
        self.btnClearSurfaces = QPushButton("Pulisci superfici")
        self.btnClearSurfaces.clicked.connect(self.clearSurfacesRequested.emit)
        hl_actions.addWidget(self.btnClearSurfaces)

        self.btnExport = QPushButton("Esporta CSV")
        self.btnExport.clicked.connect(self._do_export)
        hl_actions.addWidget(self.btnExport)
        layout.addLayout(hl_actions)

        # Visibilità superfici
        vis_group = QGroupBox("Visibilità superfici")
        vis_layout = QVBoxLayout(vis_group)
        self.surface_visibility_list = QListWidget()
        self.surface_visibility_list.itemChanged.connect(self._on_surface_visibility_changed)
        vis_layout.addWidget(self.surface_visibility_list)
        layout.addWidget(vis_group)
        
        self.tab_widget.addTab(profile_widget, "Profilo Altimetrico")

    def _create_soil_parameters_tab(self):
        """Crea la scheda per i parametri geotecnici (condivisi tra griglia e simplex)."""
        soil_widget = QWidget()
        layout = QVBoxLayout(soil_widget)
        
        # Gruppo parametri del terreno
        soil_group = QGroupBox("Parametri Geotecnici del Terreno")
        soil_layout = QFormLayout(soil_group)
        
        # Peso specifico
        self.gamma_spinbox = QDoubleSpinBox()
        self.gamma_spinbox.setRange(10.0, 30.0)
        self.gamma_spinbox.setValue(20.0)
        self.gamma_spinbox.setSuffix(" kN/m³")
        self.gamma_spinbox.setDecimals(1)
        soil_layout.addRow("Peso specifico (γ):", self.gamma_spinbox)
        
        # Coesione
        self.cohesion_spinbox = QDoubleSpinBox()
        self.cohesion_spinbox.setRange(0.0, 100.0)
        self.cohesion_spinbox.setValue(10.0)
        self.cohesion_spinbox.setSuffix(" kPa")
        self.cohesion_spinbox.setDecimals(1)
        soil_layout.addRow("Coesione (c):", self.cohesion_spinbox)
        
        # Porosità
        self.porosity_spinbox = QDoubleSpinBox()
        self.porosity_spinbox.setRange(0.0, 1.0)
        self.porosity_spinbox.setValue(0.3)
        self.porosity_spinbox.setDecimals(2)
        self.porosity_spinbox.setSingleStep(0.05)
        soil_layout.addRow("Porosità (n):", self.porosity_spinbox)
        
        # Angolo di attrito
        self.friction_angle_spinbox = QDoubleSpinBox()
        self.friction_angle_spinbox.setRange(0.0, 45.0)
        self.friction_angle_spinbox.setValue(25.0)
        self.friction_angle_spinbox.setSuffix(" °")
        self.friction_angle_spinbox.setDecimals(1)
        soil_layout.addRow("Angolo di attrito (φ):", self.friction_angle_spinbox)
        
        layout.addWidget(soil_group)
        
        # Gruppo parametri dell'analisi (comuni)
        analysis_group = QGroupBox("Parametri dell'Analisi")
        analysis_layout = QFormLayout(analysis_group)
        
        # Numero di conci
        self.slices_spinbox = QSpinBox()
        self.slices_spinbox.setRange(10, 100)
        self.slices_spinbox.setValue(50)
        analysis_layout.addRow("Numero di conci:", self.slices_spinbox)
        
        # Profondità della superficie di scivolamento
        self.depth_factor_spinbox = QDoubleSpinBox()
        self.depth_factor_spinbox.setRange(0.1, 2.0)
        self.depth_factor_spinbox.setValue(0.5)
        self.depth_factor_spinbox.setDecimals(2)
        analysis_layout.addRow("Fattore profondità:", self.depth_factor_spinbox)
        
        layout.addWidget(analysis_group)
        
        # Gruppo parametri secondo strato
        layer2_group = QGroupBox("Parametri Geotecnici Secondo Strato (opzionale)")
        layer2_layout = QFormLayout(layer2_group)
        
        self.gamma_2_spinbox = QDoubleSpinBox()
        self.gamma_2_spinbox.setRange(10.0, 30.0)
        self.gamma_2_spinbox.setValue(22.0)
        self.gamma_2_spinbox.setSuffix(" kN/m³")
        self.gamma_2_spinbox.setDecimals(1)
        layer2_layout.addRow("Peso specifico (γ₂):", self.gamma_2_spinbox)
        
        self.cohesion_2_spinbox = QDoubleSpinBox()
        self.cohesion_2_spinbox.setRange(0.0, 1000.0)
        self.cohesion_2_spinbox.setValue(50.0)
        self.cohesion_2_spinbox.setSuffix(" kPa")
        self.cohesion_2_spinbox.setDecimals(1)
        layer2_layout.addRow("Coesione (c₂):", self.cohesion_2_spinbox)
        
        # Porosità secondo strato
        self.porosity_2_spinbox = QDoubleSpinBox()
        self.porosity_2_spinbox.setRange(0.0, 1.0)
        self.porosity_2_spinbox.setValue(0.25)
        self.porosity_2_spinbox.setDecimals(2)
        self.porosity_2_spinbox.setSingleStep(0.05)
        layer2_layout.addRow("Porosità (n₂):", self.porosity_2_spinbox)
        
        self.friction_angle_2_spinbox = QDoubleSpinBox()
        self.friction_angle_2_spinbox.setRange(0.0, 45.0)
        self.friction_angle_2_spinbox.setValue(30.0)
        self.friction_angle_2_spinbox.setSuffix(" °")
        self.friction_angle_2_spinbox.setDecimals(1)
        layer2_layout.addRow("Angolo di attrito (φ₂):", self.friction_angle_2_spinbox)
        
        layout.addWidget(layer2_group)
        
        # Aggiungi uno stretch per spingere tutto in alto
        layout.addStretch()
        
        self.tab_widget.addTab(soil_widget, "Parametri Geotecnici")

    def _create_stratigraphy_tab(self):
        """Crea la scheda per la configurazione di stratigrafia e falda."""
        strat_widget = QWidget()
        layout = QVBoxLayout(strat_widget)
        
        # Gruppo secondo strato
        layer2_group = QGroupBox("Secondo Strato")
        layer2_layout = QVBoxLayout(layer2_group)
        
        # Checkbox per abilitare secondo strato
        self.enable_layer2_checkbox = QCheckBox("Abilita secondo strato")
        self.enable_layer2_checkbox.stateChanged.connect(self._on_layer2_enabled_changed)
        layer2_layout.addWidget(self.enable_layer2_checkbox)
        
        # Widget container per parametri secondo strato
        self.layer2_params_widget = QWidget()
        layer2_params_layout = QFormLayout(self.layer2_params_widget)
        
        # Modalità definizione interfaccia
        interface_group = QGroupBox("Definizione Interfaccia Strato")
        interface_layout = QVBoxLayout(interface_group)
        
        self.layer2_definition_group = QButtonGroup()
        
        self.layer2_const_depth_radio = QRadioButton("Profondità costante dal piano campagna")
        self.layer2_definition_group.addButton(self.layer2_const_depth_radio, 0)
        interface_layout.addWidget(self.layer2_const_depth_radio)
        
        self.layer2_const_depth_spinbox = QDoubleSpinBox()
        self.layer2_const_depth_spinbox.setRange(0.1, 100.0)
        self.layer2_const_depth_spinbox.setValue(5.0)
        self.layer2_const_depth_spinbox.setSuffix(" m")
        self.layer2_const_depth_spinbox.setDecimals(2)
        self.layer2_const_depth_spinbox.valueChanged.connect(self._refresh_profile_display)
        interface_layout.addWidget(self.layer2_const_depth_spinbox)
        
        self.layer2_raster_depth_radio = QRadioButton("Profondità da raster")
        self.layer2_definition_group.addButton(self.layer2_raster_depth_radio, 1)
        interface_layout.addWidget(self.layer2_raster_depth_radio)
        
        self.layer2_raster_combo = QComboBox()
        self.layer2_raster_combo.currentIndexChanged.connect(self._refresh_profile_display)
        interface_layout.addWidget(self.layer2_raster_combo)
        
        self.layer2_elevation_radio = QRadioButton("Quota assoluta")
        self.layer2_definition_group.addButton(self.layer2_elevation_radio, 2)
        interface_layout.addWidget(self.layer2_elevation_radio)
        
        self.layer2_elevation_spinbox = QDoubleSpinBox()
        self.layer2_elevation_spinbox.setRange(-1000.0, 10000.0)
        self.layer2_elevation_spinbox.setValue(0.0)
        self.layer2_elevation_spinbox.setSuffix(" m")
        self.layer2_elevation_spinbox.setDecimals(2)
        self.layer2_elevation_spinbox.valueChanged.connect(self._refresh_profile_display)
        interface_layout.addWidget(self.layer2_elevation_spinbox)
        
        self.layer2_const_depth_radio.setChecked(True)
        self.layer2_definition_group.buttonClicked.connect(self._on_layer2_definition_changed)
        
        layer2_params_layout.addRow(interface_group)
        
        layer2_layout.addWidget(self.layer2_params_widget)
        self.layer2_params_widget.setEnabled(False)
        
        layout.addWidget(layer2_group)
        
        # Gruppo falda
        water_group = QGroupBox("Falda Freatica")
        water_layout = QVBoxLayout(water_group)
        
        self.enable_water_checkbox = QCheckBox("Abilita falda")
        self.enable_water_checkbox.stateChanged.connect(self._on_water_enabled_changed)
        water_layout.addWidget(self.enable_water_checkbox)
        
        self.water_params_widget = QWidget()
        water_params_layout = QFormLayout(self.water_params_widget)
        
        # Modalità definizione falda
        water_def_group = QGroupBox("Definizione Falda")
        water_def_layout = QVBoxLayout(water_def_group)
        
        self.water_definition_group = QButtonGroup()
        
        self.water_const_depth_radio = QRadioButton("Profondità costante dal piano campagna")
        self.water_definition_group.addButton(self.water_const_depth_radio, 0)
        water_def_layout.addWidget(self.water_const_depth_radio)
        
        self.water_const_depth_spinbox = QDoubleSpinBox()
        self.water_const_depth_spinbox.setRange(0.0, 100.0)
        self.water_const_depth_spinbox.setValue(2.0)
        self.water_const_depth_spinbox.setSuffix(" m")
        self.water_const_depth_spinbox.setDecimals(2)
        self.water_const_depth_spinbox.valueChanged.connect(self._refresh_profile_display)
        water_def_layout.addWidget(self.water_const_depth_spinbox)
        
        self.water_raster_depth_radio = QRadioButton("Profondità da raster")
        self.water_definition_group.addButton(self.water_raster_depth_radio, 1)
        water_def_layout.addWidget(self.water_raster_depth_radio)
        
        self.water_raster_combo = QComboBox()
        self.water_raster_combo.currentIndexChanged.connect(self._refresh_profile_display)
        water_def_layout.addWidget(self.water_raster_combo)
        
        self.water_elevation_radio = QRadioButton("Quota assoluta")
        self.water_definition_group.addButton(self.water_elevation_radio, 2)
        water_def_layout.addWidget(self.water_elevation_radio)
        
        self.water_elevation_spinbox = QDoubleSpinBox()
        self.water_elevation_spinbox.setRange(-1000.0, 10000.0)
        self.water_elevation_spinbox.setValue(0.0)
        self.water_elevation_spinbox.setSuffix(" m")
        self.water_elevation_spinbox.setDecimals(2)
        self.water_elevation_spinbox.valueChanged.connect(self._refresh_profile_display)
        water_def_layout.addWidget(self.water_elevation_spinbox)
        
        self.water_const_depth_radio.setChecked(True)
        self.water_definition_group.buttonClicked.connect(self._on_water_definition_changed)
        
        water_params_layout.addRow(water_def_group)
        
        water_layout.addWidget(self.water_params_widget)
        self.water_params_widget.setEnabled(False)
        
        layout.addWidget(water_group)
        
        # Aggiungi uno stretch per spingere tutto in alto
        layout.addStretch()
        
        self.tab_widget.addTab(strat_widget, "Stratigrafia e Falda")
    
    def _on_layer2_enabled_changed(self, state):
        """Gestisce l'abilitazione/disabilitazione dei parametri del secondo strato."""
        self.layer2_params_widget.setEnabled(state == Qt.Checked)
        if state == Qt.Checked:
            self._reload_layer2_rasters()
        # Aggiorna il grafico
        self._refresh_profile_display()
    
    def _on_layer2_definition_changed(self):
        """Aggiorna l'interfaccia in base alla modalità selezionata."""
        selected_id = self.layer2_definition_group.checkedId()
        self.layer2_const_depth_spinbox.setEnabled(selected_id == 0)
        self.layer2_raster_combo.setEnabled(selected_id == 1)
        self.layer2_elevation_spinbox.setEnabled(selected_id == 2)
        # Aggiorna il grafico
        self._refresh_profile_display()
    
    def _on_water_enabled_changed(self, state):
        """Gestisce l'abilitazione/disabilitazione dei parametri della falda."""
        self.water_params_widget.setEnabled(state == Qt.Checked)
        if state == Qt.Checked:
            self._reload_water_rasters()
        # Aggiorna il grafico
        self._refresh_profile_display()
    
    def _on_water_definition_changed(self):
        """Aggiorna l'interfaccia in base alla modalità selezionata per la falda."""
        selected_id = self.water_definition_group.checkedId()
        self.water_const_depth_spinbox.setEnabled(selected_id == 0)
        self.water_raster_combo.setEnabled(selected_id == 1)
        self.water_elevation_spinbox.setEnabled(selected_id == 2)
        # Aggiorna il grafico
        self._refresh_profile_display()
    
    def _reload_layer2_rasters(self):
        """Popola la combo per il raster del secondo strato."""
        self.layer2_raster_combo.clear()
        for lyr in QgsProject.instance().mapLayers().values():
            try:
                if lyr.type() == lyr.RasterLayer:
                    self.layer2_raster_combo.addItem(lyr.name(), lyr)
            except Exception:
                continue
    
    def _reload_water_rasters(self):
        """Popola la combo per il raster della falda."""
        self.water_raster_combo.clear()
        for lyr in QgsProject.instance().mapLayers().values():
            try:
                if lyr.type() == lyr.RasterLayer:
                    self.water_raster_combo.addItem(lyr.name(), lyr)
            except Exception:
                continue
    
    def _refresh_profile_display(self):
        """Aggiorna la visualizzazione del profilo con le superfici e stratigrafia correnti."""
        if not self._last_profile_distances or not self._last_profile_elevations:
            return
        
        # Ridisegna usando i dati salvati e le superfici correnti
        self.updateProfile(
            self._last_profile_distances,
            self._last_profile_elevations,
            slip_surfaces_list=self._last_surfaces_list
        )

    def _create_grid_stability_tab(self):
        """Crea la scheda per l'analisi di stabilità con griglia di cerchi (Bishop/GLE)."""
        stability_widget = QWidget()
        layout = QVBoxLayout(stability_widget)
        
        # Gruppo parametri griglia
        grid_group = QGroupBox("Parametri Griglia di Ricerca")
        grid_layout = QFormLayout(grid_group)

        # Metodo di calcolo stabilità
        self.grid_method_combo = QComboBox()
        self.grid_method_combo.addItems(["Bishop", "Morgenstern-Price", "Spencer"])
        grid_layout.addRow("Metodo di calcolo:", self.grid_method_combo)
        
        # Numero punti ingresso
        self.num_in_pts_spinbox = QSpinBox()
        self.num_in_pts_spinbox.setRange(5, 50)
        self.num_in_pts_spinbox.setValue(16)
        grid_layout.addRow("Numero punti ingresso:", self.num_in_pts_spinbox)
        
        # Numero punti uscita
        self.num_out_pts_spinbox = QSpinBox()
        self.num_out_pts_spinbox.setRange(5, 50)
        self.num_out_pts_spinbox.setValue(16)
        grid_layout.addRow("Numero punti uscita:", self.num_out_pts_spinbox)
        
        # Incremento minimo eta
        self.min_eta_inc_spinbox = QDoubleSpinBox()
        self.min_eta_inc_spinbox.setRange(1.0, 20.0)
        self.min_eta_inc_spinbox.setValue(5.0)
        self.min_eta_inc_spinbox.setSuffix(" °")
        self.min_eta_inc_spinbox.setDecimals(1)
        grid_layout.addRow("Incremento minimo η:", self.min_eta_inc_spinbox)
        
        # Intervallo ingresso (frazione del profilo)
        self.in_interval_min_spinbox = QDoubleSpinBox()
        self.in_interval_min_spinbox.setRange(0.0, 1.0)
        self.in_interval_min_spinbox.setValue(0.6)
        self.in_interval_min_spinbox.setDecimals(2)
        grid_layout.addRow("Ingresso - min (frazione):", self.in_interval_min_spinbox)
        
        self.in_interval_max_spinbox = QDoubleSpinBox()
        self.in_interval_max_spinbox.setRange(0.0, 1.0)
        self.in_interval_max_spinbox.setValue(1.0)
        self.in_interval_max_spinbox.setDecimals(2)
        grid_layout.addRow("Ingresso - max (frazione):", self.in_interval_max_spinbox)
        
        # Intervallo uscita (frazione del profilo)
        self.out_interval_min_spinbox = QDoubleSpinBox()
        self.out_interval_min_spinbox.setRange(0.0, 1.0)
        self.out_interval_min_spinbox.setValue(0.0)
        self.out_interval_min_spinbox.setDecimals(2)
        grid_layout.addRow("Uscita - min (frazione):", self.out_interval_min_spinbox)
        
        self.out_interval_max_spinbox = QDoubleSpinBox()
        self.out_interval_max_spinbox.setRange(0.0, 1.0)
        self.out_interval_max_spinbox.setValue(0.4)
        self.out_interval_max_spinbox.setDecimals(2)
        grid_layout.addRow("Uscita - max (frazione):", self.out_interval_max_spinbox)
        
        layout.addWidget(grid_group)
        
        # Pulsante calcolo
        self.btnGridStabilityAnalysis = QPushButton("Esegui Analisi Griglia")
        self.btnGridStabilityAnalysis.clicked.connect(self._emit_grid_stability_analysis)
        layout.addWidget(self.btnGridStabilityAnalysis)
        
        # Area risultati
        results_group = QGroupBox("Risultati")
        results_layout = QVBoxLayout(results_group)
        
        self.grid_results_text = QTextEdit()
        self.grid_results_text.setMaximumHeight(150)
        self.grid_results_text.setPlainText("Nessuna analisi eseguita")
        results_layout.addWidget(self.grid_results_text)
        
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(stability_widget, "Analisi Griglia")

    def _create_simplex_stability_tab(self):
        """Crea la scheda per l'analisi di stabilità con ottimizzazione simplex."""
        stability_widget = QWidget()
        layout = QVBoxLayout(stability_widget)
        
        # Gruppo bounds ottimizzazione simplex
        bounds_group = QGroupBox("Bounds Ottimizzazione Simplex")
        bounds_layout = QFormLayout(bounds_group)

        # Metodo di calcolo stabilità
        self.simplex_method_combo = QComboBox()
        self.simplex_method_combo.addItems(["Bishop", "Morgenstern-Price", "Spencer"])
        bounds_layout.addRow("Metodo di calcolo:", self.simplex_method_combo)
        
        # x_in bounds (frazione del profilo)
        self.x_in_min_spinbox = QDoubleSpinBox()
        self.x_in_min_spinbox.setRange(0.0, 1.0)
        self.x_in_min_spinbox.setValue(0.5)
        self.x_in_min_spinbox.setDecimals(2)
        bounds_layout.addRow("x_in - min (frazione):", self.x_in_min_spinbox)
        
        self.x_in_max_spinbox = QDoubleSpinBox()
        self.x_in_max_spinbox.setRange(0.0, 1.0)
        self.x_in_max_spinbox.setValue(1.0)
        self.x_in_max_spinbox.setDecimals(2)
        bounds_layout.addRow("x_in - max (frazione):", self.x_in_max_spinbox)
        
        # x_out bounds (frazione del profilo)
        self.x_out_min_spinbox = QDoubleSpinBox()
        self.x_out_min_spinbox.setRange(0.0, 1.0)
        self.x_out_min_spinbox.setValue(0.0)
        self.x_out_min_spinbox.setDecimals(2)
        bounds_layout.addRow("x_out - min (frazione):", self.x_out_min_spinbox)
        
        self.x_out_max_spinbox = QDoubleSpinBox()
        self.x_out_max_spinbox.setRange(0.0, 1.0)
        self.x_out_max_spinbox.setValue(0.5)
        self.x_out_max_spinbox.setDecimals(2)
        bounds_layout.addRow("x_out - max (frazione):", self.x_out_max_spinbox)
        
        # eta bounds (gradi)
        self.eta_min_spinbox = QDoubleSpinBox()
        self.eta_min_spinbox.setRange(0.0, 90.0)
        self.eta_min_spinbox.setValue(0.0)
        self.eta_min_spinbox.setSuffix(" °")
        self.eta_min_spinbox.setDecimals(1)
        bounds_layout.addRow("η - min:", self.eta_min_spinbox)
        
        self.eta_max_spinbox = QDoubleSpinBox()
        self.eta_max_spinbox.setRange(0.0, 90.0)
        self.eta_max_spinbox.setValue(90.0)
        self.eta_max_spinbox.setSuffix(" °")
        self.eta_max_spinbox.setDecimals(1)
        bounds_layout.addRow("η - max:", self.eta_max_spinbox)
        
        layout.addWidget(bounds_group)
        
        # Gruppo parametri ottimizzazione
        optimization_group = QGroupBox("Parametri Ottimizzazione")
        optimization_layout = QFormLayout(optimization_group)
        
        # Numero massimo iterazioni
        self.max_iterations_spinbox = QSpinBox()
        self.max_iterations_spinbox.setRange(50, 1000)
        self.max_iterations_spinbox.setValue(300)
        optimization_layout.addRow("Iterazioni massime:", self.max_iterations_spinbox)
        
        layout.addWidget(optimization_group)
        
        # Pulsante calcolo
        self.btnSimplexStabilityAnalysis = QPushButton("Esegui Analisi Simplex")
        self.btnSimplexStabilityAnalysis.clicked.connect(self._emit_simplex_stability_analysis)
        layout.addWidget(self.btnSimplexStabilityAnalysis)
        
        # Area risultati
        results_group = QGroupBox("Risultati")
        results_layout = QVBoxLayout(results_group)
        
        self.simplex_results_text = QTextEdit()
        self.simplex_results_text.setMaximumHeight(150)
        self.simplex_results_text.setPlainText("Nessuna analisi eseguita")
        results_layout.addWidget(self.simplex_results_text)
        
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(stability_widget, "Analisi Simplex")

    def _reload_rasters(self):
        """Popola la combo con i raster presenti nel progetto (solo layer di tipo Raster)."""
        self.cboRaster.clear()
        for lyr in QgsProject.instance().mapLayers().values():
            # Uso attributi robusti per raster
            try:
                if lyr.type() == lyr.RasterLayer:
                    self.cboRaster.addItem(lyr.name(), lyr)
            except Exception:
                continue

    def setSelectedPoints(self, p1, p2):
        self._p1, self._p2 = p1, p2
        self.lblPoints.setText(f"P1: ({p1.x():.2f},{p1.y():.2f})  P2: ({p2.x():.2f},{p2.y():.2f})")

    def _emit_compute(self):
        # Obsoleto: il profilo viene calcolato automaticamente al secondo punto
        raster_layer = self.cboRaster.currentData()
        self.computeProfileRequested.emit(raster_layer, self._p1, self._p2)

    def _emit_grid_stability_analysis(self):
        """Raccoglie i parametri e emette il segnale per l'analisi di stabilità con griglia."""
        x_max = self.profile_distances[-1] if hasattr(self, 'profile_distances') and self.profile_distances else 100.0
        
        params = {
            'analysis_type': 'grid',
            'stability_method': self.grid_method_combo.currentText(),
            'gamma': self.gamma_spinbox.value(),
            'cohesion': self.cohesion_spinbox.value(),
            'porosity': self.porosity_spinbox.value(),
            'friction_angle': self.friction_angle_spinbox.value(),
            'num_slices': self.slices_spinbox.value(),
            'depth_factor': self.depth_factor_spinbox.value(),
            'num_in_pts': self.num_in_pts_spinbox.value(),
            'num_out_pts': self.num_out_pts_spinbox.value(),
            'min_eta_inc': self.min_eta_inc_spinbox.value(),
            'in_interval_min': self.in_interval_min_spinbox.value(),
            'in_interval_max': self.in_interval_max_spinbox.value(),
            'out_interval_min': self.out_interval_min_spinbox.value(),
            'out_interval_max': self.out_interval_max_spinbox.value(),
        }
        
        # Aggiungi parametri stratigrafia
        params.update(self._get_stratigraphy_params())
        
        self.gridStabilityAnalysisRequested.emit(params)

    def _emit_simplex_stability_analysis(self):
        """Raccoglie i parametri e emette il segnale per l'analisi di stabilità con simplex."""
        params = {
            'analysis_type': 'simplex',
            'stability_method': self.simplex_method_combo.currentText(),
            'gamma': self.gamma_spinbox.value(),
            'cohesion': self.cohesion_spinbox.value(),
            'porosity': self.porosity_spinbox.value(),
            'friction_angle': self.friction_angle_spinbox.value(),
            'num_slices': self.slices_spinbox.value(),
            'depth_factor': self.depth_factor_spinbox.value(),
            'x_in_min': self.x_in_min_spinbox.value(),
            'x_in_max': self.x_in_max_spinbox.value(),
            'x_out_min': self.x_out_min_spinbox.value(),
            'x_out_max': self.x_out_max_spinbox.value(),
            'eta_min': self.eta_min_spinbox.value(),
            'eta_max': self.eta_max_spinbox.value(),
            'max_iterations': self.max_iterations_spinbox.value(),
        }
        
        # Aggiungi parametri stratigrafia
        params.update(self._get_stratigraphy_params())
        
        self.simplexStabilityAnalysisRequested.emit(params)

    def updateProfile(self, distances, elevations, slip_surface_points=None, slip_surfaces_list=None):
        """Aggiorna il grafico del profilo.

        Filtra i valori None (nodat / fuori raster). Se nessun dato valido mostra un messaggio.
        
        Args:
            distances: lista delle distanze
            elevations: lista delle quote
            slip_surface_points: tupla (x, y) - superficie singola (deprecato, usa slip_surfaces_list)
            slip_surfaces_list: lista di dizionari con 'x', 'y', 'color', 'label' per più superfici
        """
        if self.figure is None:
            return
        # Salva ultimo profilo
        self._last_profile_distances = list(distances) if distances else []
        self._last_profile_elevations = list(elevations) if elevations else []

        # Se ho nuove superfici, aggiorno l'elenco di visibilità se cambia
        if slip_surfaces_list is not None:
            need_rebuild = False
            if self._last_surfaces_list is None:
                need_rebuild = True
            else:
                old_labels = [s.get('label', '') for s in self._last_surfaces_list]
                new_labels = [s.get('label', '') for s in slip_surfaces_list]
                if len(old_labels) != len(new_labels) or old_labels != new_labels:
                    need_rebuild = True
            self._last_surfaces_list = slip_surfaces_list
            if need_rebuild:
                self._populate_surface_visibility_list(self._last_surfaces_list)
        elif slip_surface_points is None:
            # Nessuna superficie: svuoto lista visibilità
            self._last_surfaces_list = None
            self.surface_visibility_list.clear()

        # Determina superfici visibili
        # Nota: il filtro viene fatto direttamente nel blocco di disegno sottostante

        # Disegno
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        # Filtra valori None mantenendo allineamento
        dist_f = []
        elev_f = []
        for d, z in zip(distances, elevations):
            if z is not None:
                dist_f.append(d)
                elev_f.append(z)
        if dist_f:
            ax.plot(dist_f, elev_f, '-k', linewidth=2, label='Profilo terreno')
        else:
            ax.text(0.5, 0.5, 'Nessun dato valido', ha='center', va='center', transform=ax.transAxes)
        
        # Disegna interfaccia secondo strato se abilitato
        if hasattr(self, 'enable_layer2_checkbox') and self.enable_layer2_checkbox.isChecked() and dist_f:
            layer2_y = self._calculate_layer2_interface(dist_f)
            if layer2_y is not None:
                ax.plot(dist_f, layer2_y, '--b', linewidth=1.5, label='Interfaccia strato 2', alpha=0.7)
        
        # Disegna falda se abilitata
        if hasattr(self, 'enable_water_checkbox') and self.enable_water_checkbox.isChecked() and dist_f:
            water_y = self._calculate_water_table(dist_f)
            if water_y is not None:
                ax.plot(dist_f, water_y, '-.c', linewidth=1.5, label='Falda freatica', alpha=0.7)
        
        # Plotta multiple superfici di scivolamento (priorità)
        if slip_surfaces_list is not None and len(slip_surfaces_list) > 0:
            # Filtra solo le superfici visibili
            visible_indices = [i for i in range(self.surface_visibility_list.count())
                               if self.surface_visibility_list.item(i).checkState() == 2]
            visible_surfaces = [slip_surfaces_list[i] for i in visible_indices if i < len(slip_surfaces_list)]
            
            for surface in visible_surfaces:
                ax.plot(surface['x'], surface['y'], 
                       color=surface.get('color', 'red'), 
                       linewidth=2, 
                       linestyle='-',
                       label=surface.get('label', 'Superficie critica'))
        
        # Fallback: singola superficie (retrocompatibilità)
        elif slip_surface_points is not None:
            slip_x, slip_y = slip_surface_points
            ax.plot(slip_x, slip_y, '-r', linewidth=2, label='Superficie critica')
        
        # Mostra legenda se ci sono elementi da mostrare
        has_legend_items = (
            (slip_surfaces_list is not None and len(slip_surfaces_list) > 0 and visible_surfaces) or
            slip_surface_points is not None or
            (hasattr(self, 'enable_layer2_checkbox') and self.enable_layer2_checkbox.isChecked()) or
            (hasattr(self, 'enable_water_checkbox') and self.enable_water_checkbox.isChecked())
        )
        if has_legend_items:
            ax.legend()
        
        ax.set_xlabel('Distanza [m]')
        ax.set_ylabel('Quota [m]')
        ax.grid(True, linestyle='--', alpha=0.4)
        self.canvas.draw()

    def _populate_surface_visibility_list(self, surfaces_list):
        self.surface_visibility_list.blockSignals(True)
        self.surface_visibility_list.clear()
        for s in surfaces_list:
            label = s.get('label', 'Superficie')
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | 2)  # ItemIsUserCheckable
            item.setCheckState(2)  # Checked
            self.surface_visibility_list.addItem(item)
        self.surface_visibility_list.blockSignals(False)

    def _on_surface_visibility_changed(self, item):
        """Aggiorna la visualizzazione quando cambia la visibilità di una superficie."""
        # Usa _refresh_profile_display per ridisegnare tutto correttamente
        self._refresh_profile_display()

    def _do_export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salva profilo", "profilo.csv", "CSV (*.csv)")
        if path:
            self.exportRequested.emit(path)

    def setStatus(self, msg):
        self.lblStatus.setText(msg)

    def updateStabilityResults(self, results_text, analysis_type='grid'):
        """Aggiorna l'area dei risultati dell'analisi di stabilità.
        
        Args:
            results_text: testo dei risultati
            analysis_type: 'grid' o 'simplex' per selezionare quale area aggiornare
        """
        if analysis_type == 'grid' and hasattr(self, 'grid_results_text'):
            self.grid_results_text.setPlainText(results_text)
        elif analysis_type == 'simplex' and hasattr(self, 'simplex_results_text'):
            self.simplex_results_text.setPlainText(results_text)
            
    def setProfileDistances(self, distances):
        """Salva le distanze del profilo per uso nei calcoli dei parametri."""
        self.profile_distances = distances
    
    def _calculate_layer2_interface(self, x_distances):
        """Calcola le quote dell'interfaccia del secondo strato per la visualizzazione.
        
        Args:
            x_distances: lista di distanze lungo il profilo
            
        Returns:
            lista di quote o None se il calcolo fallisce
        """
        if not self._plugin:
            return None
        
        # Ottieni i parametri di stratigrafia
        params = self._get_stratigraphy_params()
        if not params.get('enable_layer2', False):
            return None
        
        # Usa il metodo del plugin per calcolare il profilo
        return self._plugin.compute_layer2_profile_for_display(params)
    
    def _calculate_water_table(self, x_distances):
        """Calcola le quote della falda per la visualizzazione.
        
        Args:
            x_distances: lista di distanze lungo il profilo
            
        Returns:
            lista di quote o None se il calcolo fallisce
        """
        if not self._plugin:
            return None
        
        # Ottieni i parametri di stratigrafia
        params = self._get_stratigraphy_params()
        if not params.get('enable_water', False):
            return None
        
        # Usa il metodo del plugin per calcolare il profilo
        return self._plugin.compute_water_profile_for_display(params)
    
    def _get_stratigraphy_params(self):
        """Raccoglie i parametri di stratigrafia e falda."""
        params = {}
        
        # Secondo strato
        params['enable_layer2'] = self.enable_layer2_checkbox.isChecked()
        if params['enable_layer2']:
            layer2_def_id = self.layer2_definition_group.checkedId()
            params['layer2_definition_mode'] = layer2_def_id  # 0=const_depth, 1=raster, 2=elevation
            
            if layer2_def_id == 0:  # Profondità costante
                params['layer2_const_depth'] = self.layer2_const_depth_spinbox.value()
            elif layer2_def_id == 1:  # Raster
                params['layer2_raster_layer'] = self.layer2_raster_combo.currentData()
            elif layer2_def_id == 2:  # Quota assoluta
                params['layer2_elevation'] = self.layer2_elevation_spinbox.value()
            
            params['gamma_2'] = self.gamma_2_spinbox.value()
            params['cohesion_2'] = self.cohesion_2_spinbox.value()
            params['porosity_2'] = self.porosity_2_spinbox.value()
            params['friction_angle_2'] = self.friction_angle_2_spinbox.value()
        
        # Falda
        params['enable_water'] = self.enable_water_checkbox.isChecked()
        if params['enable_water']:
            water_def_id = self.water_definition_group.checkedId()
            params['water_definition_mode'] = water_def_id  # 0=const_depth, 1=raster, 2=elevation
            
            if water_def_id == 0:  # Profondità costante
                params['water_const_depth'] = self.water_const_depth_spinbox.value()
            elif water_def_id == 1:  # Raster
                params['water_raster_layer'] = self.water_raster_combo.currentData()
            elif water_def_id == 2:  # Quota assoluta
                params['water_elevation'] = self.water_elevation_spinbox.value()
        
        return params
