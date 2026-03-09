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

"""
 Dataset from:
     Lalicata et al. (2024)    https://doi.org/10.1007/s40999-024-01053-1
     Himansu and Burman (2019) https://doi.org/10.1007/s10706-018-0683-8
"""
options=lemOptions()
ground_surface=lambda x : 0.0*(x<=0.0)+ x*(0.0<x)*(x<=3.0) + 3.0*(x>3.0)



soil=Soil.soilWithVerticalSampling(
          cohesion      =lambda x,y: 10.0*np.ones_like(x+y),
          friction_angle=lambda x,y: 30.0*np.ones_like(x+y),
          pore_pressure =lambda x,y: 0.0*np.ones_like(x+y),
          saturation    =lambda x,y: 0.0*np.ones_like(x+y),
          column_weight =lambda x,y: 18.0*(ground_surface(x)-y),
          num_vertical_sample=1
    )



domain=circularSlipSearchDomain(
    ground_surface=ground_surface,
    in_range=(2.,5.),
    out_range=(-.5,1.),
)


method=lemMethod(bishop,soil,options)
grid_options={
    "in_points":np.array([3.,4.,5.]),
    "out_points":np.array([-.5,0.,.5])}

result,time,calls=grid_simplex(domain=domain,method=method,grid_options=grid_options,num_geometries=1,options={"num_grid_output":3 })
plt.figure(dpi=300)
(geo,lemRes)=result[0]
bounding_box=np.array([[-3,5],[-3,5]])
GeometryPlot(geo,bounding_box=bounding_box).plot(100)
params=domain.getParameters(geo)
print( f'fos={lemRes.factor_of_safety:>7.3f} for in={params[0]:>6.2f}, out={params[1]:>6.2f}, eta={np.degrees(params[2]):.0f}')
print( f'Total time {time:.3f} seconds for {calls} calls')
plt.show()