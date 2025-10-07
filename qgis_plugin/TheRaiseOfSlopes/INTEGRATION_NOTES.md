# Integrazione Framework GLE nel Plugin QGIS

## Modifiche Apportate

### 1. Integrazione del Framework Limit-Equilibrium

Il plugin è stato aggiornato per utilizzare le strutture dati e i metodi del framework `limit-equilibrium` invece di un'implementazione semplificata.

**Moduli importati:**
- `base_classes`: `SoilProperties`, `SoilState`, `UniformQuadrature`, `Options`
- `circularSlipSurface`: `circularSlipSurface`
- `gle`: `morgerstern_price`
- `gridOfCircles`: `GridOptions`, `gridComputation`

### 2. Funzione Ground Surface Lineare a Tratti

È stata implementata la funzione `_create_ground_surface_function()` che:
- Prende i punti campionati dal DEM (distanze e quote)
- Filtra i valori `None` (nodata)
- Crea un interpolatore lineare con `scipy.interpolate.interp1d`
- Restituisce una funzione compatibile con il framework GLE

Questa funzione rispetta il requirement che la superficie topografica sia definita come funzione, lineare a tratti nel caso di profilo campionato su DEM.

### 3. Analisi di Stabilità con Morgenstern & Price

La funzione `_analyze_stability()` ora:

1. **Crea la ground_surface function** dal profilo campionato
2. **Calcola il bounding box** appropriato per l'analisi
3. **Definisce una griglia di cerchi** per la ricerca della superficie critica:
   - Punti di ingresso: nella parte alta del pendio (70%-100% della lunghezza)
   - Punti di uscita: nella parte bassa (0%-30% della lunghezza)  
   - 8×8 = 64 cerchi testati
   
4. **Imposta i parametri del terreno** usando le lambda functions richieste:
   - `cohesion(x, y)`: coesione costante in kPa
   - `friction_angle(x, y)`: angolo di attrito costante in gradi
   - `dry_density(x, y)`: peso specifico costante in kN/m³
   
5. **Definisce lo stato del terreno**:
   - `saturation(x, y)`: saturazione costante
   - `pore_pressure(x, y)`: pressione interstiziale
   - `integrated_density(x, y)`: densità integrata dalla superficie

6. **Esegue il calcolo** con `gridComputation()` che:
   - Testa tutte le superfici circolari nella griglia
   - Calcola il FS per ciascuna usando `morgerstern_price()`
   - Ritorna i risultati ordinati per FS crescente

7. **Presenta i risultati** mostrando:
   - Fattore di sicurezza minimo (più critico)
   - Geometria della superficie critica (punti ingresso/uscita, centro, raggio)
   - Numero di conci analizzati
   - Tempo di calcolo
   - Condizione di stabilità (STABILE/MARGINALMENTE STABILE/INSTABILE)

### 4. Interfaccia Utente

L'interfaccia nella scheda "Analisi di Stabilità" include:
- **Parametri geotecnici**: γ, c, φ
- **Parametri dell'analisi**: fattore profondità per il bounding box
- **Condizioni idrauliche**: livello freatico (preparato per future implementazioni)
- **Area risultati**: mostra output dettagliato dell'analisi

### 5. Gestione Errori

- Verifica disponibilità moduli `limit-equilibrium`
- Gestione graceful se i moduli non sono disponibili
- Traceback completo in caso di errori per debugging

## Utilizzo

1. Caricare un DEM in QGIS
2. Selezionare due punti sul DEM per definire il profilo
3. Calcolare il profilo altimetrico
4. Passare alla scheda "Analisi di Stabilità"
5. Impostare i parametri geotecnici
6. Eseguire l'analisi

## Note Tecniche

- La funzione `ground_surface(x)` accetta array numpy e ritorna array numpy
- L'interpolazione è lineare tra i punti campionati
- L'extrapolazione è abilitata per gestire punti fuori dal range
- Il framework GLE usa superfici di scivolamento circolari
- Il metodo di Morgenstern & Price è un metodo di equilibrio limite generale (GLE)

## Requisiti

- QGIS 3.x
- NumPy
- SciPy  
- Moduli custom del framework `limit-equilibrium` (in `src/limit-equilibrium/`)

## File Modificati

- `the_raise_of_slopes_plugin.py`: logica principale del plugin
- Nessuna modifica richiesta a `profile_dialog.py` (interfaccia già predisposta)

## Backup

Il file originale è stato salvato come `the_raise_of_slopes_plugin_OLD.py`
