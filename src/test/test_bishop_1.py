import numpy as np
import sys
sys.path.append("../limit-equilibrium")
import base_classes as bc
from circularSlipSurface import circularSplipSurface
from bishop import bishop


geometry=circularSplipSurface.fromInOutAndEta(
    ground_surface=lambda x : 0*(x<=0)+ x*(0<x)*(x<=3) + 3*(x>3),
    bounding_box=np.array([[-10,10],[-9,9]]),
    in_x=5.0,
    out_x=0.0,
    eta=np.radians(70)
    )
soil_properties=bc.SoilProperties( 
    cohesion       = lambda x,y : 5.0,
    friction_angle = lambda x,y : 30.0,
    dry_density    = lambda x,y : 18.0,
    porosity       = lambda x,y : 0.0,
    grain_density  = lambda x,y : 0.0
    )
soil_state=bc.SoilState(
    saturation         = lambda x,y : 1.0,
    pore_pressure      = lambda x,y : 0.0,
    integrated_density = lambda x,y : 18.0*(geometry.ground_surface(x)-y)
    )
quadrature = bc.UniformQuadrature(
    x_interval=geometry.landslide_interval,
    num=30
    ) 
options=bc.Options(
    max_iteration = 200,
    tolerance = 1e-4
    )

res=bishop(geometry,soil_properties,soil_state,quadrature,options)
print(res.factor_of_safety)