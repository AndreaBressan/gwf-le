# 🚀 Quick Start - Plugin QGIS

## Installazione in 1 Comando

```bash
./install_qgis_plugin.sh
```

Poi in QGIS: **Plugin → Gestisci plugin → Abilita "The Raise Of Slopes"**

---

## Uso in 3 Passi

### 1️⃣ Calcola Profilo
1. Carica DEM in QGIS
2. Plugin → The Raise Of Slopes
3. Seleziona 2 punti sul DEM
4. "Calcola profilo"

### 2️⃣ Imposta Parametri
1. Scheda "Analisi di Stabilità"
2. Imposta:
   - γ (peso specifico): 18-22 kN/m³
   - c (coesione): 0-50 kPa
   - φ (attrito): 20-40°

### 3️⃣ Analizza
1. "Esegui Analisi di Stabilità"
2. Visualizza FS e superficie critica

---

## Aggiornamento

```bash
./install_qgis_plugin.sh  # Aggiorna tutto
```

---

## Struttura Plugin

```
TheRaiseOfSlopes/
├── le_core/              ← Framework GLE (autocontenuto)
├── the_raise_of_slopes_plugin.py
├── ui/
└── tools/
```

---

## Documentazione

- **README.md**: guida completa
- **QGIS_PLUGIN_MANAGEMENT.md**: gestione e sviluppo
- **SOLUTION_SUMMARY.md**: soluzione problema dipendenze

---

## Supporto

Problema? Controlla:
1. `ls qgis_plugin/TheRaiseOfSlopes/le_core/` - moduli presenti?
2. Riavvia QGIS
3. Console Python QGIS per errori

---

**Il plugin è autocontenuto e pronto all'uso! ✨**
