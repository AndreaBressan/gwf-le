# 🔧 Risoluzione Problemi Import in QGIS

## Problema: "Moduli limit-equilibrium non disponibili"

### Causa 1: Import Relativi non Funzionanti

**Sintomo**: Errore anche se `le_core/` esiste

**Soluzione Implementata**: Doppio tentativo di import
```python
try:
    # Import relativi (preferito)
    from .le_core.base_classes import SoilProperties
except ImportError:
    # Fallback: import assoluti con sys.path
    from base_classes import SoilProperties
```

### Causa 2: Matplotlib Non Disponibile

**Sintomo**: Errore `ModuleNotFoundError: No module named 'matplotlib'`

**Soluzione Implementata**: Import opzionale di matplotlib
```python
# In base_classes.py
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
```

I metodi `plot()` ora verificano `MATPLOTLIB_AVAILABLE` prima di usare plt.

## Modifiche Applicate

### 1. `the_raise_of_slopes_plugin.py`

✅ Aggiunto path esplicito a `le_core/`
```python
le_core_path = os.path.join(plugin_dir, 'le_core')
sys.path.insert(0, le_core_path)
```

✅ Doppio tentativo di import (relativo + assoluto)

✅ Debug logging migliorato per diagnostica

### 2. `le_core/base_classes.py`

✅ Import opzionale di matplotlib

✅ Check `MATPLOTLIB_AVAILABLE` nei metodi plot

✅ Errori espliciti se plot chiamato senza matplotlib

## Testing in QGIS

### 1. Verifica Import

Nella **Console Python di QGIS**:

```python
import sys
import os

# Verifica percorso plugin
plugin_path = os.path.join(
    os.path.expanduser('~'),
    'Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/TheRaiseOfSlopes'
)
print(f"Plugin path: {plugin_path}")
print(f"Esiste? {os.path.exists(plugin_path)}")

# Verifica le_core
le_core_path = os.path.join(plugin_path, 'le_core')
print(f"\nle_core path: {le_core_path}")
print(f"Esiste? {os.path.exists(le_core_path)}")

if os.path.exists(le_core_path):
    print(f"File in le_core: {os.listdir(le_core_path)}")

# Tenta import
sys.path.insert(0, le_core_path)
try:
    from base_classes import SoilProperties
    print("\n✓ Import base_classes OK!")
except Exception as e:
    print(f"\n✗ Errore import: {e}")
```

### 2. Verifica Plugin Caricato

```python
# Nella Console Python QGIS
from qgis.utils import plugins

if 'TheRaiseOfSlopes' in plugins:
    plugin = plugins['TheRaiseOfSlopes']
    print("✓ Plugin caricato")
    print(f"LIMIT_EQUILIBRIUM_AVAILABLE: {plugin.LIMIT_EQUILIBRIUM_AVAILABLE}")
else:
    print("✗ Plugin non caricato")
```

## Diagnosi Errori

### Errore: "No module named 'le_core'"

**Verifica**:
```bash
ls ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/TheRaiseOfSlopes/le_core/
```

**Soluzione**: Reinstalla
```bash
./install_qgis_plugin.sh
```

### Errore: "No module named 'matplotlib'"

**Situazione**: Normale in alcuni ambienti QGIS

**Soluzione**: Il plugin ora gestisce questo caso - matplotlib è opzionale. I calcoli funzioneranno comunque, solo i metodi `plot()` non saranno disponibili (non usati dal plugin).

### Errore: "cannot import name 'SoilProperties'"

**Verifica**:
```bash
cat ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/TheRaiseOfSlopes/le_core/base_classes.py | head -20
```

**Soluzione**: File corrotto, reinstalla
```bash
./install_qgis_plugin.sh
```

## Checklist Troubleshooting

Quando il plugin non funziona:

- [ ] **Verifica `le_core/` esiste**
  ```bash
  ls ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/TheRaiseOfSlopes/le_core/
  ```

- [ ] **Verifica 8 file Python in `le_core/`**
  - `__init__.py`
  - `base_classes.py`
  - `bishop.py`
  - `circularSlipSurface.py`
  - `gle.py`
  - `gridComputation.py`
  - `gridOfCircles.py`
  - `slices_data.py`

- [ ] **Reinstalla plugin**
  ```bash
  ./install_qgis_plugin.sh
  ```

- [ ] **Riavvia QGIS completamente**

- [ ] **Controlla Console Python QGIS** per errori

- [ ] **Riabilita plugin** in Gestione Plugin

## Log Debug

Per debug avanzato, aggiungi all'inizio di `the_raise_of_slopes_plugin.py`:

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - TheRaiseOfSlopes - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

Poi usa:
```python
logger.debug(f"Tentativo import da: {le_core_path}")
```

## Compatibilità Versioni

### QGIS 3.x
✅ Testato e funzionante

### Python
- ✅ Python 3.9+
- ⚠️ Python 3.6-3.8 (non testato ma dovrebbe funzionare)

### Dipendenze
- ✅ NumPy: richiesto
- ✅ SciPy: richiesto
- ⚠️ Matplotlib: opzionale (gestito gracefully)

## Ambiente QGIS

Per verificare l'ambiente Python di QGIS:

```python
# Console Python QGIS
import sys
print(f"Python: {sys.version}")
print(f"Executable: {sys.executable}")

import numpy as np
print(f"NumPy: {np.__version__}")

import scipy
print(f"SciPy: {scipy.__version__}")

try:
    import matplotlib
    print(f"Matplotlib: {matplotlib.__version__}")
except ImportError:
    print("Matplotlib: NON DISPONIBILE (OK, è opzionale)")
```

## Fix Applicati nella Versione Corrente

| Problema | Fix | File |
|----------|-----|------|
| Import relativi falliscono | Doppio tentativo import | `the_raise_of_slopes_plugin.py` |
| Matplotlib non trovato | Import opzionale | `le_core/base_classes.py` |
| Path non trovato | Aggiunto sys.path esplicito | `the_raise_of_slopes_plugin.py` |
| Debug insufficiente | Logging esteso | `the_raise_of_slopes_plugin.py` |

## Reinstallazione Pulita

Se tutti i fix falliscono:

```bash
# 1. Rimuovi completamente
rm -rf ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/TheRaiseOfSlopes

# 2. Pulisci le_core locale
rm -rf qgis_plugin/TheRaiseOfSlopes/le_core

# 3. Reinstalla da zero
./install_qgis_plugin.sh

# 4. Riavvia QGIS
# 5. Riabilita plugin
```

## Contatti

Per ulteriore supporto, fornire:
1. Output della Console Python QGIS
2. Risultato del test di verifica import (sopra)
3. Versione QGIS (`Help → About`)
4. Sistema operativo e versione
