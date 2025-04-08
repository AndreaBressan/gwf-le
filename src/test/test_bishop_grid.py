import numpy as np
import time
import sys
sys.path.append("../limit-equilibrium")
from base_classes import SoilProperties,SoilState,UniformQuadrature,Options,np,plt
from circularSlipSurface import circularSlipSurface
from bishop import bishop
from gridOfCircles import gridOfCircles

ground_surface=lambda x : 0*(x<=0)+ x*(0<x)*(x<=3) + 3*(x>3)
bounding_box=np.array([[-5,10],[-5,9]])
in_interval=[3,10]
out_interval=[-5,1]
min_eta_inc=np.radians(5)
num_in_pts=10
num_out_pts=10

time_start = time.perf_counter()
geometries=gridOfCircles(ground_surface, bounding_box, in_interval,out_interval,min_eta_inc,num_in_pts,num_out_pts)
time_duration = time.perf_counter()- time_start
print(f'Grid construction took {time_duration:.3f} seconds')


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
    integrated_density = lambda x,y : constant_dry_density*(ground_surface(x)-y)
    )
options=Options(
    max_iteration = 200,
    tolerance = 1e-4
    )

time_start = time.perf_counter()
result=[bishop(geometry,soil_properties,soil_state,UniformQuadrature(x_interval=geometry.landslide_interval,num=30),options) for geometry in geometries]
time_duration = time.perf_counter()- time_start
print(f'Bishop computation took {time_duration:.3f} seconds')

result.sort(key=lambda x: x.factor_of_safety)
fig=result[0].inputs[0].plot(400)
plt.savefig("worst_grid.svg")
print(result[0].factor_of_safety, result[-1].factor_of_safety)