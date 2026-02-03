import numpy as np
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


from time import perf_counter as time

methods={
    "fellenius":        fellenius,
    "bishop":           bishop,
    "spencer":          spencer,
    "morgerstern_price":morgerstern_price}

# There is a strange effect for which the time of bishop method is exaggerated, probably python interpreter stuff
results=dict()
t2=time()
for name in methods:
    t1 = time()
    results[name]=methods[name](geometry,soil,options)
    print(f'{name:20} {results[name].factor_of_safety:.3f} with Lambda{f'{results[name].Lambda:>.3f}':>6}, in {time()-t1:.3f} seconds')
print(f'total time {time()-t2:.3f}')
