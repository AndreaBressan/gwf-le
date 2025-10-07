# The Raise Of Slopes - Plugin QGIS

Plugin QGIS per l'analisi di stabilità dei versanti utilizzando il metodo di Morgerstern & Price (General Limit Equilibrium).

## Funzionalità

### 1. Profilo Altimetrico
- Selezione di due punti sul DEM
- Campionamento automatico del profilo
- Interpolazione bilineare per valori precisi
- Gestione trasformazioni CRS
- Visualizzazione grafica interattiva
- Export in formato CSV

### 2. Analisi di Stabilità
- Metodo di **Morgenstern & Price** (GLE completo)
- Ricerca automatica della superficie di scivolamento critica
- Griglia di superfici circolari
- Parametri geotecnici configurabili (γ, c, φ)
- Output dettagliato con geometria della superficie critica

## Struttura del Plugin

Il plugin è **autocontenuto** con tutti i moduli necessari inclusi:

```
TheRaiseOfSlopes/
├── __init__.py
├── the_raise_of_slopes_plugin.py
├── le_core/                    # ← Framework limit-equilibrium integrato
│   ├── base_classes.py
│   ├── gle.py
│   ├── circularSlipSurface.py
│   └── ...
├── tools/
└── ui/
```

## Installazione

### Metodo Automatico (Raccomandato) 🚀

Dalla directory principale del progetto:

```bash
# Prepara e installa il plugin in un solo comando
./install_qgis_plugin.sh
```

Lo script:
1. Copia i moduli `limit-equilibrium` in `le_core/`
2. Installa il plugin nella directory di QGIS
3. Mostra istruzioni per abilitarlo

### Metodo Manuale

```bash
# 1. Prepara il plugin (copia moduli)
./setup_qgis_plugin.sh

# 2. Copia nella directory QGIS
# macOS:
cp -r qgis_plugin/TheRaiseOfSlopes ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/

# Linux:
cp -r qgis_plugin/TheRaiseOfSlopes ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/

# Windows:
# Copia in: %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\
```

### 3. Abilita in QGIS

1. Apri/Riavvia QGIS
2. **Plugin → Gestisci e installa plugin**
3. Scheda **Installati**
4. Abilita **The Raise Of Slopes**

## Utilizzo Rapido

### 1️⃣ Calcola Profilo

1. Carica un DEM in QGIS
2. Apri plugin: **Plugin → The Raise Of Slopes**
3. Seleziona DEM e clicca **"Seleziona 2 punti"**
4. Clicca due punti sul DEM (monte → valle)
5. **"Calcola profilo"**

### 2️⃣ Analisi Stabilità

1. Vai alla scheda **"Analisi di Stabilità"**
2. Imposta parametri geotecnici:
   - Peso specifico (γ): 18-22 kN/m³
   - Coesione (c): 0-50 kPa
   - Angolo di attrito (φ): 20-40°
3. **"Esegui Analisi"**
4. Visualizza risultati e FS

## Interpretazione Risultati

### Fattore di Sicurezza (FS)

| FS | Condizione | Significato |
|----|-----------|-------------|
| **≥ 1.5** | ✅ STABILE | Condizioni sicure |
| **1.0 - 1.5** | ⚠️ MARGINALE | Attenzione richiesta |
| **< 1.0** | ❌ INSTABILE | Rischio collasso |

### Output dell'Analisi

- **FS minimo**: fattore di sicurezza critico
- **Superficie critica**: geometria del cerchio di scivolamento
- **64 cerchi testati**: griglia 8×8 di superfici possibili
- **Tempo calcolo**: performance dell'analisi

## Dipendenze

### ✅ Già Incluse in QGIS
- NumPy, SciPy, Matplotlib

### ✅ Incluse nel Plugin  
- Framework `limit-equilibrium` (nella cartella `le_core/`)

**Nessuna installazione aggiuntiva richiesta!**

## Aggiornamento

Quando `src/limit-equilibrium/` viene modificato:

```bash
# Aggiorna e reinstalla
./install_qgis_plugin.sh
```

## Architettura Tecnica

### Organizzazione Plugin

Il plugin è **autocontenuto**: i moduli `limit-equilibrium` sono **copiati** in `le_core/` invece di usare path esterni. Questo permette:

- ✅ Funzionamento ovunque venga copiato il plugin
- ✅ Nessuna dipendenza da strutture di directory esterne
- ✅ Installazione semplice in QGIS
- ⚠️ Codice duplicato (va aggiornato con `setup_qgis_plugin.sh`)

### Metodo Morgerstern & Price

- **General Limit Equilibrium (GLE)** completo
- Equilibrio momenti + forze
- Funzione distribuzione: `f(x) = sin(πx/L)`
- Superficie circolare ottimizzata su griglia

### Superficie Topografica

Il profilo DEM → **funzione lineare a tratti**:
```python
ground_surface = scipy.interpolate.interp1d(distances, elevations)
```

## Troubleshooting

### Plugin non appare

```bash
# Verifica installazione
ls ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/TheRaiseOfSlopes

# Reinstalla
./install_qgis_plugin.sh
```

### Errore "Moduli non disponibili"

```bash
# Aggiorna moduli
./setup_qgis_plugin.sh

# Verifica
ls qgis_plugin/TheRaiseOfSlopes/le_core/
```

### Analisi fallisce

- ✅ Verifica profilo calcolato
- ✅ Controlla parametri geotecnici ragionevoli
- ✅ Aumenta fattore profondità se necessario
- 📋 Controlla console Python QGIS per errori

## Script di Gestione

### `setup_qgis_plugin.sh`
Copia moduli da `src/limit-equilibrium/` → `le_core/`

### `install_qgis_plugin.sh`  
Prepara + installa plugin in QGIS (tutto in uno)

## Sviluppo

### Modificare il Codice

1. Modifica `the_raise_of_slopes_plugin.py` o altri file
2. Se modifichi `src/limit-equilibrium/`, riesegui:
   ```bash
   ./setup_qgis_plugin.sh
   ```
3. Reinstalla:
   ```bash
   ./install_qgis_plugin.sh
   ```
4. Riavvia QGIS

### Debug

Console Python QGIS: **Plugin → Console Python**

## Crediti

- **Framework GLE**: Leonardo Lalicata, Andrea Bressan (2025)
- **Metodo**: Morgenstern & Price (1965)
- **Plugin QGIS**: Integrazione framework esistente

## File di Supporto

- `INTEGRATION_NOTES.md`: dettagli tecnici integrazione
- `README_OLD.md`: README versione iniziale
- `setup_qgis_plugin.sh`: script preparazione
- `install_qgis_plugin.sh`: script installazione
