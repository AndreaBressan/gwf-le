# Gestione Plugin QGIS - The Raise Of Slopes

## Problema Risolto

Il plugin QGIS necessita di essere **autocontenuto** nella sua cartella quando viene installato in QGIS, ma dipendeva da moduli in `src/limit-equilibrium/` che non sarebbero disponibili dopo la copia.

## Soluzione Implementata

### Approccio: Duplicazione Moduli

I moduli del framework `limit-equilibrium` vengono **copiati** all'interno del plugin in una sottocartella dedicata:

```
qgis_plugin/TheRaiseOfSlopes/
├── le_core/                    # ← Moduli copiati qui
│   ├── __init__.py
│   ├── base_classes.py
│   ├── bishop.py
│   ├── circularSlipSurface.py
│   ├── gle.py
│   ├── gridComputation.py
│   ├── gridOfCircles.py
│   └── slices_data.py
└── ... (altri file del plugin)
```

### Script di Gestione

#### 1. `setup_qgis_plugin.sh` - Preparazione

```bash
./setup_qgis_plugin.sh
```

**Cosa fa:**
- Crea la directory `le_core/` nel plugin
- Copia tutti i file da `src/limit-equilibrium/`
- Crea `__init__.py` con exports appropriati
- Rende il plugin autocontenuto

**Quando usarlo:**
- Prima installazione
- Dopo modifiche a `src/limit-equilibrium/`
- Per aggiornare i moduli nel plugin

#### 2. `install_qgis_plugin.sh` - Installazione Completa

```bash
./install_qgis_plugin.sh
```

**Cosa fa:**
- Esegue `setup_qgis_plugin.sh` automaticamente
- Rimuove installazione precedente (se presente)
- Copia il plugin nella directory QGIS
- Mostra istruzioni per abilitarlo

**Quando usarlo:**
- Installazione iniziale in QGIS
- Aggiornamento completo del plugin
- Testing dopo modifiche

## Workflow di Sviluppo

### Scenario 1: Modifica al Plugin (solo UI/logica)

```bash
# 1. Modifica file plugin (es. the_raise_of_slopes_plugin.py)
nano qgis_plugin/TheRaiseOfSlopes/the_raise_of_slopes_plugin.py

# 2. Reinstalla
./install_qgis_plugin.sh

# 3. Riavvia QGIS
```

### Scenario 2: Modifica ai Moduli Limit-Equilibrium

```bash
# 1. Modifica moduli
nano src/limit-equilibrium/gle.py

# 2. Aggiorna e installa (tutto in uno)
./install_qgis_plugin.sh

# 3. Riavvia QGIS
```

### Scenario 3: Solo Preparazione (senza installare)

```bash
# Prepara il plugin per distribuzione
./setup_qgis_plugin.sh

# Ora la cartella qgis_plugin/TheRaiseOfSlopes/ è pronta
# per essere zippata o copiata manualmente
```

## Import nel Codice

### ✅ Nuovo (Autocontenuto)

```python
from .le_core.base_classes import SoilProperties, SoilState
from .le_core.gle import morgerstern_price
from .le_core.gridOfCircles import GridOptions, gridComputation
```

### ❌ Vecchio (Dipendenza esterna)

```python
# NON FUNZIONA quando copiato in QGIS
sys.path.append('../../src/limit-equilibrium')
from base_classes import SoilProperties
```

## Struttura Completa Progetto

```
gwf-le/
├── src/
│   └── limit-equilibrium/        # Sorgente originale
│       ├── base_classes.py
│       ├── gle.py
│       └── ...
│
├── qgis_plugin/
│   └── TheRaiseOfSlopes/         # Plugin QGIS
│       ├── le_core/              # Copia dei moduli ← automatica
│       │   ├── base_classes.py
│       │   ├── gle.py
│       │   └── ...
│       ├── the_raise_of_slopes_plugin.py
│       └── ...
│
├── setup_qgis_plugin.sh          # Script preparazione
├── install_qgis_plugin.sh        # Script installazione
└── README.md
```

