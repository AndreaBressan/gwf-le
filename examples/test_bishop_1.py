import numpy as np
import time
import sys
sys.path.append("../LEM")
sys.path.append("../searchCriticalF")
from base_classes import SoilProperties,SoilState,UniformQuadrature,Options,np,plt
from circularSlipSurface import circularSlipSurface
from bishop import bishop

geometry=circularSlipSurface.fromInOutAndEta(
    ground_surface=lambda x : 0*(x<=0)+ x*(0<x)*(x<=3) + 3*(x>3),
    bounding_box=np.array([[-5,10],[-5,9]]),
    in_x=5.0,
    out_x=0.0,
    eta=np.radians(70)
    )
fig=geometry.plot(400)
fig.show()
constant_dry_density=18.0
soil_properties=SoilProperties( 
    cohesion       = lambda x,y : 5.0*np.ones_like(x+y),
    friction_angle = lambda x,y : 30.0*np.ones_like(x+y),
    dry_density    = lambda x,y : constant_dry_density*np.ones_like(x+y),
    porosity       = lambda x,y : 0.0*np.ones_like(x+y),
    grain_density  = lambda x,y : 0.0*np.ones_like(x+y)
    )
soil_state=SoilState(
    saturation         = lambda x,y : 1.0*np.ones_like(x+y),
    pore_pressure      = lambda x,y : 0.0*np.ones_like(x+y),
    integrated_density = lambda x,y : constant_dry_density*(geometry.ground_surface(x)-y)
    )

options=Options(
    max_iteration = 200,
    tolerance = 1e-4,
    quadrature = lambda interval : UniformQuadrature(
        x_interval=interval,
        num=50
        ) 
)

res=[]
time_start = time.perf_counter()
res = bishop(geometry,soil_properties,soil_state,options)
time_end = time.perf_counter()
time_duration = time_end - time_start
print(f'Took {time_duration:.3f} seconds')
fig=geometry.plot(400)
plt.savefig("geometry.svg")
print('Safety Factor:', round(res.factor_of_safety,5))