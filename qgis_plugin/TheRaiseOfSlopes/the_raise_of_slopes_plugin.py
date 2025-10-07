# -*- coding: utf-8 -*-
"""Main entry point for QGIS plugin.

Funzionalità implementate:
 - Selezione di due punti sul DEM
 - Campionamento profilo altimetrico lungo la linea
 - Gestione nodata e trasformazione CRS (progetto -> raster)
 - Visualizzazione grafica e export CSV  
 - Analisi di stabilità con metodo Morgenstern & Price usando il framework GLE
"""
import os
import sys
import numpy as np
import scipy.interpolate as interpolate
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtCore import Qt
from qgis.core import (
    QgsPointXY,
    QgsCoordinateTransform,
    QgsProject,
    QgsGeometry,
    QgsWkbTypes,
)
from qgis.gui import QgsRubberBand

from .ui.profile_dialog import ProfileDialog
from .tools.point_selection_tool import TwoPointSelectionTool

# Import delle classi del framework limit-equilibrium
# I moduli sono nella sottocartella le_core/ (copiati da src/limit-equilibrium)
# Aggiungiamo il path per compatibilità con diversi modi di caricamento del plugin
plugin_dir = os.path.dirname(__file__)
le_core_path = os.path.join(plugin_dir, 'le_core')
if le_core_path not in sys.path:
    sys.path.insert(0, le_core_path)

try:
    # Prova prima import relativi (preferito)
    from .le_core.base_classes import SoilProperties, SoilState, UniformQuadrature, Options
    from .le_core.circularSlipSurface import circularSlipSurface
    from .le_core.gle import morgerstern_price
    from .le_core.bishop import bishop
    from .le_core.gridOfCircles import GridOptions, gridComputation
    LIMIT_EQUILIBRIUM_AVAILABLE = True
except ImportError:
    try:
        # Fallback: import assoluti dopo aver aggiunto il path
        from base_classes import SoilProperties, SoilState, UniformQuadrature, Options
        from circularSlipSurface import circularSlipSurface
        from gle import morgerstern_price
        from bishop import bishop
        from gridOfCircles import GridOptions, gridComputation
        LIMIT_EQUILIBRIUM_AVAILABLE = True
    except ImportError as e:
        LIMIT_EQUILIBRIUM_AVAILABLE = False
        print(f"Avviso: Moduli limit-equilibrium non disponibili: {e}")
        print(f"Percorso le_core: {le_core_path}")
        print(f"Esiste le_core? {os.path.exists(le_core_path)}")
        if os.path.exists(le_core_path):
            print(f"File in le_core: {os.listdir(le_core_path)}")
        print(f"Eseguire lo script setup_qgis_plugin.sh per copiare i moduli necessari.")


def classFactory(iface):  # QGIS chiamerà questa funzione
    return TheRaiseOfSlopesPlugin(iface)


