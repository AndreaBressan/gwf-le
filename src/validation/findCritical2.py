import numpy as np
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.LEM.lemInterface import *
from src.LEM.geometryPlot import *
from src.LEM.gleMethods import *
from src.LEM.circularSlipSurfaces import *
from src.LEM.searchInterface import *

options=lemOptions()
ground_surface=lambda x : 0.0*(x<=0.0)+ x*(0.0<x)*(x<=3.0) + 3.0*(x>3.0)


soil=Soil(cohesion=lambda x,y: 5.0*np.ones_like(x+y),
          vertical_cohesion=lambda x,y: 5.0*np.ones_like(x+y),
          friction_angle=lambda x,y: 30.0*np.ones_like(x+y),
          vertical_friction_angle=lambda x,y: 5.0*np.ones_like(x+y),
          pore_pressure=lambda x,y: 0.0*np.ones_like(x+y),
          saturation=lambda x,y: 0.0*np.ones_like(x+y),
          column_weight=lambda x,y: 18.0*(ground_surface(x)-y))


domain=circularSlipSearchDomain(
    ground_surface=ground_surface,
    in_range=(2.,5.),
    out_range=(-.5,1.),
)

method=lemMethod(bishop,soil,options)
gridOptions={
    "in_points":np.array([3.,4.,5.]),
    "out_points":np.array([-.5,0.,.5])}
grid=domain.sample_grid(gridOptions)
result,time=find_critical  (method,grid ,num_geometries=10 )

bounding_box=np.array([[-3,5],[-3,5]])


startGeos=[r[0] for r in result]
result2,time2,calls=simplex(domain,method,startGeos,10)


def makeFigure(result,bounding_box,time, tot_geo):
    plt.figure()
    (geo,lemRes)=result[0]
    GeometryPlot(geo,bounding_box=bounding_box).plotTerrain(100)
    for r in result:
        (geo,lemRes)=r
        GeometryPlot(geo,bounding_box=bounding_box).plotSlipSurface(num_points=100)
        params=domain.getParameters(geo)
        print( f'fos={lemRes.factor_of_safety:>7.3f} for in={params[0]:>6.2f}, out={params[1]:>6.2f}, eta={np.degrees(params[2]):.0f}')
    print(f'Total time {time:.3f} seconds for {tot_geo} geometries')


makeFigure(result,bounding_box,time,len(grid))
makeFigure(result2,bounding_box,time2,calls)

plt.show()
