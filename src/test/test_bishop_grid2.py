import numpy as np
import sys
sys.path.append("../limit-equilibrium")
from base_classes import SoilProperties,SoilState,UniformQuadrature,Options,np,plt
from bishop import bishop
from gridOfCircles import GridOptions, gridComputation

ground_surface=lambda x : 0*(x<=0)+ x*(0<x)*(x<=3) + 3*(x>3)
bounding_box=np.array([[-5,10],[-5,9]])
gOptions=GridOptions(in_interval=[3,6],out_interval=None,min_eta_inc=np.radians(5),num_in_pts=3,num_out_pts=None, out_pts=[-3,-1.5,0,0.1875,0.75])

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
mOptions=Options(
    max_iteration = 200,
    tolerance = 1e-4,
    quadrature = lambda interval : UniformQuadrature(
        x_interval=interval,
        num=50 # uncomment to change the number of slices
        ) 
    )

[result,time_duration]=gridComputation(bishop, ground_surface,bounding_box,soil_properties,soil_state,gOptions,mOptions)

print(f'Bishop computation took {time_duration:.3f} seconds')
print(f'The grid contains {len(result):d} points')

fig=result[0].inputs[0].plot(400,dpc=240,x_cm=10)
for j in range(1,5):
    result[j].inputs[0].plotSlipSurface(400)

plt.savefig("worst_grid.svg")
print(result[0].factor_of_safety, result[-1].factor_of_safety)


F = np.array([a.factor_of_safety for a in result])
geom=[[a.inputs[0].in_pt[0], a.inputs[0].out_pt[0], np.degrees(a.inputs[0].eta)] for a in result]
"""
bisogna associare a ogni F il cerchio corrispondente (x_in , x_out, eta)
"""