## Distribuzione del Plugin

### Per Utenti Finali

1. **Esegui setup**:
   ```bash
   ./setup_qgis_plugin.sh
   ```

2. **Zippa la cartella**:
   ```bash
   cd qgis_plugin
   zip -r TheRaiseOfSlopes.zip TheRaiseOfSlopes/
   ```

3. **Distribuisci** `TheRaiseOfSlopes.zip`

4. **Installazione utente**:
   - Decomprimi in cartella plugin QGIS
   - Abilita da Gestione Plugin

### Per Repository QGIS Official Plugin

1. Prepara plugin: `./setup_qgis_plugin.sh`
2. Verifica `metadata.txt`
3. Crea repository seguendo [QGIS Plugin Guidelines](https://plugins.qgis.org/)

## Directory Plugin QGIS per Piattaforma

### macOS
```
~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
```

### Linux
```
~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
```

### Windows
```
%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\
```

## Vantaggi e Svantaggi

### ✅ Vantaggi

- **Autocontenuto**: funziona ovunque
- **Facile installazione**: nessuna configurazione path
- **Distribuibile**: può essere zippato e condiviso
- **Compatibile**: con sistema plugin QGIS standard

### ⚠️ Svantaggi

- **Codice duplicato**: esistono due copie dei moduli
- **Sincronizzazione manuale**: serve script per aggiornare
- **Spazio disco**: duplicazione file (minimo, ~100KB)

### Alternativa Non Implementata: Package Python

Si potrebbe creare un package installabile:
```bash
pip install -e src/limit-equilibrium
```

**Pro**: codice centralizzato  
**Contro**: complesso per utenti, richiede configurazione ambiente QGIS

## Troubleshooting

### Script non eseguibili

```bash
chmod +x setup_qgis_plugin.sh install_qgis_plugin.sh
```

### Directory QGIS non trovata

Modifica `install_qgis_plugin.sh` con il path corretto del tuo profilo QGIS.

### Moduli non aggiornati

```bash
# Forza aggiornamento
rm -rf qgis_plugin/TheRaiseOfSlopes/le_core
./setup_qgis_plugin.sh
```

### Test senza installare in QGIS

```python
# Da terminale Python nell'ambiente di sviluppo
cd qgis_plugin/TheRaiseOfSlopes
python -c "from le_core import morgerstern_price; print('OK')"
```

## Manutenzione

### Checklist Aggiornamento Moduli

- [ ] Modifica in `src/limit-equilibrium/`
- [ ] Esegui `./setup_qgis_plugin.sh`
- [ ] Verifica import: `python -c "from le_core import *"`
- [ ] Testa in QGIS: `./install_qgis_plugin.sh`
- [ ] Verifica funzionalità plugin
- [ ] Commit changes (incluso `le_core/`)

### Changelog

Mantieni un changelog in `qgis_plugin/TheRaiseOfSlopes/CHANGELOG.md` per tracciare:
- Versione plugin
- Data aggiornamento moduli `le_core/`
- Modifiche API se presenti

## Best Practices

1. **Sempre** eseguire `setup_qgis_plugin.sh` prima di distribuire
2. **Mai** modificare direttamente file in `le_core/` (modificare sorgente in `src/`)
3. **Testare** in QGIS dopo ogni aggiornamento importante
4. **Documentare** modifiche al framework che impattano il plugin
5. **Versionare** `le_core/` nel repository per tracciare allineamento

## Note Tecniche

### Import Relativi

Il plugin usa import relativi per `le_core`:
```python
from .le_core.gle import morgerstern_price  # Relativo al package plugin
```

### Namespace Package

`le_core/__init__.py` esporta tutti i simboli necessari per import puliti:
```python
from .le_core import SoilProperties  # Invece di .base_classes
```

### Compatibilità

I moduli in `le_core/` sono identici a quelli in `src/limit-equilibrium/`, quindi:
- Stesso comportamento
- Stessi risultati numerici
- Compatibilità test esistenti
