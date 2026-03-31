import numpy as np
import scipy.interpolate as interp
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
    GeometryPlot(geo_ref,bounding_box=bounding_box).plotSlipSurface(100,label=f'FEM, F={FoS_ref}',color='black')
    plt.legend()
    plt.gca().set_aspect('equal')
    params=domain.getParameters(geo)
    print( f'fos={lemRes.factor_of_safety:>7.3f} for in={params[0]:>6.2f}, out={params[1]:>6.2f}, eta={np.degrees(params[2]):.0f}')
    print( f'Total time {time:.3f} seconds for {calls} calls')
    plt.show()

options=lemOptions()
base, height = 8.66 , 5.0
ground_surface=lambda x : 0.0*(x<=0.0)+ height * x/base*(0.0<x)*(x<=base) + height*(x>base)
bounding_box=np.array([[-5,15],[-4,6]])

zw = -2.0 # ground water table
pore_pressure = lambda x,y:  10*(-y + zw)
GWT = lambda x: zw*np.ones_like(x)

def VanGenuchten(suction, P, N,Sres):
    M = 1 - 1/N
    effective_saturation = (1+(suction/P)**N)**-M
    saturation = Sres + (1.0 - Sres)*effective_saturation
    return effective_saturation # use the effective degree of saturation because we are considering only mechanical effects


def column_weight(x,y,
                  ground_surface,
                  gamma_values, 
                  y_layer):
    ys = ground_surface(x)
    w1 = gamma_values[0]*(ys-y) #upper layer only
    w2 = (gamma_values[0]*(ys-y_layer(x)) + gamma_values[1]*(y_layer(x)-y) ) # both layers
    return np.where(y >= y_layer(x), w1, w2)


def makePiecewiseGeometryFromData(filename):
    data = np.loadtxt(filename, skiprows=1)
    knots = np.array([data[0,0], *data[:,0].tolist(), data[-1,0]])
    slip_fun=interp.make_interp_spline(data[:,0],data[:,1],k=1,t=knots)
    slip_tan=slip_fun.derivative()
    return Geometry(
        ground_surface=ground_surface,
        slip_surface=lambda x: slip_fun(x),
        slip_tangent=lambda x: slip_tan(x),
        landslide_interval=[data[0,0],data[-1,0]]
    )

"""
 Dataset from:
     Lalicata et al. (2025)    https://doi.org/10.1016/j.trgeo.2025.101582
"""

"""
 Clay Soil and no infiltration using Morgerstern & Price
"""
P , N , Sres = 200. , 1.56 , 0.2
gamma_values = [16, 18]
c, phi = 5 , 28.0 

soil=Soil.soilWithVerticalSampling(
          cohesion      =lambda x,y: c*np.ones_like(x+y),
          friction_angle=lambda x,y: phi*np.ones_like(x+y),
          pore_pressure = pore_pressure,
          saturation    =lambda x,y:  VanGenuchten(np.maximum(-pore_pressure(x,y) , 0.0), P , N , Sres),
          column_weight =lambda x,y: column_weight(x,y,
                                                   ground_surface,
                                                   gamma_values, 
                                                   y_layer=GWT),
          num_vertical_sample=1
    )

domain=circularSlipSearchDomain(
    ground_surface=ground_surface,
    in_range=(8.,20.),
    out_range=(-5,1.),
)

method=lemMethod(morgerstern_price,soil,options)

grid_options={
    "num_in_points"  : 10,
    "num_out_points" : 10
    }

FoS_ref =2.968
geo_ref = makePiecewiseGeometryFromData("SlipSurfUnsatClay.txt")

computeAndPlotComparison('Case 1): Unsaturated Clay - M&P method',bounding_box,domain,method,grid_options,FoS_ref, geo_ref)


"""
 Sand Soil and no infiltration using Morgerstern & Price
"""
P , N , Sres = 5. , 1.8 , 0.1
gamma_values = [16, 18]
c, phi = 0. , 33.0 

soil=Soil.soilWithVerticalSampling(
          cohesion      =lambda x,y: c*np.ones_like(x+y),
          friction_angle=lambda x,y: phi*np.ones_like(x+y),
          pore_pressure = pore_pressure,
          saturation    =lambda x,y:  VanGenuchten(np.maximum(-pore_pressure(x,y) , 0.0), P , N , Sres),
          column_weight =lambda x,y: column_weight(x,y,
                                                   ground_surface,
                                                   gamma_values, 
                                                   y_layer=GWT),
          num_vertical_sample=1
    )

domain=circularSlipSearchDomain(
    ground_surface=ground_surface,
    in_range=(8.,20.),
    out_range=(-5,1.),
)

method=lemMethod(morgerstern_price,soil,options)

grid_options={
    "num_in_points"  : 10,
    "num_out_points" : 10
    }

FoS_ref =1.897
geo_ref = makePiecewiseGeometryFromData("SlipSurfUnsatSand.txt")

computeAndPlotComparison('Case 2): Unsaturated Sand - M&P method',bounding_box,domain,method,grid_options,FoS_ref, geo_ref)
