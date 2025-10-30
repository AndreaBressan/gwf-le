#!/bin/bash
# Script per installare il plugin in QGIS (macOS)

PLUGIN_NAME="TheRaiseOfSlopes"
SOURCE_DIR="qgis_plugin/$PLUGIN_NAME"

# Directory dei plugin QGIS su macOS
QGIS_PLUGINS_DIR="$HOME/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins"

# Controlla se la directory esiste
if [ ! -d "$QGIS_PLUGINS_DIR" ]; then
    echo "❌ Directory dei plugin QGIS non trovata: $QGIS_PLUGINS_DIR"
    echo
    echo "Percorsi alternativi da verificare:"
    echo "  - $HOME/Library/Application Support/QGIS/QGIS3/profiles/[PROFILE_NAME]/python/plugins/"
    exit 1
fi

echo "=== Installazione Plugin QGIS ==="
echo

# Prima assicuriamoci che i moduli siano aggiornati
echo "1. Aggiornamento moduli limit-equilibrium..."
#./setup_qgis_plugin.sh
echo

# Rimuovi installazione precedente se esiste
if [ -d "$QGIS_PLUGINS_DIR/$PLUGIN_NAME" ]; then
    echo "2. Rimozione installazione precedente..."
    rm -rf "$QGIS_PLUGINS_DIR/$PLUGIN_NAME"
fi

# Copia il plugin
echo "3. Copia plugin in QGIS..."
cp -r "$SOURCE_DIR" "$QGIS_PLUGINS_DIR/"

if [ $? -eq 0 ]; then
    echo
    echo "✓ Plugin installato con successo!"
    echo
    echo "Percorso: $QGIS_PLUGINS_DIR/$PLUGIN_NAME"
    echo
    echo "Prossimi passi:"
    echo "  1. Apri/Riavvia QGIS"
    echo "  2. Menu: Plugin → Gestisci e installa plugin"
    echo "  3. Scheda: Installati"
    echo "  4. Abilita: $PLUGIN_NAME"
    echo
else
    echo
    echo "❌ Errore durante l'installazione"
    exit 1
fi
