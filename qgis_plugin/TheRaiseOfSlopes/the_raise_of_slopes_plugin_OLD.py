# -*- coding: utf-8 -*-
"""Main entry point for QGIS plugin.

Funzionalità implementate in questa fase:
 - Selezione di due punti sul DEM
 - Campionamento profilo altimetrico lungo la linea
 - Gestione nodata e trasformazione CRS (progetto -> raster)
 - Visualizzazione grafica e export CSV
 - Analisi di stabilità con metodo Morgenstern & Price usando il framework GLE

Nota: gli import QGIS vanno mantenuti all'inizio per chiarezza.
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
# Aggiungiamo il percorso al modulo limit-equilibrium
plugin_dir = os.path.dirname(__file__)
le_path = os.path.join(os.path.dirname(os.path.dirname(plugin_dir)), 'src', 'limit-equilibrium')
if le_path not in sys.path:
    sys.path.append(le_path)

try:
    from base_classes import SoilProperties, SoilState, UniformQuadrature, Options
    from circularSlipSurface import circularSlipSurface
    from gle import morgerstern_price
    from gridOfCircles import GridOptions, gridComputation
    LIMIT_EQUILIBRIUM_AVAILABLE = True
except ImportError as e:
    LIMIT_EQUILIBRIUM_AVAILABLE = False
    print(f"Avviso: Moduli limit-equilibrium non disponibili: {e}")


def classFactory(iface):  # QGIS chiamerà questa funzione
    return TheRaiseOfSlopesPlugin(iface)


class TheRaiseOfSlopesPlugin:
    def __init__(self, iface):
        """Inizializza lo stato del plugin.

        :param iface: interfaccia QGIS fornita da classFactory
        """
        self.iface = iface
        self.action = None
        self.dlg = None
        self.selection_tool = None
        self.profile_distances = []  # progressive X
        self.profile_elevations = []  # Z quota
        
        # Rubber bands per visualizzazione placeholder
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
        """Mostra il dialog principale creando le connessioni la prima volta."""
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
        # Pulisce eventuali placeholder precedenti
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
        # Rimuovi eventuali elementi precedenti
        self._clear_rubber_bands()
        
        # Crea rubber band per il primo punto (rosso, più grande)
        self.p1_rubber_band = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.PointGeometry)
        self.p1_rubber_band.setColor(QColor(255, 0, 0))  # Rosso
        self.p1_rubber_band.setIconSize(15)  # Più grande per indicare P1
        self.p1_rubber_band.addPoint(p1)
        
        self.dlg.setStatus("Primo punto (P1) selezionato. Seleziona il secondo punto (P2)...")

    def _create_placeholder(self, p1, p2):
        """Crea un placeholder visivo sulla mappa per i punti selezionati."""
        # Crea rubber band per il secondo punto (verde, dimensione normale)
        self.p2_rubber_band = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.PointGeometry)
        self.p2_rubber_band.setColor(QColor(0, 255, 0))  # Verde per P2
        self.p2_rubber_band.setIconSize(12)  # Dimensione normale
        self.p2_rubber_band.addPoint(p2)
        
        # Crea rubber band per la linea
        self.line_rubber_band = QgsRubberBand(self.iface.mapCanvas(), QgsWkbTypes.LineGeometry)
        self.line_rubber_band.setColor(QColor(0, 0, 255))  # Blu
        self.line_rubber_band.setWidth(2)
        self.line_rubber_band.addPoint(p1)
        self.line_rubber_band.addPoint(p2)

    def _on_points_selected(self, p1, p2):
        self.dlg.setSelectedPoints(p1, p2)
        self.dlg.setStatus("Punti selezionati. Premi 'Calcola profilo'.")
        # Crea il placeholder visivo
        self._create_placeholder(p1, p2)
        self._restore_map_tool()

    def _compute_profile(self, raster_layer, p1, p2):
        """Campiona il profilo altimetrico fra i due punti.

        Strategia:
            1. Determina un passo di campionamento basato sulla dimensione media dei pixel del raster
            2. Interpola coordinate lungo il segmento (spazio parametrico t)
            3. Trasforma le coordinate nel CRS del raster se necessario
            4. Esegue campionamento elevazione con nearest + fallback bilineare
            5. Accumula liste distance/elevation e aggiorna il dialog
        """
        if not raster_layer or not p1 or not p2:
            self.dlg.setStatus("Parametri mancanti per il profilo.")
            return
        # Calcolo campioni lungo il segmento
        provider = raster_layer.dataProvider()
        extent_length = p1.distance(p2)
        if extent_length == 0:
            self.dlg.setStatus("I due punti coincidono.")
            return
        # passo = dimensione pixel media (x e y)
        px = raster_layer.rasterUnitsPerPixelX()
        py = raster_layer.rasterUnitsPerPixelY()
        step = (abs(px) + abs(py)) / 2.0
        if step <= 0:
            step = extent_length / 100.0  # fallback 100 segmenti
        n = int(extent_length / step) + 1
        distances = []
        elevations = []
        band = 1
        no_data = provider.sourceNoDataValue(band)
        # Controllo CRS: se i punti (canvas) hanno CRS diverso dal raster li trasformo
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
                    # Se trasformazione fallisce salto il punto
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
        """Esporta il profilo in CSV (distanza, quota)."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write('distanza,quota\n')
                for d, z in zip(self.profile_distances, self.profile_elevations):
                    f.write(f"{d},{z}\n")
            self.dlg.setStatus(f"Profilo salvato: {path}")
        except Exception as e:
            self.dlg.setStatus(f"Errore salvataggio: {e}")

    def _sample_with_bilinear(self, provider, pt, band, no_data, raster_layer):
        """Restituisce valore campionato con fallback bilineare.

        1. Tenta sample diretto (nearest)
        2. Se None o nodata prova a leggere i 4 pixel del quadrato circostante e interpolare
        3. Se uno dei 4 è nodata -> ritorna None.
        """
        import math
        val, ok = provider.sample(pt, band)  # nearest neighbor
        if ok:
            if no_data is not None:
                if (isinstance(no_data, float) and isinstance(val, float) and math.isnan(no_data) and math.isnan(val)) or val == no_data:
                    pass  # procederà a bilineare
                else:
                    return val
            else:
                return val

        # Bilinear fallback
        # Coordinate raster (col, row) floating
        # Uso geotrasformazione indiretta tramite extent e pixel size (assume north-up)
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
        # Recupero dimensioni raster
        stats = provider.xSize(), provider.ySize()
        max_col = stats[0] - 1
        max_row = stats[1] - 1
        if not (0 <= col0 <= max_col and 0 <= col1 <= max_col and 0 <= row0 <= max_row and 0 <= row1 <= max_row):
            return None
        def read_cell(c, r):
            # centro pixel
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
        # Frazioni interne al pixel
        dx = col_f - col0
        dy = row_f - row0
        # Interpolazione bilineare
        v0 = v00 * (1 - dx) + v10 * dx
        v1 = v01 * (1 - dx) + v11 * dx
        vb = v0 * (1 - dy) + v1 * dy
        return vb

    def _analyze_stability(self, params):
        """Esegue l'analisi di stabilità di Morgenstern & Price usando il framework GLE."""
        # Verifica che il profilo sia stato calcolato
        if not self.profile_distances or not self.profile_elevations:
            self.dlg.setStatus("Calcola prima il profilo altimetrico.")
            return
        
        if not LIMIT_EQUILIBRIUM_AVAILABLE:
            error_msg = "Moduli limit-equilibrium non disponibili. Verificare l'installazione."
            self.dlg.setStatus(error_msg)
            self.dlg.updateStabilityResults(error_msg)
            return
        
        try:
            # Crea la funzione ground_surface lineare a tratti dal profilo campionato
            ground_surface = self._create_ground_surface_function(
                self.profile_distances, 
                self.profile_elevations
            )
            
            # Calcola il bounding box dal profilo
            valid_elevations = [e for e in self.profile_elevations if e is not None]
            if not valid_elevations:
                raise ValueError("Nessun dato valido nel profilo")
            
            x_min = self.profile_distances[0]
            x_max = self.profile_distances[-1]
            y_min = min(valid_elevations)
            y_max = max(valid_elevations)
            
            # Espandi il bounding box per includere la superficie di scivolamento
            y_min_extended = y_min - (y_max - y_min) * params['depth_factor']
            bounding_box = np.array([[x_min, x_max], [y_min_extended, y_max * 1.1]])
            
            # Prepara le opzioni della griglia di ricerca
            grid_options = GridOptions(
                in_interval=[x_max * 0.7, x_max],  # Punto di ingresso nella parte alta
                out_interval=[x_min, x_min + (x_max - x_min) * 0.3],  # Punto di uscita nella parte bassa
                min_eta_inc=np.radians(5),
                num_in_pts=8,
                num_out_pts=8
            )
            
            # Parametri del terreno (conversione a kN/m³ e kPa)
            constant_dry_density = params['gamma']  # già in kN/m³
            soil_properties = SoilProperties(
                cohesion=lambda x, y: params['cohesion'] * np.ones_like(x + y),  # kPa
                friction_angle=lambda x, y: params['friction_angle'] * np.ones_like(x + y),  # gradi
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
            
            # Esegui il calcolo sulla griglia
            self.dlg.setStatus("Calcolo in corso... (griglia di cerchi)")
            results, computation_time = gridComputation(
                morgerstern_price,
                ground_surface,
                bounding_box,
                soil_properties,
                soil_state,
                grid_options,
                method_options
            )
            
            # Prendi il risultato con FS minimo (più critico)
            if not results:
                raise ValueError("Nessuna superficie di scivolamento valida trovata")
            
            critical_result = results[0]  # già ordinato per FS crescente
            factor_of_safety = critical_result.factor_of_safety
            
            # Estrai informazioni sulla superficie critica
            triplet = critical_result.inputs[0].slip_surface
            num_slices = len(critical_result.nodes[0])
            
            # Prepara i risultati
            results_text = f"""ANALISI DI STABILITÀ - MORGENSTERN & PRICE (GLE)

Parametri utilizzati:
- Peso specifico (γ): {params['gamma']:.1f} kN/m³
- Coesione (c): {params['cohesion']:.1f} kPa
- Angolo di attrito (φ): {params['friction_angle']:.1f}°
- Numero di conci analizzati: {num_slices}
- Griglia di ricerca: {grid_options.num_in_pts} × {grid_options.num_out_pts} = {grid_options.num_in_pts * grid_options.num_out_pts} cerchi
- Tempo di calcolo: {computation_time:.2f} s

SUPERFICIE DI SCIVOLAMENTO CRITICA:
- Punto di ingresso: x = {triplet.in_pt:.2f} m
- Punto di uscita: x = {triplet.out_pt:.2f} m
- Angolo eta: {np.degrees(triplet.eta):.1f}°
- Centro del cerchio: ({triplet.center[0]:.2f}, {triplet.center[1]:.2f}) m
- Raggio: {triplet.radius:.2f} m

RISULTATI:
Fattore di Sicurezza (FS): {factor_of_safety:.3f}

Condizione: {'STABILE (FS ≥ 1.5)' if factor_of_safety >= 1.5 else 'INSTABILE (FS < 1.0)' if factor_of_safety < 1.0 else 'MARGINALMENTE STABILE (1.0 ≤ FS < 1.5)'}

Nota: Sono state analizzate {len(results)} superfici di scivolamento circolari.
Il risultato mostrato è quello con il fattore di sicurezza minimo (più critico).
"""
            
            # Aggiorna l'interfaccia
            self.dlg.updateStabilityResults(results_text)
            self.dlg.setStatus(f"Analisi completata. FS minimo = {factor_of_safety:.3f} ({len(results)} superfici analizzate)")
            
        except Exception as e:
            import traceback
            error_msg = f"Errore nell'analisi di stabilità:\n{str(e)}\n\n{traceback.format_exc()}"
            self.dlg.setStatus(f"Errore: {str(e)}")
            self.dlg.updateStabilityResults(error_msg)

    def _create_ground_surface_function(self, distances, elevations):
        """Crea una funzione lineare a tratti per la superficie del terreno.
        
        Args:
            distances: lista delle distanze progressive
            elevations: lista delle quote corrispondenti
            
        Returns:
            Una funzione che interpola linearmente le quote dato x
        """
        # Filtra i valori None
        valid_points = [(d, e) for d, e in zip(distances, elevations) if e is not None]
        if len(valid_points) < 2:
            raise ValueError("Dati insufficienti per creare la funzione del terreno")
        
        valid_distances, valid_elevations = zip(*valid_points)
        
        # Crea interpolatore lineare (piecewise linear)
        interpolator = interpolate.interp1d(
            valid_distances, 
            valid_elevations, 
            kind='linear',
            fill_value='extrapolate'
        )
        
        # Ritorna una funzione che accetta array numpy
        def ground_surface(x):
            return interpolator(x)
        
        return ground_surface

    def _interpolate_elevation(self, x, distances, elevations):
        """Interpola linearmente l'elevazione alla posizione x (funzione backward compatible)."""    def _morgenstern_price_analysis(self, distances, elevations, params):
        """
        Implementazione semplificata del metodo di Morgenstern & Price.
        
        Questo è un'implementazione di base per scopi dimostrativi.
        Per analisi professionali, utilizzare software specializzati.
        """
        import math
        
        # Filtra i valori None
        valid_points = [(d, e) for d, e in zip(distances, elevations) if e is not None]
        if len(valid_points) < 3:
            raise ValueError("Profilo insufficiente per l'analisi")
        
        distances_clean, elevations_clean = zip(*valid_points)
        
        # Parametri del terreno
        gamma = params['gamma']  # kN/m³
        c = params['cohesion']   # kPa
        phi = math.radians(params['friction_angle'])  # radianti
        num_slices = params['num_slices']
        depth_factor = params['depth_factor']
        water_table = params['water_table']
        
        # Calcola la lunghezza totale del pendio
        total_length = distances_clean[-1] - distances_clean[0]
        slice_width = total_length / num_slices
        
        # Variabili per il calcolo
        sum_driving_moments = 0.0
        sum_resisting_moments = 0.0
        
        # Centro di rotazione approssimativo (punto medio più in profondità)
        center_x = (distances_clean[0] + distances_clean[-1]) / 2
        max_elevation = max(elevations_clean)
        min_elevation = min(elevations_clean)
        center_y = min_elevation - (max_elevation - min_elevation) * depth_factor
        
        # Analisi per conci
        for i in range(num_slices):
            # Posizione del concio
            x = distances_clean[0] + (i + 0.5) * slice_width
            
            # Interpola l'elevazione alla posizione x
            y_surface = self._interpolate_elevation(x, distances_clean, elevations_clean)
            if y_surface is None:
                continue
            
            # Calcola la profondità della superficie di scivolamento
            # Superficie di scivolamento circolare semplificata
            dx = x - center_x
            dy_max = abs(y_surface - center_y)
            radius = math.sqrt(dx**2 + dy_max**2)
            
            # Altezza del concio (dall'alto alla superficie di scivolamento)
            slice_height = dy_max * 0.7  # Semplificazione
            
            # Peso del concio
            slice_area = slice_width * slice_height
            weight = slice_area * gamma
            
            # Angolo della superficie di scivolamento
            if dx != 0:
                alpha = math.atan(dy_max / abs(dx))
            else:
                alpha = math.pi / 2
            
            # Pressione dell'acqua (semplificata)
            if y_surface + water_table > center_y:
                water_height = min(slice_height, y_surface + water_table - center_y)
                water_pressure = 9.81 * water_height  # kPa
            else:
                water_pressure = 0.0
            
            # Forze tangenziali e normali
            normal_force = weight * math.cos(alpha) - water_pressure * slice_width
            tangential_force = weight * math.sin(alpha)
            
            # Resistenza al taglio (Mohr-Coulomb)
            shear_resistance = c * slice_width + normal_force * math.tan(phi)
            
            # Momenti rispetto al centro di rotazione
            moment_arm = radius
            driving_moment = tangential_force * moment_arm
            resisting_moment = shear_resistance * moment_arm
            
            sum_driving_moments += driving_moment
            sum_resisting_moments += resisting_moment
        
        # Fattore di sicurezza
        if sum_driving_moments > 0:
            factor_of_safety = sum_resisting_moments / sum_driving_moments
        else:
            factor_of_safety = 999.0  # Pendio stabile
        
        return factor_of_safety

    return ground_surface

    def _interpolate_elevation(self, x, distances, elevations):
        """Interpola linearmente l'elevazione alla posizione x (funzione backward compatible)."""
        if x <= distances[0]:
            return elevations[0]
        if x >= distances[-1]:
            return elevations[-1]
        
        for i in range(len(distances) - 1):
            if distances[i] <= x <= distances[i + 1]:
                # Interpolazione lineare
                t = (x - distances[i]) / (distances[i + 1] - distances[i])
                return elevations[i] + t * (elevations[i + 1] - elevations[i])
        
        return None
