# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                                 QLabel, QComboBox, QFileDialog, QTabWidget,
                                 QWidget, QFormLayout, QDoubleSpinBox, QSpinBox,
                                 QGroupBox, QTextEdit)
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
    stabilityAnalysisRequested = pyqtSignal(dict)  # parametri geotecnici

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Profilo Terreno - The Raise Of Slopes")
        self._raster_layer = None
        self._p1 = None
        self._p2 = None
        self._build_ui()

    def _build_ui(self):
        """Costruisce i widget dell'interfaccia con schede per profilo e analisi stabilità."""
        layout = QVBoxLayout(self)
        
        # Crea il widget a schede
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Prima scheda: Profilo altimetrico
        self._create_profile_tab()
        
        # Seconda scheda: Analisi di stabilità
        self._create_stability_tab()
        
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

        # Calcolo profilo
        self.btnCompute = QPushButton("Calcola profilo")
        self.btnCompute.clicked.connect(self._emit_compute)
        layout.addWidget(self.btnCompute)

        # Grafico
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Export
        self.btnExport = QPushButton("Esporta CSV")
        self.btnExport.clicked.connect(self._do_export)
        layout.addWidget(self.btnExport)
        
        self.tab_widget.addTab(profile_widget, "Profilo Altimetrico")

    def _create_stability_tab(self):
        """Crea la scheda per l'analisi di stabilità di Morgenstern & Price."""
        stability_widget = QWidget()
        layout = QVBoxLayout(stability_widget)
        
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
        
        # Aumento coesione con profondità
        self.cohesion_depth_rate_spinbox = QDoubleSpinBox()
        self.cohesion_depth_rate_spinbox.setRange(0.0, 10.0)
        self.cohesion_depth_rate_spinbox.setValue(0.0)
        self.cohesion_depth_rate_spinbox.setSuffix(" kPa/m")
        self.cohesion_depth_rate_spinbox.setDecimals(2)
        soil_layout.addRow("Aumento coesione con profondità:", self.cohesion_depth_rate_spinbox)
        
        # Angolo di attrito
        self.friction_angle_spinbox = QDoubleSpinBox()
        self.friction_angle_spinbox.setRange(0.0, 45.0)
        self.friction_angle_spinbox.setValue(25.0)
        self.friction_angle_spinbox.setSuffix(" °")
        self.friction_angle_spinbox.setDecimals(1)
        soil_layout.addRow("Angolo di attrito (φ):", self.friction_angle_spinbox)
        
        layout.addWidget(soil_group)
        
        # Gruppo parametri dell'analisi
        analysis_group = QGroupBox("Parametri dell'Analisi")
        analysis_layout = QFormLayout(analysis_group)
        
        # Numero di conci
        self.slices_spinbox = QSpinBox()
        self.slices_spinbox.setRange(10, 100)
        self.slices_spinbox.setValue(20)
        analysis_layout.addRow("Numero di conci:", self.slices_spinbox)
        
        # Profondità della superficie di scivolamento
        self.depth_factor_spinbox = QDoubleSpinBox()
        self.depth_factor_spinbox.setRange(0.1, 2.0)
        self.depth_factor_spinbox.setValue(0.5)
        self.depth_factor_spinbox.setDecimals(2)
        analysis_layout.addRow("Fattore profondità:", self.depth_factor_spinbox)
        
        layout.addWidget(analysis_group)
        
        # Gruppo condizioni idrauliche
        water_group = QGroupBox("Condizioni Idrauliche")
        water_layout = QFormLayout(water_group)
        
        # Livello freatico
        self.water_table_spinbox = QDoubleSpinBox()
        self.water_table_spinbox.setRange(-50.0, 0.0)
        self.water_table_spinbox.setValue(-5.0)
        self.water_table_spinbox.setSuffix(" m")
        self.water_table_spinbox.setDecimals(1)
        water_layout.addRow("Livello freatico (rel. al piano):", self.water_table_spinbox)
        
        layout.addWidget(water_group)
        
        # Pulsante calcolo
        self.btnStabilityAnalysis = QPushButton("Esegui Analisi di Stabilità (Morgenstern & Price)")
        self.btnStabilityAnalysis.clicked.connect(self._emit_stability_analysis)
        layout.addWidget(self.btnStabilityAnalysis)
        
        # Area risultati
        results_group = QGroupBox("Risultati")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(150)
        self.results_text.setPlainText("Nessuna analisi eseguita")
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(stability_widget, "Analisi di Stabilità")

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
        raster_layer = self.cboRaster.currentData()
        self.computeProfileRequested.emit(raster_layer, self._p1, self._p2)

    def _emit_stability_analysis(self):
        """Raccoglie i parametri e emette il segnale per l'analisi di stabilità."""
        params = {
            'gamma': self.gamma_spinbox.value(),
            'cohesion': self.cohesion_spinbox.value(),
            'cohesion_depth_rate': self.cohesion_depth_rate_spinbox.value(),
            'friction_angle': self.friction_angle_spinbox.value(),
            'num_slices': self.slices_spinbox.value(),
            'depth_factor': self.depth_factor_spinbox.value(),
            'water_table': self.water_table_spinbox.value()
        }
        self.stabilityAnalysisRequested.emit(params)

    def updateProfile(self, distances, elevations, slip_surface_points=None):
        """Aggiorna il grafico del profilo.

        Filtra i valori None (nodat / fuori raster). Se nessun dato valido mostra un messaggio.
        slip_surface_points: tupla (x, y) con i punti della superficie di scivolamento critica
        """
        if self.figure is None:
            return
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
        
        # Plotta la superficie di scivolamento critica se disponibile
        if slip_surface_points is not None:
            slip_x, slip_y = slip_surface_points
            ax.plot(slip_x, slip_y, '-r', linewidth=2, label='Superficie critica')
            ax.legend()
        
        ax.set_xlabel('Distanza [m]')
        ax.set_ylabel('Quota [m]')
        ax.grid(True, linestyle='--', alpha=0.4)
        self.canvas.draw()

    def _do_export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salva profilo", "profilo.csv", "CSV (*.csv)")
        if path:
            self.exportRequested.emit(path)

    def setStatus(self, msg):
        self.lblStatus.setText(msg)

    def updateStabilityResults(self, results_text):
        """Aggiorna l'area dei risultati dell'analisi di stabilità."""
        if hasattr(self, 'results_text'):
            self.results_text.setPlainText(results_text)
