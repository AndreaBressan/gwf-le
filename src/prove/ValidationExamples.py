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
base, height = 10.0 , 5.0
ground_surface=lambda x : 0.0*(x<=0.0)+ height * x/base*(0.0<x)*(x<=base) + height*(x>base)

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
    in_range=(8,14),
    out_range=(-4,1.),
    )

method=lemMethod(bishop,soil,options)
# grid_options={
#     "in_points":np.array([3.,4.,5.]),
#     "out_points":np.array([-1.,0.,.5])}
grid_options={
    "num_in_points"  : 5,
    "num_out_points" : 5
    }

result,time,calls=grid_simplex(domain=domain,method=method,grid_options=grid_options,num_geometries=1,options={"num_grid_output":3 })

plt.figure(dpi=300)
(geo,lemRes)=result[0]
bounding_box=np.array([[-1.5,13],[-2.5,7.0]])
GeometryPlot(geo,bounding_box=bounding_box).plotTerrain(100)
GeometryPlot(geo,bounding_box=bounding_box).plotSlipSurface(100,label= f'this code, F={lemRes.factor_of_safety:.3f}')
plt.title('Case 1): Bishop Method')
#Data from case 1
FoS_ref = 1.313
geo_ref = circularArc.fromCenterAndRadius(ground_surface, center=[3.7,9.1] ,radius=9.8)
GeometryPlot(geo_ref,bounding_box=bounding_box).plotSlipSurface(100,label=f'Himansu and Burman (2019), F={FoS_ref}',color='black')

plt.legend()
plt.gca().set_aspect('equal')
#
params=domain.getParameters(geo)
print( f'fos={lemRes.factor_of_safety:>7.3f} for in={params[0]:>6.2f}, out={params[1]:>6.2f}, eta={np.degrees(params[2]):.0f}')
print( f'Total time {time:.3f} seconds for {calls} calls')
plt.show()


"""
 2) Homogeneous dry soil using Bishop
"""
base, height = 17 , 8.5
ground_surface=lambda x : 0.0*(x<=0.0)+ height * x/base*(0.0<x)*(x<=base) + height*(x>base)
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
    in_range=(15,30),
    out_range=(-4,1.),
    )

method=lemMethod(bishop,soil,options)
# grid_options={
#     "in_points":np.array([3.,4.,5.]),
#     "out_points":np.array([-1.,0.,.5])}
grid_options={
    "num_in_points"  : 5,
    "num_out_points" : 5
    }

result,time,calls=grid_simplex(domain=domain,method=method,grid_options=grid_options,num_geometries=1,options={"num_grid_output":3 })

plt.figure(dpi=300)
(geo,lemRes)=result[0]
bounding_box=np.array([[-2.5,22],[-4.2,12]])
GeometryPlot(geo,bounding_box=bounding_box).plotTerrain(100)
GeometryPlot(geo,bounding_box=bounding_box).plotSlipSurface(100,label= f'this code, F={lemRes.factor_of_safety:.3f}')
plt.title('Case 2): Bishop Method')
#Data from case 2
FoS_ref = 1.719
geo_ref = circularArc.fromCenterAndRadius(ground_surface, center=[4.4,17.3] ,radius=17.9)
GeometryPlot(geo_ref,bounding_box=bounding_box).plotSlipSurface(100,label=f'Himansu and Burman (2019), F={FoS_ref}',color='black')

plt.legend()
plt.gca().set_aspect('equal')
#
params=domain.getParameters(geo)
print( f'fos={lemRes.factor_of_safety:>7.3f} for in={params[0]:>6.2f}, out={params[1]:>6.2f}, eta={np.degrees(params[2]):.0f}')
print( f'Total time {time:.3f} seconds for {calls} calls')
plt.show()

#------------------------------------------------------------------------------
# Andrea, i due casi con il terreno stratificato funzionano,
# ma sicuramente si possono migliorare le funzioni che ho messo per renderle
# più leggere coerenti.
# ci puoi pensare te?
#------------------------------------------------------------------------------
"""
 3) two layers dry soil using Bishop
"""
base, height = 10.0 , 5.0
ground_surface=lambda x : 0.0*(x<=0.0)+ height * x/base*(0.0<x)*(x<=base) + height*(x>base)

y_layer = 2.5
c_values     = [14.71,  9.8 ]
phi_values   = [20.0 , 10.0 ]
gamma_values = [18.63, 17.64]

def layered_property(v1, v2, y_layer):
    return lambda x,y: np.where(y >= y_layer, v1, v2)

c       = layered_property(c_values[0]    , c_values[1]    , y_layer)
phi     = layered_property(phi_values[0]  , phi_values[1]  , y_layer)
gamma   = layered_property(gamma_values[0], gamma_values[1], y_layer)

