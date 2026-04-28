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


def computeAndPlotComparison(title,bounding_box,domain,method,grid_options,FoS_ref, geo_ref):
    result,time,calls=grid_simplex(domain=domain,method=method,grid_options=grid_options,num_geometries=1,options={"num_grid_output":3 })
    plt.figure(dpi=300)
    (geo,lemRes)=result[0]
    GeometryPlot(geo,bounding_box=bounding_box).plotTerrain(100)
    GeometryPlot(geo,bounding_box=bounding_box).plotSlipSurface(100,label= f'this code, F={lemRes.factor_of_safety:.3f}')
    plt.title(title)
    GeometryPlot(geo_ref,bounding_box=bounding_box).plotSlipSurface(100,label=f'Himansu and Burman (2019), F={FoS_ref}',color='black')
    plt.legend()
    plt.gca().set_aspect('equal')
    params=domain.getParameters(geo)
    print( f'fos={lemRes.factor_of_safety:>7.3f} for in={params[0]:>6.2f}, out={params[1]:>6.2f}, eta={np.degrees(params[2]):.0f}')
    print( f'Total time {time:.3f} seconds for {calls} calls')
    plt.show()


"""
 Dataset from:
     Lalicata et al. (2024)    https://doi.org/10.1007/s40999-024-01053-1
     Himansu and Burman (2019) https://doi.org/10.1007/s10706-018-0683-8
"""
options=lemOptions()
base, height = 10.0 , 5.0
ground_surface_orig=lambda x : 0.0*(x<=0.0)+ height * x/base*(0.0<x)*(x<=base) + height*(x>base)
ground_surface=lambda x : ground_surface_orig(-x)


"""
 1) Homogeneous dry soil using Bishop
"""
c, phi, gamma = 9.8 , 10.0 , 17.64

soil=Soil.soilWithVerticalSampling(
          cohesion      =lambda x,y: c*np.ones_like(x+y),
          friction_angle=lambda x,y: phi*np.ones_like(x+y),
          pore_pressure =lambda x,y: 0.0*np.ones_like(x+y),
          saturation    =lambda x,y: 0.0*np.ones_like(x+y),
          column_weight =lambda x,y: gamma*(ground_surface(x)-y),
          num_vertical_sample=1
    )

domain=circularSlipSearchDomain(
    ground_surface=ground_surface,
    in_range=(-14,-8),
    out_range=(-4,1),
    )
bounding_box=np.array([[-13,1.5],[-2.5,7.0]])

method=lemMethod(bishop,soil,options)
# grid_options={
#     "in_points":np.array([3.,4.,5.]),
#     "out_points":np.array([-1.,0.,.5])}
grid_options={
    "num_in_points"  : 5,
    "num_out_points" : 5
    }
FoS_ref =1.313
geo_ref = circularArc.fromCenterAndRadius(ground_surface, center=[-3.7,9.1] ,radius=9.8)

computeAndPlotComparison('Case 1): Bishop Method',bounding_box,domain,method,grid_options,FoS_ref, geo_ref)



"""
 2) Homogeneous dry soil using Bishop
"""
base, height = 17 , 8.5
ground_surface_orig=lambda x : 0.0*(x<=0.0)+ height * x/base*(0.0<x)*(x<=base) + height*(x>base)
ground_surface=lambda x :ground_surface_orig(-x)
c, phi, gamma = 14.71 , 20.0 , 18.63

soil=Soil.soilWithVerticalSampling(
          cohesion      =lambda x,y: c*np.ones_like(x+y),
          friction_angle=lambda x,y: phi*np.ones_like(x+y),
          pore_pressure =lambda x,y: 0.0*np.ones_like(x+y),
          saturation    =lambda x,y: 0.0*np.ones_like(x+y),
          column_weight =lambda x,y: gamma*(ground_surface(x)-y),
          num_vertical_sample=1
    )

domain=circularSlipSearchDomain(
    ground_surface=ground_surface,
    in_range=(-30,-15),
    out_range=(-1,4),
    )
bounding_box=np.array([[-22,2.5],[-4.2,12]])

method=lemMethod(bishop,soil,options)
# grid_options={
#     "in_points":np.array([3.,4.,5.]),
#     "out_points":np.array([-1.,0.,.5])}
grid_options={
    "num_in_points"  : 5,
    "num_out_points" : 5
    }
FoS_ref = 1.719
geo_ref = circularArc.fromCenterAndRadius(ground_surface, center=[-4.4,17.3] ,radius=17.9)

computeAndPlotComparison('Case 2): Bishop Method',bounding_box,domain,method,grid_options,FoS_ref, geo_ref)


