#!/bin/bash
# Script per preparare il plugin QGIS copiando le dipendenze

# Percorsi
PLUGIN_DIR="qgis_plugin/TheRaiseOfSlopes"
LE_SOURCE_DIR="src/limit-equilibrium"
LE_DEST_DIR="$PLUGIN_DIR/le_core"

echo "=== Preparazione Plugin QGIS ==="
echo

# Crea la directory le_core se non esiste
if [ ! -d "$LE_DEST_DIR" ]; then
    echo "Creazione directory $LE_DEST_DIR..."
    mkdir -p "$LE_DEST_DIR"
fi

# Copia i file del framework limit-equilibrium
echo "Copia moduli limit-equilibrium..."
cp "$LE_SOURCE_DIR/base_classes.py" "$LE_DEST_DIR/"
cp "$LE_SOURCE_DIR/bishop.py" "$LE_DEST_DIR/"
cp "$LE_SOURCE_DIR/circularSlipSurface.py" "$LE_DEST_DIR/"
cp "$LE_SOURCE_DIR/gle.py" "$LE_DEST_DIR/"
cp "$LE_SOURCE_DIR/gridComputation.py" "$LE_DEST_DIR/"
cp "$LE_SOURCE_DIR/gridOfCircles.py" "$LE_DEST_DIR/"
cp "$LE_SOURCE_DIR/slices_data.py" "$LE_DEST_DIR/"
cp "$LE_SOURCE_DIR/quadrature.py" "$LE_DEST_DIR/"
cp "$LE_SOURCE_DIR/gridSimplexComputation.py" "$LE_DEST_DIR/"

# Crea __init__.py se non esiste
if [ ! -f "$LE_DEST_DIR/__init__.py" ]; then
    echo "Creazione $LE_DEST_DIR/__init__.py..."
    cat > "$LE_DEST_DIR/__init__.py" << 'EOF'
# -*- coding: utf-8 -*-
"""
Moduli del framework Limit Equilibrium integrati nel plugin QGIS.
Questi file sono copie dei moduli in src/limit-equilibrium/
"""

from .base_classes import (
    Geometry,
    SoilProperties,
    SoilState,
    Quadrature,
    UniformQuadrature,
    Options,
    Result
)
from .circularSlipSurface import circularSlipSurface
from .bishop import bishop
from .gle import morgerstern_price, spencer
from .gridOfCircles import GridOptions, gridComputation, computeEtaMinForSurface

__all__ = [
    'Geometry',
    'SoilProperties',
    'SoilState',
    'Quadrature',
    'UniformQuadrature',
    'Options',
    'Result',
    'circularSlipSurface',
    'bishop',
    'morgerstern_price',
    'spencer',
    'GridOptions',
    'gridComputation',
    'computeEtaMinForSurface'
]
EOF
fi

echo
echo "✓ Moduli copiati con successo in $LE_DEST_DIR"
echo
echo "Il plugin è ora autocontenuto e può essere copiato in:"
echo "  - macOS: ~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/"
echo "  - Linux: ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/"
echo "  - Windows: %APPDATA%\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"
echo
echo "Comando per copiare il plugin:"
echo "  cp -r $PLUGIN_DIR \"\$QGIS_PLUGINS_DIR/\""