class TheRaiseOfSlopesPlugin:
    def __init__(self, iface):
        """Inizializza lo stato del plugin."""
        self.iface = iface
        self.action = None
        self.dlg = None
        self.selection_tool = None
        self.profile_distances = []
        self.profile_elevations = []
        
        # Rubber bands per visualizzazione
        self.p1_rubber_band = None
        self.p2_rubber_band = None
        self.line_rubber_band = None

    def initGui(self):
        self.action = QAction(QIcon(self._icon_path()), "The Raise Of Slopes - Profilo", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("TheRaiseOfSlopes", self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        if self.action:
            self.iface.removeToolBarIcon(self.action)
            self.iface.removePluginMenu("TheRaiseOfSlopes", self.action)
        self._restore_map_tool()
        self._clear_rubber_bands()

    def run(self):
        """Mostra il dialog principale."""
        if not self.dlg:
            self.dlg = ProfileDialog()
            self.dlg.startSelectionRequested.connect(self._start_point_selection)
            self.dlg.computeProfileRequested.connect(self._compute_profile)
            self.dlg.exportRequested.connect(self._export_profile)
            self.dlg.stabilityAnalysisRequested.connect(self._analyze_stability)
        self.dlg.show()
        self.dlg.raise_()

    def _icon_path(self):
        return os.path.join(os.path.dirname(__file__), 'icon.png')

    def _start_point_selection(self):
        """Attiva il map tool per raccogliere due clic utente."""
        self._clear_rubber_bands()
        
        self.selection_tool = TwoPointSelectionTool(self.iface.mapCanvas())
        self.selection_tool.firstPointSelected.connect(self._on_first_point_selected)
        self.selection_tool.pointsSelected.connect(self._on_points_selected)
        self.iface.mapCanvas().setMapTool(self.selection_tool)
        self.dlg.setStatus("Seleziona il primo punto sul DEM...")

    def _restore_map_tool(self):
        self.iface.mapCanvas().unsetMapTool(self.selection_tool)
        self.selection_tool = None
    
    def _clear_rubber_bands(self):
        """Rimuove i rubber band dalla mappa."""
        if self.p1_rubber_band:
            self.iface.mapCanvas().scene().removeItem(self.p1_rubber_band)
            self.p1_rubber_band = None
        if self.p2_rubber_band:
            self.iface.mapCanvas().scene().removeItem(self.p2_rubber_band)
            self.p2_rubber_band = None
        if self.line_rubber_band:
            self.iface.mapCanvas().scene().removeItem(self.line_rubber_band)
            self.line_rubber_band = None
    
    def _on_first_point_selected(self, p1):
        """Gestisce la selezione del primo punto."""
        self._clear_rubber_bands()
        
        self.p1_rubber_band = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.PointGeometry)
        self.p1_rubber_band.setColor(QColor(255, 0, 0))
        self.p1_rubber_band.setIconSize(15)
        self.p1_rubber_band.addPoint(p1)
        
        self.dlg.setStatus("Primo punto (P1) selezionato. Seleziona il secondo punto (P2)...")

    def _create_placeholder(self, p1, p2):
        """Crea un placeholder visivo sulla mappa."""
        self.p2_rubber_band = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.PointGeometry)
        self.p2_rubber_band.setColor(QColor(0, 255, 0))
        self.p2_rubber_band.setIconSize(12)
        self.p2_rubber_band.addPoint(p2)
        
        self.line_rubber_band = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.LineGeometry)
        self.line_rubber_band.setColor(QColor(0, 0, 255))
        self.line_rubber_band.setWidth(2)
        self.line_rubber_band.addPoint(p1)
        self.line_rubber_band.addPoint(p2)

    def _on_points_selected(self, p1, p2):
        self.dlg.setSelectedPoints(p1, p2)
        self.dlg.setStatus("Punti selezionati. Premi 'Calcola profilo'.")
        self._create_placeholder(p1, p2)
        self._restore_map_tool()

    def _compute_profile(self, raster_layer, p1, p2):
        """Campiona il profilo altimetrico fra i due punti."""
        if not raster_layer or not p1 or not p2:
            self.dlg.setStatus("Parametri mancanti per il profilo.")
            return
            
        provider = raster_layer.dataProvider()
        extent_length = p1.distance(p2)
        if extent_length == 0:
            self.dlg.setStatus("I due punti coincidono.")
            return
            
        px = raster_layer.rasterUnitsPerPixelX()
        py = raster_layer.rasterUnitsPerPixelY()
        step = (abs(px) + abs(py)) / 2.0
        if step <= 0:
            step = extent_length / 100.0
            
        n = int(extent_length / step) + 1
        distances = []
        elevations = []
        band = 1
        no_data = provider.sourceNoDataValue(band)
        
        raster_crs = raster_layer.crs()
        project_crs = QgsProject.instance().crs()
        need_transform = project_crs.isValid() and raster_crs.isValid() and (project_crs != raster_crs)
        transformer = None
        if need_transform:
            transformer = QgsCoordinateTransform(project_crs, raster_crs, QgsProject.instance())
            
        for i in range(n + 1):
            d = min(i * step, extent_length)
            t = d / extent_length
            x = p1.x() + (p2.x() - p1.x()) * t
            y = p1.y() + (p2.y() - p1.y()) * t
            pt = QgsPointXY(x, y)
            if transformer is not None:
                try:
                    pt = transformer.transform(pt)
                except Exception:
                    distances.append(d)
                    elevations.append(None)
                    continue
            val = self._sample_with_bilinear(provider, pt, band, no_data, raster_layer)
            distances.append(d)
            elevations.append(val)
            
        self.profile_distances = distances
        self.profile_elevations = elevations
        self.dlg.updateProfile(distances, elevations)
        self.dlg.setStatus("Profilo calcolato: {} punti.".format(len(distances)))

    def _export_profile(self, path):
        """Esporta il profilo in CSV."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write('distanza,quota\n')
                for d, z in zip(self.profile_distances, self.profile_elevations):
                    f.write(f"{d},{z}\n")
            self.dlg.setStatus(f"Profilo salvato: {path}")
        except Exception as e:
            self.dlg.setStatus(f"Errore salvataggio: {e}")

    def _sample_with_bilinear(self, provider, pt, band, no_data, raster_layer):
        """Campiona con fallback bilineare."""
        import math
        val, ok = provider.sample(pt, band)
        if ok:
            if no_data is not None:
                if (isinstance(no_data, float) and isinstance(val, float) and math.isnan(no_data) and math.isnan(val)) or val == no_data:
                    pass
                else:
                    return val
            else:
                return val

        extent = raster_layer.extent()
        px = raster_layer.rasterUnitsPerPixelX()
        py = raster_layer.rasterUnitsPerPixelY()
        if px == 0 or py == 0:
            return None
        col_f = (pt.x() - extent.xMinimum()) / px
        row_f = (extent.yMaximum() - pt.y()) / abs(py)
        col0 = int(math.floor(col_f))
        row0 = int(math.floor(row_f))
        col1 = col0 + 1
        row1 = row0 + 1
        stats = provider.xSize(), provider.ySize()
        max_col = stats[0] - 1
        max_row = stats[1] - 1
        if not (0 <= col0 <= max_col and 0 <= col1 <= max_col and 0 <= row0 <= max_row and 0 <= row1 <= max_row):
            return None
            
        def read_cell(c, r):
            x = extent.xMinimum() + (c + 0.5) * px
            y = extent.yMaximum() - (r + 0.5) * abs(py)
            v, okc = provider.sample(QgsPointXY(x, y), band)
            if not okc:
                return None
            if no_data is not None:
                if (isinstance(no_data, float) and isinstance(v, float) and math.isnan(no_data) and math.isnan(v)) or v == no_data:
                    return None
            return v
            
        v00 = read_cell(col0, row0)
        v10 = read_cell(col1, row0)
        v01 = read_cell(col0, row1)
        v11 = read_cell(col1, row1)
        if None in (v00, v10, v01, v11):
            return None
        dx = col_f - col0
        dy = row_f - row0
        v0 = v00 * (1 - dx) + v10 * dx
        v1 = v01 * (1 - dx) + v11 * dx
        vb = v0 * (1 - dy) + v1 * dy
        return vb

    def _analyze_stability(self, params):
        """Esegue l'analisi di stabilità di Morgenstern & Price usando il framework GLE."""
        if not self.profile_distances or not self.profile_elevations:
            self.dlg.setStatus("Calcola prima il profilo altimetrico.")
            return
        
        if not LIMIT_EQUILIBRIUM_AVAILABLE:
            error_msg = "Moduli limit-equilibrium non disponibili. Verificare l'installazione."
            self.dlg.setStatus(error_msg)
            self.dlg.updateStabilityResults(error_msg)
            return
        
        try:
            # --- LOG HEADER (solo parametri noti a priori) ---
            print("=" * 60)
            print("ANALISI DI STABILITÀ - INIZIO")
            print("=" * 60)
            print(f"Parametri terreno: γ={params['gamma']:.1f} kN/m³, c={params['cohesion']:.1f} kPa, φ={params['friction_angle']:.1f}°")
            print(f"Aumento coesione con profondità: {params.get('cohesion_depth_rate', 0.0):.3f} kPa/m")

            # 1. Crea la funzione ground_surface lineare a tratti
            ground_surface = self._create_ground_surface_function(
                self.profile_distances, 
                self.profile_elevations
            )
            
            # 2. Calcola il bounding box (ora possiamo definire x_min, x_max, ecc.)
            valid_elevations = [e for e in self.profile_elevations if e is not None]
            if not valid_elevations:
                raise ValueError("Nessun dato valido nel profilo")
            
            x_min = self.profile_distances[0]
            x_max = self.profile_distances[-1]
            y_min = min(valid_elevations)
            y_max = max(valid_elevations)
            
            # Espande il bounding box per la superficie di scivolamento
            y_min_extended = y_min - (y_max - y_min) * params['depth_factor']
            bounding_box = np.array([[x_min, x_max], [y_min_extended, y_max * 1.1]])
            
            # 3. Opzioni griglia
            grid_options = GridOptions(
                in_interval=[x_max * 0.6, x_max],
                out_interval=[x_min, x_min + (x_max - x_min) * 0.4],
                min_eta_inc=np.radians(5),
                num_in_pts=16,
                num_out_pts=16
            )

            # 4. Ora che tutte le variabili sono definite, stampiamo le info derivate
            print(f"Bounding box: x=[{x_min:.1f}, {x_max:.1f}], y=[{y_min_extended:.1f}, {y_max*1.1:.1f}]")
            # (Le info di griglia verranno stampate più avanti dopo la definizione di grid_options)
            
            # Parametri del terreno
            constant_dry_density = params['gamma']
            soil_properties = SoilProperties(
                cohesion=lambda x, y: params['cohesion'] + params.get('cohesion_depth_rate', 0.0) * (ground_surface(x) - y),
                friction_angle=lambda x, y: params['friction_angle'] * np.ones_like(x + y),
                dry_density=lambda x, y: constant_dry_density * np.ones_like(x + y),
                porosity=lambda x, y: 0.0 * np.ones_like(x + y),
                grain_density=lambda x, y: 0.0 * np.ones_like(x + y)
            )
            
            # Stato del terreno
            soil_state = SoilState(
                saturation=lambda x, y: 1.0 * np.ones_like(x + y),
                pore_pressure=lambda x, y: 0.0 * np.ones_like(x + y),
                integrated_density=lambda x, y: constant_dry_density * (ground_surface(x) - y)
            )
            
            # Opzioni del metodo
            method_options = Options(
                max_iteration=200,
                tolerance=1e-4,
                quadrature=lambda interval: UniformQuadrature(x_interval=interval, num=50)
            )
            
            # Esegui calcolo
            self.dlg.setStatus("Calcolo in corso... (griglia di cerchi)")
            results, computation_time = gridComputation(
                bishop,
                ground_surface,
                bounding_box,
                soil_properties,
                soil_state,
                grid_options,
                method_options
            )
            
            print(f"\nCalcolo completato in {computation_time:.2f} secondi")
            print(f"Superfici analizzate: {len(results)}")
            
            if not results:
                raise ValueError("Nessuna superficie di scivolamento valida trovata")
            
            # Risultato critico (FS minimo)
            critical_result = results[0]
            factor_of_safety = critical_result.factor_of_safety
            
            print(f"\nRISULTATO CRITICO:")
            print(f"Fattore di Sicurezza (FS): {factor_of_safety:.4f}")
          #  print(f"Convergenza raggiunta: {critical_result.convergence}")
          #  print(f"Iterazioni: {critical_result.iterations}")
            
            # Informazioni superficie critica
            geometry = critical_result.inputs[0]
            num_slices = len(critical_result.nodes[0])
            
            # Estrai informazioni dalla geometria
            # landslide_interval contiene [x_out, x_in] o [x_in, x_out]
            x_out = geometry.landslide_interval[0]
            x_in = geometry.landslide_interval[1]
            
            print(f"\nGEOMETRIA SUPERFICIE CRITICA:")
            print(f"Punto ingresso (x_in): {x_in:.2f} m")
            print(f"Punto uscita (x_out): {x_out:.2f} m") 
            print(f"Lunghezza superficie: {x_in - x_out:.2f} m")
            print(f"Numero di conci: {num_slices}")
            print(f"Tipo di geometry.ground_surface: {type(geometry.ground_surface)}")
            print(f"geometry.ground_surface è callable: {callable(geometry.ground_surface)}")
            try:
                if callable(geometry.ground_surface):
                    print(f"Quota ingresso: {geometry.ground_surface(x_in):.2f} m")
                    print(f"Quota uscita: {geometry.ground_surface(x_out):.2f} m")
                else:
                    print("geometry.ground_surface non è callable (tipo salvato nello stato).")
            except Exception as gse:
                print(f"Errore nel calcolo delle quote ingresso/uscita: {gse}")
            
            # Mostra i primi 5 risultati ordinati per FS
            print(f"\nPRIMI 5 RISULTATI (ordinati per FS crescente):")
            sorted_results = sorted(results, key=lambda r: r.factor_of_safety)[:5]
            for i, result in enumerate(sorted_results, 1):
                geom = result.inputs[0]
                x_out_r = geom.landslide_interval[0]
                x_in_r = geom.landslide_interval[1]
                print(f"{i}. FS={result.factor_of_safety:.4f}, x_in={x_in_r:.1f}, x_out={x_out_r:.1f}, L={x_in_r-x_out_r:.1f}")
            
            # Campiona la superficie di scivolamento per il grafico
            try:
                slip_x = np.linspace(x_out, x_in, 100)
                slip_y = geometry.slip_surface(slip_x)
                slip_surface_points = (slip_x, slip_y)
            except Exception as e:
                print(f"Errore nel campionamento della superficie di scivolamento: {e}")
                slip_surface_points = None
            
            # Aggiorna il grafico del profilo con la superficie critica
            try:
                self.dlg.updateProfile(self.profile_distances, self.profile_elevations, slip_surface_points)
            except Exception as e:
                print(f"Errore nell'aggiornamento del grafico: {e}")
                self.dlg.updateProfile(self.profile_distances, self.profile_elevations)
            
            # Prepara output (senza dettagli geometrici che richiedono circularSlipSurface)
            try:
                results_text = f"""ANALISI DI STABILITÀ - MORGENSTERN & PRICE (GLE)

Parametri utilizzati:
- Peso specifico (γ): {params['gamma']:.1f} kN/m³
- Coesione (c): {params['cohesion']:.1f} kPa
- Aumento coesione con profondità: {params.get('cohesion_depth_rate', 0.0):.3f} kPa/m
- Angolo di attrito (φ): {params['friction_angle']:.1f}°
- Numero di conci analizzati: {num_slices}
- Griglia: {grid_options.num_in_pts} × {grid_options.num_out_pts} = {grid_options.num_in_pts * grid_options.num_out_pts} cerchi
- Tempo: {computation_time:.2f} s

SUPERFICIE DI SCIVOLAMENTO CRITICA:
- Punto ingresso (monte): x = {x_in:.2f} m, y = {geometry.ground_surface(x_in) if callable(geometry.ground_surface) else 'N/A':.2f} m
- Punto uscita (valle): x = {x_out:.2f} m, y = {geometry.ground_surface(x_out) if callable(geometry.ground_surface) else 'N/A':.2f} m
- Lunghezza superficie: {x_in - x_out:.2f} m

RISULTATI:
Fattore di Sicurezza (FS): {factor_of_safety:.3f}

Condizione: {'STABILE (FS ≥ 1.5)' if factor_of_safety >= 1.5 else 'INSTABILE (FS < 1.0)' if factor_of_safety < 1.0 else 'MARGINALMENTE STABILE (1.0 ≤ FS < 1.5)'}

Nota: Analizzate {len(results)} superfici circolari.
Risultato mostrato: FS minimo (più critico).
"""
            except Exception as e:
                print(f"Errore nella creazione del testo risultati: {e}")
                results_text = f"Errore nella creazione del report: {e}"
            
            self.dlg.updateStabilityResults(results_text)
            self.dlg.setStatus(f"Analisi completata. FS minimo = {factor_of_safety:.3f}")
            
            print(f"\nRIEPILOGO:")
            print(f"FS critico: {factor_of_safety:.4f}")
            print(f"Condizione: {'STABILE' if factor_of_safety >= 1.5 else 'INSTABILE' if factor_of_safety < 1.0 else 'MARGINALMENTE STABILE'}")
            print(f"Tempo calcolo: {computation_time:.2f} s")
            print(f"Superfici totali analizzate: {len(results)}")
            print("=" * 60)
            print("ANALISI DI STABILITÀ - FINE")
            print("=" * 60)
            
        except Exception as e:
            import traceback
            error_msg = f"Errore nell'analisi:\n{str(e)}\n\n{traceback.format_exc()}"
            self.dlg.setStatus(f"Errore: {str(e)}")
            self.dlg.updateStabilityResults(error_msg)
            
            print(f"\nERRORE NELL'ANALISI:")
            print(f"Tipo errore: {type(e).__name__}")
            print(f"Messaggio: {str(e)}")
            print(f"Traceback completo:\n{traceback.format_exc()}")
            print("=" * 60)

    def _create_ground_surface_function(self, distances, elevations):
        """Crea una funzione lineare a tratti per la superficie del terreno."""
        valid_points = [(d, e) for d, e in zip(distances, elevations) if e is not None]
        if len(valid_points) < 2:
            raise ValueError("Dati insufficienti per creare la funzione del terreno")
        
        valid_distances, valid_elevations = zip(*valid_points)
        
        # Interpolatore lineare
        interpolator = interpolate.interp1d(
            valid_distances, 
            valid_elevations, 
            kind='linear',
            fill_value='extrapolate'
        )
        
        def ground_surface(x):
            return interpolator(x)
        
        return ground_surface