# controllare che questa funzioni
def column_weight(x,y,
                  ground_surface,
                  gamma_values, 
                  y_layer):
    ys = ground_surface(x)

    w1 = gamma_values[0]*(ys-y) #upper layer only
    w2 = (
         gamma_values[0]*(ys-y_layer) +
         gamma_values[1]*(y_layer-y)
         ) # both layers
    
    return np.where(y >= y_layer, w1, w2)

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
    in_range=(10,15),
    out_range=(-4,1.),
    )

method=lemMethod(bishop,soil,options)
# grid_options={
#     "in_points":np.array([3.,4.,5.]),
#     "out_points":np.array([-1.,0.,.5])}
grid_options={
    "num_in_points"  : 5,
    "num_out_points" : 5
    }

result,time,calls=grid_simplex(domain=domain,method=method,grid_options=grid_options,num_geometries=1,options={"num_grid_output":3 })

plt.figure(dpi=300)
(geo,lemRes)=result[0]
bounding_box=np.array([[-1.5,13],[-2.5,7.0]])
GeometryPlot(geo,bounding_box=bounding_box).plotTerrain(100)
GeometryPlot(geo,bounding_box=bounding_box).plotSlipSurface(100,label= f'this code, F={lemRes.factor_of_safety:.3f}')
plt.title('Case 3): Bishop Method')
#Data from case 2
FoS_ref = 1.339
geo_ref = circularArc.fromCenterAndRadius(ground_surface, center=[3.8,8.2] ,radius=9.2)
GeometryPlot(geo_ref,bounding_box=bounding_box).plotSlipSurface(100,label=f'Himansu and Burman (2019), F={FoS_ref}',color='black')

plt.legend()
plt.gca().set_aspect('equal')
#
params=domain.getParameters(geo)
print( f'fos={lemRes.factor_of_safety:>7.3f} for in={params[0]:>6.2f}, out={params[1]:>6.2f}, eta={np.degrees(params[2]):.0f}')
print( f'Total time {time:.3f} seconds for {calls} calls')
plt.show()


"""
 4) two layers dry soil using Bishop
"""
base, height = 10.0 , 5.0
ground_surface=lambda x : 0.0*(x<=0.0)+ height * x/base*(0.0<x)*(x<=base) + height*(x>base)

y_layer = lambda x: np.maximum(-0.107+0.607*x,0.0)

c_values     = [14.71,  9.8 ]
phi_values   = [20.0 , 10.0 ]
gamma_values = [18.63, 17.64]

def layered_property(v1, v2):
    return lambda x,y: np.float64(np.where(y >= y_layer(x), v1, v2))

c       = layered_property(c_values[0]    , c_values[1] )
phi     = layered_property(phi_values[0]  , phi_values[1])
gamma   = layered_property(gamma_values[0], gamma_values[1])

# controllare che questa funzioni
def column_weight(x,y,
                  ground_surface,
                  gamma_values, 
                  y_layer):
    ys = ground_surface(x)

    w1 = gamma_values[0]*(ys-y) #upper layer only
    w2 = (
         gamma_values[0]*(ys-y_layer(x)) +
         gamma_values[1]*(y_layer(x)-y)
         ) # both layers
    
    return np.where(y >= y_layer(x), w1, w2)

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
    in_range=(10,15),
    out_range=(-4,1.),
    )

method=lemMethod(bishop,soil,options)
# grid_options={
#     "in_points":np.array([3.,4.,5.]),
#     "out_points":np.array([-1.,0.,.5])}
grid_options={
    "num_in_points"  : 5,
    "num_out_points" : 5
    }

result,time,calls=grid_simplex(domain=domain,method=method,grid_options=grid_options,num_geometries=1,options={"num_grid_output":3 })

plt.figure(dpi=300)
(geo,lemRes)=result[0]
bounding_box=np.array([[-1.5,13],[-2.5,7.0]])
GeometryPlot(geo,bounding_box=bounding_box).plotTerrain(100)
GeometryPlot(geo,bounding_box=bounding_box).plotSlipSurface(100,label= f'this code, F={lemRes.factor_of_safety:.3f}')
plt.title('Case 4): Bishop Method')
#Data from case 2
FoS_ref = 1.318
geo_ref = circularArc.fromCenterAndRadius(ground_surface, center=[3.8,8.8] ,radius=9.9)
GeometryPlot(geo_ref,bounding_box=bounding_box).plotSlipSurface(100,label=f'Himansu and Burman (2019), F={FoS_ref}',color='black')

plt.legend()
plt.gca().set_aspect('equal')
#
params=domain.getParameters(geo)
print( f'fos={lemRes.factor_of_safety:>7.3f} for in={params[0]:>6.2f}, out={params[1]:>6.2f}, eta={np.degrees(params[2]):.0f}')
print( f'Total time {time:.3f} seconds for {calls} calls')
plt.show()