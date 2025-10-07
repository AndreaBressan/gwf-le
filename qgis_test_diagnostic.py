"""
Script di Test per Plugin TheRaiseOfSlopes in QGIS
Copia e incolla questo codice nella Console Python di QGIS per diagnosticare problemi
"""

import sys
import os

print("="*60)
print("TEST DIAGNOSTICO - TheRaiseOfSlopes Plugin")
print("="*60)

# 1. Verifica percorso plugin
plugin_base = os.path.join(
    os.path.expanduser('~'),
    'Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins'
)
plugin_path = os.path.join(plugin_base, 'TheRaiseOfSlopes')

print(f"\n1. PERCORSO PLUGIN")
print(f"   Directory base: {plugin_base}")
print(f"   Plugin path: {plugin_path}")
print(f"   Esiste? {os.path.exists(plugin_path)}")

if not os.path.exists(plugin_path):
    print("\n❌ ERRORE: Directory plugin non trovata!")
    print("   Eseguire: ./install_qgis_plugin.sh")
else:
    print("   ✓ Directory plugin trovata")

# 2. Verifica le_core
le_core_path = os.path.join(plugin_path, 'le_core')
print(f"\n2. MODULI LE_CORE")
print(f"   Path: {le_core_path}")
print(f"   Esiste? {os.path.exists(le_core_path)}")

if os.path.exists(le_core_path):
    files = sorted([f for f in os.listdir(le_core_path) if f.endswith('.py')])
    print(f"   File Python ({len(files)}):")
    for f in files:
        print(f"      - {f}")
    
    required = ['__init__.py', 'base_classes.py', 'gle.py', 
                'circularSlipSurface.py', 'gridOfCircles.py']
    missing = [f for f in required if f not in files]
    if missing:
        print(f"\n   ⚠️ File mancanti: {missing}")
    else:
        print("   ✓ Tutti i file richiesti presenti")
else:
    print("\n❌ ERRORE: Directory le_core non trovata!")
    print("   Eseguire: ./install_qgis_plugin.sh")

# 3. Test import
print(f"\n3. TEST IMPORT")

# Aggiungi path
if le_core_path not in sys.path:
    sys.path.insert(0, le_core_path)
    print(f"   Path aggiunto a sys.path")

# Tenta import
modules_to_test = [
    ('base_classes', ['SoilProperties', 'SoilState', 'Options']),
    ('gle', ['morgerstern_price']),
    ('circularSlipSurface', ['circularSlipSurface']),
    ('gridOfCircles', ['GridOptions', 'gridComputation'])
]

all_ok = True
for module_name, symbols in modules_to_test:
    try:
        module = __import__(module_name)
        missing_symbols = [s for s in symbols if not hasattr(module, s)]
        if missing_symbols:
            print(f"   ⚠️ {module_name}: importato ma mancano {missing_symbols}")
            all_ok = False
        else:
            print(f"   ✓ {module_name}: OK")
    except ImportError as e:
        print(f"   ✗ {module_name}: ERRORE - {e}")
        all_ok = False
    except Exception as e:
        print(f"   ✗ {module_name}: ERRORE GENERICO - {e}")
        all_ok = False

# 4. Verifica dipendenze
print(f"\n4. DIPENDENZE")
dependencies = {
    'numpy': True,
    'scipy': True,
    'matplotlib': False  # Opzionale
}

for dep, required in dependencies.items():
    try:
        mod = __import__(dep)
        version = getattr(mod, '__version__', 'unknown')
        print(f"   ✓ {dep}: {version}")
    except ImportError:
        if required:
            print(f"   ✗ {dep}: MANCANTE (RICHIESTO)")
            all_ok = False
        else:
            print(f"   ⚠️ {dep}: MANCANTE (opzionale)")

# 5. Verifica plugin caricato
print(f"\n5. STATO PLUGIN IN QGIS")
try:
    from qgis.utils import plugins
    if 'TheRaiseOfSlopes' in plugins:
        plugin = plugins['TheRaiseOfSlopes']
        print(f"   ✓ Plugin caricato in QGIS")
        if hasattr(plugin, 'LIMIT_EQUILIBRIUM_AVAILABLE'):
            print(f"   LIMIT_EQUILIBRIUM_AVAILABLE: {plugin.LIMIT_EQUILIBRIUM_AVAILABLE}")
        else:
            print(f"   ⚠️ Attributo LIMIT_EQUILIBRIUM_AVAILABLE non trovato")
    else:
        print(f"   ⚠️ Plugin non caricato (normale se non ancora abilitato)")
except Exception as e:
    print(f"   ℹ️ Impossibile verificare stato plugin: {e}")

# 6. Ambiente Python
print(f"\n6. AMBIENTE PYTHON")
print(f"   Versione: {sys.version.split()[0]}")
print(f"   Executable: {sys.executable}")
print(f"   Platform: {sys.platform}")

# Risultato finale
print("\n" + "="*60)
if all_ok and os.path.exists(le_core_path):
    print("✓ TUTTI I TEST SUPERATI!")
    print("Il plugin dovrebbe funzionare correttamente.")
    print("\nSe vedi ancora errori:")
    print("1. Riavvia QGIS completamente")
    print("2. Riabilita il plugin in Gestione Plugin")
else:
    print("✗ ALCUNI TEST FALLITI")
    print("\nSoluzione:")
    print("1. Nel terminale, esegui: ./install_qgis_plugin.sh")
    print("2. Riavvia QGIS")
    print("3. Abilita il plugin in Gestione Plugin")
    print("4. Riesegui questo test")
print("="*60)
