import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.LEM.lemInterface import *
from src.LEM.geometryPlot import *
from src.LEM.gleMethods import *
from src.searchCriticalF.circularSlipSurfaces import *

options=lemOptions()
ground_surface=lambda x : 0.0*(x<=0.0)+ x*(0.0<x)*(x<=3.0) + 3.0*(x>3.0)
geometry=circularArc.fromInOutAndEta(ground_surface, 4.0, 0.0, np.radians(70))

soil=Soil(cohesion=lambda x,y: 5.0*np.ones_like(x+y),
          vertical_cohesion=lambda x,y: 5.0*np.ones_like(x+y),
          friction_angle=lambda x,y: 30.0*np.ones_like(x+y),
          vertical_friction_angle=lambda x,y: 5.0*np.ones_like(x+y),
          pore_pressure=lambda x,y: 0.0*np.ones_like(x+y),
          saturation=lambda x,y: 0.0*np.ones_like(x+y),
          column_weight=lambda x,y: 18.0*(ground_surface(x)-y))


methods=["fellenius","bishop","spencer","morgerstern_price"]
results=[fellenius(geometry,soil,options),
    bishop(geometry,soil,options),
    spencer(geometry,soil,options),
    morgerstern_price(geometry,soil,options)]

for (name,out) in zip(methods,results):
    print(name, f'{out.factor_of_safety:.3f} with Lambda {out.Lambda:.3f}')

