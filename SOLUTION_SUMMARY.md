# 🎯 Soluzione: Plugin QGIS Autocontenuto

## Il Problema
Il plugin QGIS dipendeva da moduli in `src/limit-equilibrium/` che non sono disponibili quando il plugin viene copiato nella directory QGIS.

## La Soluzione: Copia dei Moduli

I moduli sono stati **copiati** dentro il plugin in `le_core/`:

```
TheRaiseOfSlopes/
├── le_core/              ← Moduli limit-equilibrium copiati qui
│   ├── __init__.py
│   ├── base_classes.py
│   ├── gle.py
│   ├── circularSlipSurface.py
│   └── ... (tutti i moduli necessari)
└── ... (altri file)
```

## 🚀 Come Usare

### Installazione Rapida

```bash
# Dal directory principale del progetto
./install_qgis_plugin.sh
```

Questo script:
1. ✅ Copia i moduli da `src/limit-equilibrium/` → `le_core/`
2. ✅ Installa il plugin in QGIS
3. ✅ Mostra istruzioni

### Aggiornamento Dopo Modifiche

```bash
# Se modifichi src/limit-equilibrium/
./install_qgis_plugin.sh

# Se modifichi solo il plugin (UI, logica)
./install_qgis_plugin.sh
```

## 📁 File Creati

### Script
- **`setup_qgis_plugin.sh`**: prepara plugin (copia moduli)
- **`install_qgis_plugin.sh`**: installa in QGIS
- **`test_plugin_imports.py`**: verifica import

### Documentazione
- **`QGIS_PLUGIN_MANAGEMENT.md`**: guida completa gestione
- **`qgis_plugin/TheRaiseOfSlopes/README.md`**: manuale utente
- **`qgis_plugin/TheRaiseOfSlopes/INTEGRATION_NOTES.md`**: note tecniche

### Codice
- **`le_core/`**: cartella con moduli copiati
- **`the_raise_of_slopes_plugin.py`**: modificato per usare `from .le_core import ...`

## ✅ Vantaggi

1. **Autocontenuto**: funziona ovunque
2. **Facile installazione**: un solo comando
3. **Distribuibile**: può essere zippato
4. **Standard QGIS**: compatibile con sistema plugin

## ⚠️ Da Ricordare

**Quando modifichi `src/limit-equilibrium/`:**
```bash
./install_qgis_plugin.sh  # Aggiorna e reinstalla
```

I moduli in `le_core/` sono una **copia**, quindi vanno risincronizzati.

## 📦 Distribuzione

```bash
# Prepara
./setup_qgis_plugin.sh

# Zippa
cd qgis_plugin
zip -r TheRaiseOfSlopes.zip TheRaiseOfSlopes/

# Distribuisci TheRaiseOfSlopes.zip
```

## 🔧 Verifica Installazione

```bash
# Controlla che i moduli siano presenti
ls qgis_plugin/TheRaiseOfSlopes/le_core/

# Output atteso:
# __init__.py
# base_classes.py
# bishop.py
# circularSlipSurface.py
# gle.py
# gridComputation.py
# gridOfCircles.py
# slices_data.py
```

## 📍 Directory QGIS

**macOS:**
```
~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
```

**Linux:**
```
~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
```

**Windows:**
```
%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\
```

## 💡 Alternative Considerate (Non Implementate)

### 1. Package Python Installabile
```bash
pip install -e src/limit-equilibrium
```
**Scartata**: troppo complesso per utenti

### 2. Symbolic Link
```bash
ln -s ../../src/limit-equilibrium le_core
```
**Scartata**: non funziona dopo copia, problemi Windows

### 3. Path Manipulation
```python
sys.path.append('../../src/limit-equilibrium')
```
**Scartata**: non funziona quando plugin copiato in QGIS

## 📚 Documentazione Completa

- **`QGIS_PLUGIN_MANAGEMENT.md`**: workflow sviluppo, troubleshooting, best practices
- **`qgis_plugin/TheRaiseOfSlopes/README.md`**: guida utente, installazione, uso
- **`INTEGRATION_NOTES.md`**: dettagli tecnici integrazione GLE

## ✨ Risultato Finale

Il plugin è **completamente autocontenuto** e può essere:
- ✅ Copiato in qualsiasi directory QGIS
- ✅ Distribuito come ZIP
- ✅ Usato senza configurazioni aggiuntive
- ✅ Mantenuto sincronizzato con script automatici

**Il problema è risolto! 🎉**