#------------------------------------------------------------------------------
# Helpers for terrains with two layers
#------------------------------------------------------------------------------

def layered_property(v1, v2,y_layer):
    return lambda x,y: np.float64(np.where(y >= y_layer(x), v1, v2))

def column_weight(x,y,
                  ground_surface,
                  gamma_values, 
                  y_layer):
    ys = ground_surface(x)
    w1 = gamma_values[0]*(ys-y) #upper layer only
    w2 = (gamma_values[0]*(ys-y_layer(x)) + gamma_values[1]*(y_layer(x)-y) ) # both layers
    return np.where(y >= y_layer(x), w1, w2)



"""
 3) two layers dry soil using Bishop
"""
base, height = 10.0 , 5.0
ground_surface_orig=lambda x : 0.0*(x<=0.0)+ height * x/base*(0.0<x)*(x<=base) + height*(x>base)
ground_surface=lambda x :ground_surface_orig(-x)

y_layer = lambda x: 2.5*np.ones_like(x)
c_values     = [14.71,  9.8 ]
phi_values   = [20.0 , 10.0 ]
gamma_values = [18.63, 17.64]

c       = layered_property(c_values[0]    , c_values[1]    , y_layer)
phi     = layered_property(phi_values[0]  , phi_values[1]  , y_layer)

soil=Soil.soilWithVerticalSampling(
          cohesion      = c,
          friction_angle=  phi,
          pore_pressure =lambda x,y: 0.0*np.ones_like(x+y),
          saturation    =lambda x,y: 0.0*np.ones_like(x+y),
          column_weight =lambda x,y: column_weight(x,y,
                                                   ground_surface,
                                                   gamma_values, 
                                                   y_layer),
          num_vertical_sample=1
    )

domain=circularSlipSearchDomain(
    ground_surface=ground_surface,
    in_range=(-15,-10),
    out_range=(-1,4),
    )
bounding_box=np.array([[-13,1.5],[-2.5,7.0]])

method=lemMethod(bishop,soil,options)
# grid_options={
#     "in_points":np.array([3.,4.,5.]),
#     "out_points":np.array([-1.,0.,.5])}
grid_options={
    "num_in_points"  : 5,
    "num_out_points" : 5
    }
#Data from case 2
FoS_ref = 1.339
geo_ref = circularArc.fromCenterAndRadius(ground_surface, center=[-3.8,8.2] ,radius=9.2)

computeAndPlotComparison('Case 3): Bishop Method',bounding_box,domain,method,grid_options,FoS_ref, geo_ref)


"""
 4) two layers dry soil using Bishop
"""
base, height = 10.0 , 5.0
ground_surface_orig=lambda x : 0.0*(x<=0.0)+ height * x/base*(0.0<x)*(x<=base) + height*(x>base)
ground_surface=lambda x :ground_surface_orig(-x)
y_layer_orig = lambda x: np.maximum(-0.107+0.607*x,0.0)
y_layer = lambda x: y_layer_orig(-x)

c_values     = [14.71,  9.8 ]
phi_values   = [20.0 , 10.0 ]
gamma_values = [18.63, 17.64]

c       = layered_property(c_values[0]    , c_values[1],   y_layer)
phi     = layered_property(phi_values[0]  , phi_values[1], y_layer)

soil=Soil.soilWithVerticalSampling(
          cohesion      = c,
          friction_angle=  phi,
          pore_pressure =lambda x,y: 0.0*np.ones_like(x+y),
          saturation    =lambda x,y: 0.0*np.ones_like(x+y),
          column_weight =lambda x,y: column_weight(x,y,
                                                   ground_surface,
                                                   gamma_values, 
                                                   y_layer),
          num_vertical_sample=1
    )

domain=circularSlipSearchDomain(
    ground_surface=ground_surface,
    in_range=(-15,-10),
    out_range=(-1,4),
    )
bounding_box=np.array([[-13,1.5],[-2.5,7.0]])

method=lemMethod(bishop,soil,options)
# grid_options={
#     "in_points":np.array([3.,4.,5.]),
#     "out_points":np.array([-1.,0.,.5])}
grid_options={
    "num_in_points"  : 5,
    "num_out_points" : 5
    }

#Data from case 4
FoS_ref = 1.318
geo_ref = circularArc.fromCenterAndRadius(ground_surface, center=[-3.8,8.8] ,radius=9.9)

computeAndPlotComparison('Case 4): Bishop Method',bounding_box,domain,method,grid_options,FoS_ref, geo_ref)