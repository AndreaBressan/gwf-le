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
    from .le_core.gridSimplexComputation import simplexComputation
    from .le_core.gle import morgerstern_price, spencer
    LIMIT_EQUILIBRIUM_AVAILABLE = True
except ImportError:
    try:
        # Fallback: import assoluti dopo aver aggiunto il path
        from base_classes import SoilProperties, SoilState, UniformQuadrature, Options
        from circularSlipSurface import circularSlipSurface
        from gle import morgerstern_price, spencer
        from bishop import bishop
        from gridOfCircles import GridOptions, gridComputation
        from gridSimplexComputation import simplexComputation
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
        
        # Salva i dati del profilo per calcoli successivi
        self.profile_p1 = None
        self.profile_p2 = None
        self.profile_raster_layer = None
        
        # Memorizza TUTTE le superfici critiche calcolate (lista di dict)
        # Ogni item: {'search': 'grid'|'simplex', 'method': 'Bishop'|..., 'x': np.array, 'y': np.array, 'fs': float}
        self.slip_surfaces = []
        
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
            self.dlg.set_plugin(self)  # Passa il riferimento al plugin
            self.dlg.startSelectionRequested.connect(self._start_point_selection)
            self.dlg.computeProfileRequested.connect(self._compute_profile)
            self.dlg.exportRequested.connect(self._export_profile)
            self.dlg.gridStabilityAnalysisRequested.connect(self._analyze_grid_stability)
            self.dlg.simplexStabilityAnalysisRequested.connect(self._analyze_simplex_stability)
            self.dlg.clearSurfacesRequested.connect(self._clear_surfaces)
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
        self._create_placeholder(p1, p2)
        self._restore_map_tool()
        
        # Calcola automaticamente il profilo
        raster_layer = self.dlg.cboRaster.currentData()
        if raster_layer:
            self.dlg.setStatus("Calcolo automatico del profilo in corso...")
            self._compute_profile(raster_layer, p1, p2)
        else:
            self.dlg.setStatus("Punti selezionati. Seleziona un raster DEM e premi 'Calcola profilo'.")

    def _compute_profile(self, raster_layer, p1, p2):
        """Campiona il profilo altimetrico fra i due punti."""
        if not raster_layer or not p1 or not p2:
            self.dlg.setStatus("Parametri mancanti per il profilo.")
            return
        
        # Salva i dati del profilo per calcoli successivi
        self.profile_p1 = p1
        self.profile_p2 = p2
        self.profile_raster_layer = raster_layer
            
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
        
        # Cancella le superfici critiche precedenti (nuovo profilo)
        self.slip_surfaces = []
        
        self.dlg.updateProfile(distances, elevations)
        self.dlg.setProfileDistances(distances)  # Salva le distanze nel dialog
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

    def _clear_surfaces(self):
        """Pulisce tutte le superfici disegnate e aggiorna il grafico."""
        self.slip_surfaces = []
        # Forza un ridisegno del profilo senza superfici
        self.dlg.updateProfile(self.profile_distances, self.profile_elevations, slip_surfaces_list=[])
        self.dlg.setStatus("Superfici pulite")

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

    def _sample_raster_at_x_coordinates(self, x_coords, raster_layer, default_value=0.0):
        """Campiona un raster alle coordinate x lungo il profilo.
        
        Args:
            x_coords: Array numpy di coordinate x lungo il profilo (distanze)
            raster_layer: Layer raster QGIS da campionare
            default_value: Valore di default se il campionamento fallisce
            
        Returns:
            Array numpy con i valori campionati dal raster
        """
        if not self.profile_distances or not self.profile_elevations:
            # Se non abbiamo un profilo, ritorna il valore di default
            return np.full_like(x_coords, default_value, dtype=float)
        
        # Converti x_coords in array numpy se necessario
        x_coords = np.atleast_1d(x_coords)
        result = np.full_like(x_coords, default_value, dtype=float)
        
        # Ottieni provider e parametri del raster
        provider = raster_layer.dataProvider()
        band = 1
        no_data = provider.sourceNoDataValue(band)
        
        # Gestione CRS
        raster_crs = raster_layer.crs()
        project_crs = QgsProject.instance().crs()
        need_transform = project_crs.isValid() and raster_crs.isValid() and (project_crs != raster_crs)
        transformer = None
        if need_transform:
            transformer = QgsCoordinateTransform(project_crs, raster_crs, QgsProject.instance())
        
        # I punti P1 e P2 del profilo
        if not self._p1 or not self._p2:
            return result
        
        p1 = self._p1
        p2 = self._p2
        extent_length = p1.distance(p2)
        
        if extent_length == 0:
            return result
        
        # Per ogni coordinata x, calcola la posizione geografica e campiona
        for i, x in enumerate(x_coords):
            if x < 0 or x > extent_length:
                # Fuori dal range del profilo
                result[i] = default_value
                continue
            
            # Parametro t lungo il segmento P1-P2
            t = x / extent_length
            
            # Coordinate geografiche del punto
            geo_x = p1.x() + (p2.x() - p1.x()) * t
            geo_y = p1.y() + (p2.y() - p1.y()) * t
            pt = QgsPointXY(geo_x, geo_y)
            
            # Trasformazione CRS se necessaria
            if transformer is not None:
                try:
                    pt = transformer.transform(pt)
                except Exception:
                    result[i] = default_value
                    continue
            
            # Campiona il raster
            val = self._sample_with_bilinear(provider, pt, band, no_data, raster_layer)
            
            if val is not None:
                result[i] = val
            else:
                result[i] = default_value
        
        return result

    def _analyze_grid_stability(self, params):
        """Esegue l'analisi di stabilità con griglia di cerchi usando Bishop."""
        if not self.profile_distances or not self.profile_elevations:
            self.dlg.setStatus("Calcola prima il profilo altimetrico.")
            return
        
        if not LIMIT_EQUILIBRIUM_AVAILABLE:
            error_msg = "Moduli limit-equilibrium non disponibili. Verificare l'installazione."
            self.dlg.setStatus(error_msg)
            self.dlg.updateStabilityResults(error_msg, 'grid')
            return
        
        try:
            # --- LOG HEADER ---
            print("=" * 60)
            print("ANALISI DI STABILITÀ GRIGLIA - INIZIO")
            print("=" * 60)
            print(f"Parametri terreno strato 1: γ={params['gamma']:.1f} kN/m³, c={params['cohesion']:.1f} kPa, φ={params['friction_angle']:.1f}°, n={params['porosity']:.2f}")
            
            # Log stratigrafia
            if params.get('enable_layer2', False):
                print(f"Secondo strato attivo: γ₂={params['gamma_2']:.1f} kN/m³, c₂={params['cohesion_2']:.1f} kPa, φ₂={params['friction_angle_2']:.1f}°")
            if params.get('enable_water', False):
                print("Falda freatica attiva")

            # 1. Crea la funzione ground_surface
            ground_surface = self._create_ground_surface_function(
                self.profile_distances, 
                self.profile_elevations
            )
            
            # 2. Crea la funzione per l'interfaccia del secondo strato (se abilitato)
            layer2_interface = None
            if params.get('enable_layer2', False):
                layer2_interface = self._create_layer2_interface_function(params, ground_surface)
                print(f"Interfaccia secondo strato creata: modalità {params.get('layer2_definition_mode', 'unknown')}")
                # Test dell'interfaccia su un punto campione
                x_min_temp = self.profile_distances[0]
                x_max_temp = self.profile_distances[-1]
                test_x = (x_min_temp + x_max_temp) / 2
                test_interface_y = layer2_interface(test_x)
                test_ground_y = ground_surface(test_x)
                print(f"  Test punto x={test_x:.1f}: terreno={test_ground_y:.1f}m, interfaccia={test_interface_y:.1f}m, spessore={test_ground_y-test_interface_y:.1f}m")
            
            # 3. Crea la funzione per la falda (se abilitata)
            water_table = None
            if params.get('enable_water', False):
                water_table = self._create_water_table_function(params, ground_surface)
            
            # 4. Calcola il bounding box
            valid_elevations = [e for e in self.profile_elevations if e is not None]
            if not valid_elevations:
                raise ValueError("Nessun dato valido nel profilo")
            
            x_min = self.profile_distances[0]
            x_max = self.profile_distances[-1]
            y_min = min(valid_elevations)
            y_max = max(valid_elevations)
            
            y_min_extended = y_min - (y_max - y_min) * params['depth_factor']
            bounding_box = np.array([[x_min, x_max], [y_min_extended, y_max * 1.1]])
            
            # 5. Opzioni griglia (usando i parametri dall'interfaccia)
            in_interval_min = params['in_interval_min'] * x_max
            in_interval_max = params['in_interval_max'] * x_max
            out_interval_min = params['out_interval_min'] * x_max
            out_interval_max = params['out_interval_max'] * x_max
            
            grid_options = GridOptions(
                in_interval=[in_interval_min, in_interval_max],
                out_interval=[out_interval_min, out_interval_max],
                in_pts=None,
                out_pts=None,
                min_eta_inc=np.radians(params['min_eta_inc']),
                num_in_pts=params['num_in_pts'],
                num_out_pts=params['num_out_pts']
            )

            print(f"Bounding box: x=[{x_min:.1f}, {x_max:.1f}], y=[{y_min_extended:.1f}, {y_max*1.1:.1f}]")
            print(f"Griglia: in=[{in_interval_min:.1f}, {in_interval_max:.1f}], out=[{out_interval_min:.1f}, {out_interval_max:.1f}]")
            print(f"Punti griglia: in={params['num_in_pts']}, out={params['num_out_pts']}, min_eta={params['min_eta_inc']}°")

            # Selettore del metodo di stabilità
            method_label, solver = self._get_solver(params.get('stability_method', 'Bishop'))
            print(f"Metodo di calcolo stabilità: {method_label}")
            
            # Parametri del terreno e stato
            soil_properties, soil_state = self._create_soil_properties_and_state(
                params, ground_surface, layer2_interface, water_table
            )
            
            # Opzioni del metodo
            method_options = Options(
                max_iteration=200,
                tolerance=1e-4,
                quadrature=lambda interval: UniformQuadrature(x_interval=interval, num=params['num_slices'])
            )
            
            # Esegui calcolo
            self.dlg.setStatus("Calcolo in corso... (griglia di cerchi)")
            
            print("Chiamata a gridComputation...")
            results, computation_time = gridComputation(
                solver,
                ground_surface,
                bounding_box,
                soil_properties,
                soil_state,
                grid_options,
                method_options
            )

            print(f"\nCalcolo completato in {computation_time:.2f} secondi")
            
            if results is None or len(results) == 0:
                raise ValueError("Nessuna superficie di scivolamento valida trovata")
            
            # Appiattisci la lista dei risultati se necessario (gridComputation può restituire liste annidate)
            all_results = []
            for result_group in results:
                if isinstance(result_group, list):
                    all_results.extend(result_group)
                else:
                    all_results.append(result_group)
            
            print(f"Superfici analizzate: {len(all_results)}")
            
            # Trova il risultato critico (FS minimo)
            critical_result = min(all_results, key=lambda r: r.factor_of_safety)
            factor_of_safety = critical_result.factor_of_safety
            
            print(f"\nRISULTATO CRITICO:")
            print(f"Fattore di Sicurezza (FS): {factor_of_safety:.4f}")

            # Geometria superficie critica
            # Estrai informazioni dalla geometria (inputs contiene la circularSlipSurface)
            if hasattr(critical_result, 'inputs') and critical_result.inputs:
                geometry = critical_result.inputs[0]
                if hasattr(geometry, 'landslide_interval'):
                    x_out = geometry.landslide_interval[0]
                    x_in = geometry.landslide_interval[1]
                else:
                    # Fallback
                    x_in = x_max * 0.8
                    x_out = x_min + (x_max - x_min) * 0.2
            else:
                # Fallback
                x_in = x_max * 0.8
                x_out = x_min + (x_max - x_min) * 0.2
            
            y_in = ground_surface(x_in)
            y_out = ground_surface(x_out)
            
            # Calcola eta se possibile
            if hasattr(critical_result, 'inputs') and critical_result.inputs and hasattr(critical_result.inputs[0], 'eta'):
                eta_deg = np.degrees(critical_result.inputs[0].eta)
            else:
                # Stima eta dalla geometria
                eta_deg = "N/A"
            
            print(f"\nGEOMETRIA SUPERFICIE CRITICA:")
            print(f"Punto ingresso (x_in): {x_in:.2f} m, quota: {y_in:.2f} m")
            print(f"Punto uscita (x_out): {x_out:.2f} m, quota: {y_out:.2f} m")
            print(f"Lunghezza superficie: {x_in - x_out:.2f} m")
            if isinstance(eta_deg, (int, float)):
                print(f"Angolo eta: {eta_deg:.2f}°")
            else:
                print(f"Angolo eta: {eta_deg}")
            
            # Campiona la superficie per il grafico
            try:
                slip_x, slip_y = None, None
                # Prova a ottenere la geometria dall'oggetto 'inputs'
                if hasattr(critical_result, 'inputs') and critical_result.inputs:
                    geom = critical_result.inputs[0]
                    x_start, x_end = geom.landslide_interval
                    slip_x = np.linspace(x_start, x_end, 200)
                    # La classe circularSlipSurface espone la funzione y come 'slip_surface(x)'
                    slip_y = geom.slip_surface(slip_x)
                else:
                    # Fallback: prova a ricostruire da x_in/x_out/eta se disponibili
                    if isinstance(eta_deg, (int, float)):
                        eta_rad = np.radians(eta_deg)
                        geom = circularSlipSurface.fromInOutAndEta(ground_surface, bounding_box, x_in, x_out, eta_rad)
                        x_start, x_end = geom.landslide_interval
                        slip_x = np.linspace(x_start, x_end, 200)
                        slip_y = geom.slip_surface(slip_x)
                    else:
                        raise AttributeError("Geometria mancante e impossibile ricostruire senza eta.")

                # Salva la superficie critica con metadati
                self._store_surface('grid', method_label, slip_x, slip_y, factor_of_safety)

            except Exception as e:
                # Se non riesci a ottenere la superficie, non mostrare nulla
                print(f"⚠️ Impossibile campionare la superficie critica per il grafico (Griglia): {e}")
                pass
            
            # Aggiorna il grafico con tutte le superfici disponibili
            self._update_profile_with_all_surfaces()
            
            # Prepara output
            eta_str = f"{eta_deg:.2f}°" if isinstance(eta_deg, (int, float)) else str(eta_deg)
            
            # Info stratigrafia per output
            strat_info = self._format_stratigraphy_info(params)
            
            results_text = f"""ANALISI DI STABILITÀ - {method_label.upper()} (GRIGLIA)

Parametri utilizzati:
- Peso specifico (γ): {params['gamma']:.1f} kN/m³
- Coesione (c): {params['cohesion']:.1f} kPa
- Angolo di attrito (φ): {params['friction_angle']:.1f}°
- Numero conci: {params['num_slices']}
- Tempo: {computation_time:.2f} s

{strat_info}

PARAMETRI GRIGLIA:
- Punti ingresso: {params['num_in_pts']}
- Punti uscita: {params['num_out_pts']}
- Incremento minimo η: {params['min_eta_inc']:.1f}°
- Intervallo ingresso: [{in_interval_min:.1f}, {in_interval_max:.1f}] m
- Intervallo uscita: [{out_interval_min:.1f}, {out_interval_max:.1f}] m

SUPERFICIE DI SCIVOLAMENTO CRITICA:
- Punto ingresso (monte): x = {x_in:.2f} m, z = {y_in:.2f} m
- Punto uscita (valle): x = {x_out:.2f} m, z = {y_out:.2f} m
- Lunghezza superficie: {x_in - x_out:.2f} m
- Angolo eta: {eta_str}

RISULTATI:
Fattore di Sicurezza (FS): {factor_of_safety:.3f} ({method_label})

Condizione: {'STABILE (FS ≥ 1.5)' if factor_of_safety >= 1.5 else 'INSTABILE (FS < 1.0)' if factor_of_safety < 1.0 else 'MARGINALMENTE STABILE (1.0 ≤ FS < 1.5)'}

Superfici totali analizzate: {len(all_results)}
"""
            
            self.dlg.updateStabilityResults(results_text, 'grid')
            self.dlg.setStatus(f"Analisi griglia completata. FS minimo = {factor_of_safety:.3f}")
            
            print(f"\nRIEPILOGO:")
            print(f"FS critico: {factor_of_safety:.4f}")
            print(f"Superfici totali: {len(all_results)}")
            print("=" * 60)
            print("ANALISI DI STABILITÀ GRIGLIA - FINE")
            print("=" * 60)
            
        except Exception as e:
            import traceback
            error_msg = f"Errore nell'analisi griglia:\n{str(e)}\n\n{traceback.format_exc()}"
            self.dlg.setStatus(f"Errore: {str(e)}")
            self.dlg.updateStabilityResults(error_msg, 'grid')
            print(f"\nERRORE NELL'ANALISI GRIGLIA:\n{traceback.format_exc()}")

    def _analyze_simplex_stability(self, params):
        """Esegue l'analisi di stabilità con ottimizzazione simplex."""
        if not self.profile_distances or not self.profile_elevations:
            self.dlg.setStatus("Calcola prima il profilo altimetrico.")
            return
        
        if not LIMIT_EQUILIBRIUM_AVAILABLE:
            error_msg = "Moduli limit-equilibrium non disponibili. Verificare l'installazione."
            self.dlg.setStatus(error_msg)
            self.dlg.updateStabilityResults(error_msg, 'simplex')
            return
        
        try:
            # --- LOG HEADER ---
            print("=" * 60)
            print("ANALISI DI STABILITÀ SIMPLEX - INIZIO")
            print("=" * 60)
            print(f"Parametri terreno strato 1: γ={params['gamma']:.1f} kN/m³, c={params['cohesion']:.1f} kPa, φ={params['friction_angle']:.1f}°, n={params['porosity']:.2f}")
            
            # Log stratigrafia
            if params.get('enable_layer2', False):
                print(f"Secondo strato attivo: γ₂={params['gamma_2']:.1f} kN/m³, c₂={params['cohesion_2']:.1f} kPa, φ₂={params['friction_angle_2']:.1f}°")
            if params.get('enable_water', False):
                print("Falda freatica attiva")

            # 1. Crea la funzione ground_surface
            ground_surface = self._create_ground_surface_function(
                self.profile_distances, 
                self.profile_elevations
            )
            
            # 2. Crea la funzione per l'interfaccia del secondo strato (se abilitato)
            layer2_interface = None
            if params.get('enable_layer2', False):
                layer2_interface = self._create_layer2_interface_function(params, ground_surface)
                print(f"Interfaccia secondo strato creata: modalità {params.get('layer2_definition_mode', 'unknown')}")
                # Test dell'interfaccia su un punto campione
                x_min_temp = self.profile_distances[0]
                x_max_temp = self.profile_distances[-1]
                test_x = (x_min_temp + x_max_temp) / 2
                test_interface_y = layer2_interface(test_x)
                test_ground_y = ground_surface(test_x)
                print(f"  Test punto x={test_x:.1f}: terreno={test_ground_y:.1f}m, interfaccia={test_interface_y:.1f}m, spessore={test_ground_y-test_interface_y:.1f}m")
            
            # 3. Crea la funzione per la falda (se abilitata)
            water_table = None
            if params.get('enable_water', False):
                water_table = self._create_water_table_function(params, ground_surface)
            
            # 2. Calcola il bounding box
            valid_elevations = [e for e in self.profile_elevations if e is not None]
            if not valid_elevations:
                raise ValueError("Nessun dato valido nel profilo")
            
            x_min = self.profile_distances[0]
            x_max = self.profile_distances[-1]
            y_min = min(valid_elevations)
            y_max = max(valid_elevations)
            
            y_min_extended = y_min - (y_max - y_min) * params['depth_factor']
            bounding_box = np.array([[x_min, x_max], [y_min_extended, y_max * 1.1]])
            
            
            

            # Bounds per ottimizzazione simplex (usando i parametri dall'interfaccia)
            x_in_min = params['x_in_min'] * x_max
            x_in_max = params['x_in_max'] * x_max
            x_out_min = params['x_out_min'] * x_max
            x_out_max = params['x_out_max'] * x_max
            eta_min = params['eta_min']
            eta_max = params['eta_max']
            
            # Validazione: assicura che gli intervalli siano sufficientemente ampi
            min_interval = x_max * 0.05  # Almeno 5% della lunghezza totale
            if (x_in_max - x_in_min) < min_interval:
                print(f"⚠️  Attenzione: intervallo x_in troppo stretto ({x_in_max-x_in_min:.2f}m), espando a {min_interval:.2f}m")
                center = (x_in_min + x_in_max) / 2
                x_in_min = max(x_min, center - min_interval/2)
                x_in_max = min(x_max, center + min_interval/2)
            
            if (x_out_max - x_out_min) < min_interval:
                print(f"⚠️  Attenzione: intervallo x_out troppo stretto ({x_out_max-x_out_min:.2f}m), espando a {min_interval:.2f}m")
                center = (x_out_min + x_out_max) / 2
                x_out_min = max(x_min, center - min_interval/2)
                x_out_max = min(x_max, center + min_interval/2)
            
            # Assicura che x_in sia sempre > x_out (monte > valle)
            if x_in_min <= x_out_max:
                print(f"⚠️  Attenzione: overlap tra x_in e x_out, correggo...")
                gap = x_max * 0.1  # Gap minimo del 10%
                mid_point = (x_in_min + x_out_max) / 2
                x_out_max = mid_point - gap/2
                x_in_min = mid_point + gap/2
            
            bounds = ((x_in_min, x_in_max), 
                      (x_out_min, x_out_max), 
                      (eta_min, eta_max))
            
            # 3. Opzioni griglia per simplex (devono corrispondere ai bounds!)
            # IMPORTANTE: grid_options viene usato da simplexComputation per la ricerca iniziale
            # quindi DEVE usare gli stessi intervalli dei bounds per x_in e x_out
            # min_eta_inc è l'INCREMENTO angolare (es. 5°), non il valore minimo di eta
            # I bounds su eta verranno applicati dall'ottimizzatore simplex
            # Usiamo una griglia più grossolana (8x8) per ridurre combinazioni problematiche
            simplex_grid_pts = 8  # Griglia iniziale più grossolana per simplex
            
            grid_options = GridOptions(
                in_interval=[x_in_min, x_in_max],
                out_interval=[x_out_min, x_out_max],
                in_pts=None,
                out_pts=None,
                min_eta_inc=np.radians(10),  # Incremento più largo per griglia iniziale (10° invece di 5°)
                num_in_pts=simplex_grid_pts,
                num_out_pts=simplex_grid_pts
            )

            print(f"Bounding box: x=[{x_min:.1f}, {x_max:.1f}], y=[{y_min_extended:.1f}, {y_max*1.1:.1f}]")
            print(f"Bounds simplex:")
            print(f"  x_in: [{x_in_min:.1f}, {x_in_max:.1f}] m (intervallo: {x_in_max-x_in_min:.1f} m)")
            print(f"  x_out: [{x_out_min:.1f}, {x_out_max:.1f}] m (intervallo: {x_out_max-x_out_min:.1f} m)")
            print(f"  η: [{eta_min:.1f}, {eta_max:.1f}]°")
            print(f"Griglia iniziale simplex:")
            print(f"  num_in_pts: {simplex_grid_pts}")
            print(f"  num_out_pts: {simplex_grid_pts}")
            print(f"  min_eta_inc: 10.0° (incremento per griglia iniziale)")
            print(f"  Totale combinazioni: {simplex_grid_pts * simplex_grid_pts} coppie (in,out)")

            # Selettore del metodo di stabilità
            method_label, solver = self._get_solver(params.get('stability_method', 'Bishop'))
            print(f"Metodo di calcolo stabilità: {method_label}")
            
            # Parametri del terreno e stato
            soil_properties, soil_state = self._create_soil_properties_and_state(
                params, ground_surface, layer2_interface, water_table
            )
            
            # Opzioni del metodo
            method_options = Options(
                max_iteration=params.get('max_iterations', 300),
                tolerance=1e-4,
                quadrature=lambda interval: UniformQuadrature(x_interval=interval, num=params['num_slices'])
            )
            
            # Esegui calcolo
            self.dlg.setStatus("Calcolo in corso... (ottimizzazione simplex)")
            
            print("Chiamata a simplexComputation...")
            results, computation_time = simplexComputation(
                solver,
                ground_surface,
                bounding_box,
                soil_properties,
                soil_state,
                grid_options,
                method_options,
                bounds
            )

            print(f"\nCalcolo completato in {computation_time:.2f} secondi")
            
            if results is None:
                raise ValueError("Nessuna superficie di scivolamento valida trovata")
            
            # Verifica che abbiamo un risultato anche se l'ottimizzazione non è perfettamente convergente
            if not hasattr(results, 'fun'):
                raise ValueError("Risultato dell'ottimizzazione non valido")
            
            # Anche se non ha successo completo, se abbiamo un FS usiamolo
            # (a volte simplex raggiunge max iterazioni ma ha comunque un buon risultato)
            factor_of_safety = results.fun
            
            print(f"\nRISULTATO CRITICO:")
            print(f"Fattore di Sicurezza (FS): {factor_of_safety:.4f}")
            print(f"   Successo ottimizzazione: {results.success if hasattr(results, 'success') else 'N/A'}")
            print(f"   Messaggio: {results.message if hasattr(results, 'message') else 'N/A'}")
            print(f"   Iterazioni: {results.nit if hasattr(results, 'nit') else 'N/A'}")
            
            # Warning se non è convergente
            if hasattr(results, 'success') and not results.success:
                print(f"⚠️  ATTENZIONE: L'ottimizzazione non ha completamente convergente, ma il risultato potrebbe essere comunque valido.")

            # Informazioni superficie critica
            if hasattr(results, 'x') and len(results.x) >= 3:
                x_in = float(results.x[0])
                x_out = float(results.x[1])
                eta_deg = float(results.x[2])
                
                print(f"\nGEOMETRIA SUPERFICIE CRITICA:")
                print(f"Punto ingresso (x_in): {x_in:.2f} m")
                print(f"Punto uscita (x_out): {x_out:.2f} m") 
                print(f"Lunghezza superficie: {x_in - x_out:.2f} m")
                print(f"Angolo eta: {eta_deg:.2f}°")
                
                # Ricostruisci la superficie circolare per il grafico usando l'API le_core
                try:
                    # Normalizza per robustezza
                    if x_in <= x_out:
                        print("Nota: x_in <= x_out dal risultato simplex, inverto per la ricostruzione grafica.")
                        x_in, x_out = x_out, x_in
                    eta_deg = max(min(eta_deg, 89.9), 0.1)

                    # Ricostruisci la geometria tramite helper della libreria
                    eta_rad = np.radians(eta_deg)
                    geom = circularSlipSurface.fromInOutAndEta(ground_surface, bounding_box, x_in, x_out, eta_rad)

                    # Campiona l'arco con la funzione esposta dalla geometria
                    x_start, x_end = geom.landslide_interval
                    slip_x = np.linspace(x_start, x_end, 200)
                    slip_y = geom.slip_surface(slip_x)

                    # Salva la superficie critica con metadati
                    self._store_surface('simplex', method_label, slip_x, slip_y, factor_of_safety)

                    # Aggiorna il grafico con tutte le superfici disponibili
                    self._update_profile_with_all_surfaces()
                except Exception as e:
                    print(f"⚠️ Errore nel campionamento della superficie circolare: {e}")
                    # Fallback di visualizzazione: disegna una polilinea di collegamento sul terreno
                    try:
                        x0, x1 = (x_in, x_out) if isinstance(x_in, (int,float)) and isinstance(x_out,(int,float)) else (None, None)
                        if x0 is not None and x1 is not None:
                            xs = np.linspace(min(x0,x1), max(x0,x1), 50)
                            ys = ground_surface(xs) - 0.5  # leggermente sotto la superficie
                            self._store_surface('simplex', method_label, xs, ys, factor_of_safety)
                    except Exception:
                        pass
                    self._update_profile_with_all_surfaces()
            else:
                print("⚠️ Parametri geometrici non disponibili")
                x_in = x_out = eta_deg = "N/A"
                self._update_profile_with_all_surfaces()
                self.dlg.updateProfile(self.profile_distances, self.profile_elevations)
            
            # Prepara output
            # Gestisci il caso in cui i parametri geometrici non siano disponibili
            if isinstance(x_in, (int, float)) and isinstance(x_out, (int, float)):
                x_in_str = f"{x_in:.2f}"
                x_out_str = f"{x_out:.2f}"
                length_str = f"{x_in - x_out:.2f}"
            else:
                x_in_str = str(x_in)
                x_out_str = str(x_out)
                length_str = "N/A"
            
            eta_str = f"{eta_deg:.2f}" if isinstance(eta_deg, (int, float)) else str(eta_deg)
            
            # Status della convergenza e dettagli
            has_success = hasattr(results, 'success') and results.success
            convergence_status = "✓" if has_success else "⚠️ (non completamente convergente)"
            opt_message = str(results.message) if hasattr(results, 'message') and results.message is not None else 'N/A'
            opt_nit = str(results.nit) if hasattr(results, 'nit') else 'N/A'
            
            # Info stratigrafia per output
            strat_info = self._format_stratigraphy_info(params)
            
            results_text = f"""ANALISI DI STABILITÀ - {method_label.upper()} (SIMPLEX)

Parametri utilizzati:
- Peso specifico (γ): {float(params['gamma']):.1f} kN/m³
- Coesione (c): {float(params['cohesion']):.1f} kPa
- Angolo di attrito (φ): {float(params['friction_angle']):.1f}°
- Numero conci: {int(params['num_slices'])}
- Tempo: {float(computation_time):.2f} s

{strat_info}

BOUNDS SIMPLEX (valori assoluti):
- x_in: [{float(x_in_min):.1f}, {float(x_in_max):.1f}] m
- x_out: [{float(x_out_min):.1f}, {float(x_out_max):.1f}] m
- η: [{float(eta_min):.1f}, {float(eta_max):.1f}]°

BOUNDS SIMPLEX (percentuali rispetto a L_max={float(x_max):.1f}m):
- x_in: [{float(params['x_in_min'])*100:.1f}%, {float(params['x_in_max'])*100:.1f}%]
- x_out: [{float(params['x_out_min'])*100:.1f}%, {float(params['x_out_max'])*100:.1f}%]

SUPERFICIE DI SCIVOLAMENTO CRITICA:
- Punto ingresso (monte): x = {x_in_str} m
- Punto uscita (valle): x = {x_out_str} m
- Lunghezza superficie: {length_str} m
- Angolo eta: {eta_str}°

RISULTATI:
Fattore di Sicurezza (FS): {float(factor_of_safety):.3f} ({method_label})

Condizione: {'STABILE (FS ≥ 1.5)' if factor_of_safety >= 1.5 else 'INSTABILE (FS < 1.0)' if factor_of_safety < 1.0 else 'MARGINALMENTE STABILE (1.0 ≤ FS < 1.5)'}

Ottimizzazione:
- Convergenza: {convergence_status}
- Messaggio: {opt_message}
- Iterazioni: {opt_nit}
"""
            
            self.dlg.updateStabilityResults(results_text, 'simplex')
            self.dlg.setStatus(f"Analisi simplex completata. FS = {factor_of_safety:.3f}")
            
            print(f"\nRIEPILOGO:")
            print(f"FS critico: {factor_of_safety:.4f}")
            print("=" * 60)
            print("ANALISI DI STABILITÀ SIMPLEX - FINE")
            print("=" * 60)
            
        except Exception as e:
            import traceback
            error_msg = f"Errore nell'analisi simplex:\n{str(e)}\n\n{traceback.format_exc()}"
            self.dlg.setStatus(f"Errore: {str(e)}")
            self.dlg.updateStabilityResults(error_msg, 'simplex')
            print(f"\nERRORE NELL'ANALISI SIMPLEX:\n{traceback.format_exc()}")

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
    
    def _create_layer2_interface_function(self, params, ground_surface):
        """Crea una funzione per l'interfaccia del secondo strato."""
        mode = params.get('layer2_definition_mode', 0)
        
        if mode == 0:  # Profondità costante dal piano campagna
            depth = params.get('layer2_const_depth', 5.0)
            return lambda x: ground_surface(x) - depth
        
        elif mode == 1:  # Da raster
            raster_layer = params.get('layer2_raster_layer')
            if raster_layer:
                # Crea funzione che campiona il raster (profondità) e sottrae dalla superficie
                def layer2_from_raster(x):
                    depths = self._sample_raster_at_x_coordinates(x, raster_layer, default_value=5.0)
                    return ground_surface(x) - depths
                return layer2_from_raster
            else:
                # Fallback
                depth = params.get('layer2_const_depth', 5.0)
                return lambda x: ground_surface(x) - depth
        
        elif mode == 2:  # Quota assoluta
            elevation = params.get('layer2_elevation', 0.0)
            return lambda x: np.full_like(x, elevation, dtype=float)
        
        # Fallback
        depth = params.get('layer2_const_depth', 5.0)
        return lambda x: ground_surface(x) - depth
    
    def _create_water_table_function(self, params, ground_surface):
        """Crea una funzione per la falda freatica."""
        mode = params.get('water_definition_mode', 0)
        
        if mode == 0:  # Profondità costante dal piano campagna
            depth = params.get('water_const_depth', 2.0)
            return lambda x: ground_surface(x) - depth
        
        elif mode == 1:  # Da raster
            raster_layer = params.get('water_raster_layer')
            if raster_layer:
                # Crea funzione che campiona il raster (profondità) e sottrae dalla superficie
                def water_from_raster(x):
                    depths = self._sample_raster_at_x_coordinates(x, raster_layer, default_value=2.0)
                    return ground_surface(x) - depths
                return water_from_raster
            else:
                # Fallback
                depth = params.get('water_const_depth', 2.0)
                return lambda x: ground_surface(x) - depth
        
        elif mode == 2:  # Quota assoluta
            elevation = params.get('water_elevation', 0.0)
            return lambda x: np.full_like(x, elevation, dtype=float)
        
        # Fallback
        depth = params.get('water_const_depth', 2.0)
        return lambda x: ground_surface(x) - depth
    
    def compute_layer2_profile_for_display(self, params):
        """Calcola i valori dell'interfaccia del secondo strato lungo il profilo per la visualizzazione.
        
        Returns:
            Lista di quote (float) o None se non può essere calcolato
        """
        if not self.profile_distances or not self.profile_elevations:
            return None
        
        try:
            # Crea la funzione ground_surface
            ground_surface = self._create_ground_surface_function(
                self.profile_distances, 
                self.profile_elevations
            )
            
            mode = params.get('layer2_definition_mode', 0)
            
            if mode == 0:  # Profondità costante
                depth = params.get('layer2_const_depth', 5.0)
                return [ground_surface(x) - depth for x in self.profile_distances]
            
            elif mode == 1:  # Da raster
                raster_layer = params.get('layer2_raster_layer')
                if not raster_layer or not self.profile_p1 or not self.profile_p2:
                    return None
                
                # Campiona il raster lungo il profilo
                depths = []
                provider = raster_layer.dataProvider()
                band = 1
                no_data = provider.sourceNoDataValue(band)
                extent_length = self.profile_p1.distance(self.profile_p2)
                
                raster_crs = raster_layer.crs()
                project_crs = QgsProject.instance().crs()
                need_transform = project_crs.isValid() and raster_crs.isValid() and (project_crs != raster_crs)
                transformer = None
                if need_transform:
                    transformer = QgsCoordinateTransform(project_crs, raster_crs, QgsProject.instance())
                
                for d in self.profile_distances:
                    t = d / extent_length if extent_length > 0 else 0
                    x = self.profile_p1.x() + (self.profile_p2.x() - self.profile_p1.x()) * t
                    y = self.profile_p1.y() + (self.profile_p2.y() - self.profile_p1.y()) * t
                    pt = QgsPointXY(x, y)
                    
                    if transformer is not None:
                        try:
                            pt = transformer.transform(pt)
                        except Exception:
                            depths.append(5.0)  # Default
                            continue
                    
                    val = self._sample_with_bilinear(provider, pt, band, no_data, raster_layer)
                    depths.append(val if val is not None else 5.0)
                
                # Calcola le quote dell'interfaccia
                return [ground_surface(x) - depth for x, depth in zip(self.profile_distances, depths)]
            
            elif mode == 2:  # Quota assoluta
                elevation = params.get('layer2_elevation', 0.0)
                return [elevation] * len(self.profile_distances)
            
        except Exception as e:
            print(f"Errore calcolo profilo layer2 per visualizzazione: {e}")
            return None
    
    def compute_water_profile_for_display(self, params):
        """Calcola i valori della falda lungo il profilo per la visualizzazione.
        
        Returns:
            Lista di quote (float) o None se non può essere calcolato
        """
        if not self.profile_distances or not self.profile_elevations:
            return None
        
        try:
            # Crea la funzione ground_surface
            ground_surface = self._create_ground_surface_function(
                self.profile_distances, 
                self.profile_elevations
            )
            
            mode = params.get('water_definition_mode', 0)
            
            if mode == 0:  # Profondità costante
                depth = params.get('water_const_depth', 2.0)
                return [ground_surface(x) - depth for x in self.profile_distances]
            
            elif mode == 1:  # Da raster
                raster_layer = params.get('water_raster_layer')
                if not raster_layer or not self.profile_p1 or not self.profile_p2:
                    return None
                
                # Campiona il raster lungo il profilo
                depths = []
                provider = raster_layer.dataProvider()
                band = 1
                no_data = provider.sourceNoDataValue(band)
                extent_length = self.profile_p1.distance(self.profile_p2)
                
                raster_crs = raster_layer.crs()
                project_crs = QgsProject.instance().crs()
                need_transform = project_crs.isValid() and raster_crs.isValid() and (project_crs != raster_crs)
                transformer = None
                if need_transform:
                    transformer = QgsCoordinateTransform(project_crs, raster_crs, QgsProject.instance())
                
                for d in self.profile_distances:
                    t = d / extent_length if extent_length > 0 else 0
                    x = self.profile_p1.x() + (self.profile_p2.x() - self.profile_p1.x()) * t
                    y = self.profile_p1.y() + (self.profile_p2.y() - self.profile_p1.y()) * t
                    pt = QgsPointXY(x, y)
                    
                    if transformer is not None:
                        try:
                            pt = transformer.transform(pt)
                        except Exception:
                            depths.append(2.0)  # Default
                            continue
                    
                    val = self._sample_with_bilinear(provider, pt, band, no_data, raster_layer)
                    depths.append(val if val is not None else 2.0)
                
                # Calcola le quote della falda
                return [ground_surface(x) - depth for x, depth in zip(self.profile_distances, depths)]
            
            elif mode == 2:  # Quota assoluta
                elevation = params.get('water_elevation', 0.0)
                return [elevation] * len(self.profile_distances)
            
        except Exception as e:
            print(f"Errore calcolo profilo falda per visualizzazione: {e}")
            return None
    
    def _create_soil_properties_and_state(self, params, ground_surface, layer2_interface=None, water_table=None):
        """Crea SoilProperties e SoilState in base ai parametri."""
        constant_dry_density = params['gamma']
        
        if params.get('enable_layer2', False) and layer2_interface is not None:
            # Due strati
            constant_dry_density_2 = params.get('gamma_2', 22.0)
            
            # Funzioni che restituiscono parametri diversi sopra/sotto l'interfaccia
            def cohesion_2layer(x, y):
                interface_y = layer2_interface(x)
                c1 = params['cohesion']
                c2 = params.get('cohesion_2', 50.0)
                return np.where(y > interface_y, c1, c2)
            
            def friction_angle_2layer(x, y):
                interface_y = layer2_interface(x)
                phi1 = params['friction_angle']
                phi2 = params.get('friction_angle_2', 30.0)
                return np.where(y > interface_y, phi1, phi2)
            
            def porosity_2layer(x, y):
                interface_y = layer2_interface(x)
                n1 = params['porosity']
                n2 = params.get('porosity_2', 0.25)
                return np.where(y > interface_y, n1, n2)
            
            def dry_density_2layer(x, y):
                interface_y = layer2_interface(x)
                gamma1 = params['gamma']
                gamma2 = params.get('gamma_2', 22.0)
                return np.where(y > interface_y, gamma1, gamma2)
            
            soil_properties = SoilProperties(
                cohesion=cohesion_2layer,
                friction_angle=friction_angle_2layer,
                dry_density=dry_density_2layer,
                porosity=porosity_2layer,
                grain_density=lambda x, y: 0.0 * np.ones_like(x + y)
            )
            
            # Stato del terreno con eventuale falda
            if params.get('enable_water', False) and water_table is not None:
                def saturation_with_water(x, y):
                    water_y = water_table(x)
                    return np.where(y <= water_y, 1.0, 0.0)
                
                def pore_pressure_with_water(x, y):
                    water_y = water_table(x)
                    gamma_w = 9.81  # kN/m³
                    return np.where(y <= water_y, gamma_w * (water_y - y), 0.0)
                
                def dry_density_with_water_2layer(x, y):
                    interface_y = layer2_interface(x)
                    water_y = water_table(x)
                    saturation = np.where(y <= water_y, 1.0, 0.0)
                    gamma1_sat = params['gamma'] + params['porosity'] * saturation * 9.81
                    gamma2_sat = params.get('gamma_2', 22.0) + params.get('porosity_2', 0.25) * saturation * 9.81
                    return np.where(y > interface_y, gamma1_sat, gamma2_sat)
                
                def integrated_density_2layer_water(x, y):
                    # Normalize inputs to numpy arrays for vectorized ops
                    x_arr = np.asarray(x)
                    y_arr = np.asarray(y)
                    interface_y = np.asarray(layer2_interface(x_arr))
                    ground_y = np.asarray(ground_surface(x_arr))

                    # Calcola spessore strato 1 e 2 (element-wise)
                    depth_total = ground_y - y_arr
                    depth_layer1 = np.maximum(0.0, ground_y - np.maximum(y_arr, interface_y))
                    depth_layer2 = np.maximum(0.0, np.minimum(ground_y, interface_y) - y_arr)
                    
                    # Compute effective gamma for each layer element-wise
                    gamma1_eff = dry_density_with_water_2layer(x_arr, ground_y - depth_layer1/2)
                    gamma1_eff = np.where(depth_layer1 > 0.0, gamma1_eff, 0.0)

                    gamma2_eff = dry_density_with_water_2layer(x_arr, interface_y - depth_layer2/2)
                    gamma2_eff = np.where(depth_layer2 > 0.0, gamma2_eff, 0.0)
                    
                    result = gamma1_eff * depth_layer1 + gamma2_eff * depth_layer2
                    # Return a scalar if inputs were scalars, otherwise return array
                    if np.ndim(result) == 0:
                        return float(result)
                    return result
                
                soil_state = SoilState(
                    saturation=saturation_with_water,
                    pore_pressure=pore_pressure_with_water,
                    integrated_density=integrated_density_2layer_water
                )
            else:
                # Senza falda
                def integrated_density_2layer(x, y):
                    interface_y = layer2_interface(x)
                    ground_y = ground_surface(x)
                    
                    # Calcola spessore strato 1 e 2
                    depth_total = ground_y - y
                    depth_layer1 = np.maximum(0, ground_y - np.maximum(y, interface_y))
                    depth_layer2 = np.maximum(0, np.minimum(ground_y, interface_y) - y)
                    
                    return params['gamma'] * depth_layer1 + params.get('gamma_2', 22.0) * depth_layer2
                
                soil_state = SoilState(
                    saturation=lambda x, y: 0.0 * np.ones_like(x + y),
                    pore_pressure=lambda x, y: 0.0 * np.ones_like(x + y),
                    integrated_density=integrated_density_2layer
                )
        else:
            # Singolo strato
            soil_properties = SoilProperties(
                cohesion=lambda x, y: params['cohesion'],
                friction_angle=lambda x, y: params['friction_angle'] * np.ones_like(x + y),
                dry_density=lambda x, y: params['gamma'] * np.ones_like(x + y),
                porosity=lambda x, y: params['porosity'] * np.ones_like(x + y),
                grain_density=lambda x, y: 0.0 * np.ones_like(x + y)
            )
            
            # Stato del terreno con eventuale falda
            if params.get('enable_water', False) and water_table is not None:
                def saturation_with_water(x, y):
                    water_y = water_table(x)
                    return np.where(y <= water_y, 1.0, 0.0)
                
                def pore_pressure_with_water(x, y):
                    water_y = water_table(x)
                    gamma_w = 9.81  # kN/m³
                    return np.where(y <= water_y, gamma_w * (water_y - y), 0.0)
                
                def dry_density_with_water(x, y):
                    water_y = water_table(x)
                    saturation = np.where(y <= water_y, 1.0, 0.0)
                    return params['gamma'] + params['porosity'] * saturation * 9.81
                
                soil_state = SoilState(
                    saturation=saturation_with_water,
                    pore_pressure=pore_pressure_with_water,
                    integrated_density=lambda x, y: dry_density_with_water(x, y) * (ground_surface(x) - y)
                )
            else:
                # Senza falda
                soil_state = SoilState(
                    saturation=lambda x, y: 0.0 * np.ones_like(x + y),
                    pore_pressure=lambda x, y: 0.0 * np.ones_like(x + y),
                    integrated_density=lambda x, y: params['gamma'] * (ground_surface(x) - y)
                )
        
        return soil_properties, soil_state
    
    def _format_stratigraphy_info(self, params):
        """Formatta le informazioni di stratigrafia per l'output."""
        info = []
        
        if params.get('enable_layer2', False):
            info.append("STRATIGRAFIA:")
            info.append(f"- Secondo strato attivo")
            mode = params.get('layer2_definition_mode', 0)
            if mode == 0:
                info.append(f"  Profondità: {params.get('layer2_const_depth', 5.0):.2f} m dal piano campagna")
            elif mode == 1:
                info.append(f"  Profondità da raster")
            elif mode == 2:
                info.append(f"  Quota assoluta: {params.get('layer2_elevation', 0.0):.2f} m")
            info.append(f"  Parametri strato 2: γ₂={params.get('gamma_2', 22.0):.1f} kN/m³, c₂={params.get('cohesion_2', 50.0):.1f} kPa, φ₂={params.get('friction_angle_2', 30.0):.1f}°, n₂={params.get('porosity_2', 0.25):.2f}")
        
        if params.get('enable_water', False):
            if not info:
                info.append("")
            info.append("FALDA FREATICA:")
            info.append(f"- Falda attiva")
            mode = params.get('water_definition_mode', 0)
            if mode == 0:
                info.append(f"  Profondità: {params.get('water_const_depth', 2.0):.2f} m dal piano campagna")
            elif mode == 1:
                info.append(f"  Profondità da raster")
            elif mode == 2:
                info.append(f"  Quota assoluta: {params.get('water_elevation', 0.0):.2f} m")
        
        return '\n'.join(info) if info else ""

    def _update_profile_with_all_surfaces(self):
        """Aggiorna il grafico del profilo con tutte le superfici critiche calcolate."""
        if not self.profile_distances or not self.profile_elevations:
            return
        
        surfaces_list = []
        for idx, s in enumerate(self.slip_surfaces):
            color = self._get_color_for_surface(idx, s['search'], s['method'])
            label = f"{'Simplex' if s['search']=='simplex' else 'Griglia'} – {s['method']} (FS={s['fs']:.3f})"
            surfaces_list.append({'x': s['x'], 'y': s['y'], 'color': color, 'label': label})

        if surfaces_list:
            self.dlg.updateProfile(self.profile_distances, self.profile_elevations, slip_surfaces_list=surfaces_list)
        else:
            self.dlg.updateProfile(self.profile_distances, self.profile_elevations)

    def _get_solver(self, method_name):
        """Ritorna (label, funzione_solver) a partire dal nome scelto in UI."""
        name = (method_name or '').strip().lower()
        if 'morgen' in name or 'morger' in name:
            return ('Morgenstern-Price', morgerstern_price)
        if 'spencer' in name:
            return ('Spencer', spencer)
        # default
        return ('Bishop', bishop)

    def _get_color_for_surface(self, index, search_type, method_label):
        """Genera un colore univoco per ogni superficie mantenendo la distinzione caldi/freddi.
        
        Palette colori:
        - Griglia (freddi): blu, ciano, verde, azzurro, turchese, verde acqua...
        - Simplex (caldi): rosso, arancione, rosa, magenta, corallo, cremisi...
        """
        # Palette estesa per griglia (colori freddi)
        grid_palette = [
            '#1f77b4',  # blu
            '#17becf',  # ciano
            '#2ca02c',  # verde
            '#00CED1',  # turchese scuro
            '#4682B4',  # blu acciaio
            '#20B2AA',  # verde acqua chiaro
            '#5F9EA0',  # blu cadetto
            '#008B8B',  # ciano scuro
            '#00BFFF',  # azzurro intenso
            '#4169E1',  # blu reale
            '#6495ED',  # blu fiordaliso
            '#87CEEB',  # celeste
        ]
        
        # Palette estesa per simplex (colori caldi)
        simplex_palette = [
            '#d62728',  # rosso
            '#ff7f0e',  # arancione
            '#e377c2',  # rosa
            '#DC143C',  # cremisi
            '#FF6347',  # pomodoro
            '#FF4500',  # arancione rosso
            '#FF69B4',  # rosa caldo
            '#DB7093',  # viola pallido
            '#CD5C5C',  # rosso indiano
            '#F08080',  # corallo chiaro
            '#FA8072',  # salmone
            '#FFA07A',  # salmone chiaro
        ]
        
        # Seleziona la palette appropriata
        palette = simplex_palette if search_type == 'simplex' else grid_palette
        
        # Usa l'indice per selezionare il colore (con wrapping se necessario)
        color = palette[index % len(palette)]
        
        return color

    def _store_surface(self, search, method_label, x, y, fs):
        """Aggiunge una superficie calcolata all'elenco, mantenendo la storia."""
        try:
            self.slip_surfaces.append({'search': search, 'method': method_label, 'x': x, 'y': y, 'fs': float(fs)})
        except Exception:
            pass

