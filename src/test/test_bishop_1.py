import numpy as np
import sys
sys.path.append("../limit-equilibrium")
from base_classes import SoilProperties,SoilState,UniformQuadrature,Options,np,plt
from circularSlipSurface import circularSplipSurface
from bishop import bishop

geometry=circularSplipSurface.fromInOutAndEta(
    ground_surface=lambda x : 0*(x<=0)+ x*(0<x)*(x<=3) + 3*(x>3),
    bounding_box=np.array([[-5,10],[-5,9]]),
    in_x=5.0,
    out_x=0.0,
    eta=np.radians(70)
    )
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
quadrature = UniformQuadrature(
    x_interval=geometry.landslide_interval,
    num=30
    ) 
options=Options(
    max_iteration = 200,
    tolerance = 1e-4
    )

res=bishop(geometry,soil_properties,soil_state,quadrature,options)
fig=geometry.plot(400)
plt.savefig("geometry.svg")

print(res.factor_of_safety)
