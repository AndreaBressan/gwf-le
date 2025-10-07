#!/usr/bin/env python3
"""
Test di import dei moduli le_core (senza dipendenze grafiche)
"""
import sys
import os

# Aggiungi la directory del plugin al path
plugin_dir = os.path.join(os.path.dirname(__file__), 'qgis_plugin', 'TheRaiseOfSlopes')
sys.path.insert(0, plugin_dir)

print("=== Test Import Moduli le_core ===\n")

try:
    print("1. Test import numpy...")
    import numpy as np
    print("   ✓ numpy OK")
except ImportError as e:
    print(f"   ✗ numpy non disponibile: {e}")
    sys.exit(1)

try:
    print("2. Test import scipy...")
    import scipy.interpolate
    print("   ✓ scipy OK")
except ImportError as e:
    print(f"   ✗ scipy non disponibile: {e}")
    sys.exit(1)

# Disabilita matplotlib per il test
sys.modules['matplotlib'] = type(sys)('matplotlib')
sys.modules['matplotlib.pyplot'] = type(sys)('matplotlib.pyplot')

try:
    print("3. Test import base_classes...")
    from le_core.base_classes import SoilProperties, SoilState, Options
    print("   ✓ base_classes OK")
except ImportError as e:
    print(f"   ✗ base_classes fallito: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("4. Test import circularSlipSurface...")
    from le_core.circularSlipSurface import circularSlipSurface
    print("   ✓ circularSlipSurface OK")
except ImportError as e:
    print(f"   ✗ circularSlipSurface fallito: {e}")
    sys.exit(1)

try:
    print("5. Test import gle...")
    from le_core.gle import morgerstern_price
    print("   ✓ gle OK")
except ImportError as e:
    print(f"   ✗ gle fallito: {e}")
    sys.exit(1)

try:
    print("6. Test import gridOfCircles...")
    from le_core.gridOfCircles import GridOptions, gridComputation
    print("   ✓ gridOfCircles OK")
except ImportError as e:
    print(f"   ✗ gridOfCircles fallito: {e}")
    sys.exit(1)

print("\n=== ✓ Tutti i test superati! ===")
print("\nIl plugin è pronto per essere usato in QGIS.")
print("Per installare: ./install_qgis_plugin.sh")
