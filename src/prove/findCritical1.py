import numpy as np
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.LEM.lemInterface import *
from src.LEM.geometryPlot import *
from src.LEM.gleMethods import *
from src.searchCriticalF.circularSlipSurfaces import *
from src.searchCriticalF.searchInterface import *

options=lemOptions()
ground_surface=lambda x : 0.0*(x<=0.0)+ x*(0.0<x)*(x<=3.0) + 3.0*(x>3.0)


soil=Soil(cohesion=lambda x,y: 5.0*np.ones_like(x+y),
          vertical_cohesion=lambda x,y: 5.0*np.ones_like(x+y),
          friction_angle=lambda x,y: 30.0*np.ones_like(x+y),
          vertical_friction_angle=lambda x,y: 5.0*np.ones_like(x+y),
          pore_pressure=lambda x,y: 0.0*np.ones_like(x+y),
          saturation=lambda x,y: 0.0*np.ones_like(x+y),
          column_weight=lambda x,y: 18.0*(ground_surface(x)-y))


searchDomain=circularSlipSearchDomain(
    ground_surface=ground_surface,
    in_range=(2.,5.),
    out_range=(-.5,1.)
)

method=lemMethod(bishop,soil,options)
gridOptions={"num_in_points":5,"num_out_points":5}
result,time=find_critical  (method, searchDomain.sample_grid(gridOptions),num_geometries=10 )

bounding_box=np.array([[-3,5],[-3,5]])
(geo,lemRes)=result[0]
pltGeo=GeometryPlot(geo,bounding_box=bounding_box).plotTerrain(100)
for r in result:
    (geo,lemRes)=r
    pltGeo=GeometryPlot(geo,bounding_box=bounding_box).plotSlipSurface(num_points=100)
    params=searchDomain.getParameters(geo)
    print( f'fos={lemRes.factor_of_safety:>7.3f} for in={params[0]:>6.2f}, out={params[1]:>6.2f}, eta={np.degrees(params[2]):.0f}')

print(f'Total time {time:.3f} seconds for {len(result)} geometries')
plt.show()
plt.close()