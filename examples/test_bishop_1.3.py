import numpy as np
import time
import sys
sys.path.append("../src/LEM")
sys.path.append("../src/searchCriticalF")
from base_classes import SoilProperties,SoilState,UniformQuadrature,Options,np,plt
from circularSlipSurface import circularSlipSurface
from gridOfCircles import GridOptions, gridComputation,computeEtaMinForSurface
from bishop import bishop
import scipy.optimize as optimize

geometry=circularSlipSurface.fromInOutAndEta(
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

plt.savefig("geometry.svg")
# print('Safety Factor 1:', round(res.factor_of_safety,5))


def func(v):
    x_in , x_out , eta = v[0] , v[1] , np.radians(v[2])
    func.calls+=1
    eta_min2=computeEtaMinForSurface(geometry.ground_surface,geometry.bounding_box,x_in,x_out)
    
    sds_in = [x_in , geometry.ground_surface(x_in)]
    sds_out = [x_out , geometry.ground_surface(x_out)]
    if x_out >= 0.0:
        eta_min = np.arctan(sds_in[1]/ sds_in[0])
    else:
        m_perp_in_0 =  - sds_in[0]/sds_in[1]
        xc_min = 0.5 * sds_out[0]
        yc_min = sds_in[1] + m_perp_in_0 * (xc_min - sds_in[0])
        eta_min = max(np.arctan(- (sds_in[0]  - xc_min ) / (sds_in[1]  - yc_min )) , 
                      np.arctan(sds_in[1]/ sds_in[0]))
    # return eta>eta_min
    if np.abs(eta_min - eta_min2) > 1.e-8:  
        # print('err in eta (°):' , np.degrees(abs(eta_min - eta_min2)) )
        print(np.degrees(eta_min) ,np.degrees(eta_min2) )
    if eta < eta_min:
        return 100
    else:
        Geometry=circularSlipSurface.fromInOutAndEta(geometry.ground_surface,geometry.bounding_box,x_in,x_out,eta)
        return bishop(Geometry,soil_properties,soil_state,options).factor_of_safety


time_start=time.perf_counter()
func.calls=0
bounds = ((2,10) ,
          (-10,1) , 
          (0, 90))
        
zero=[]
calls=[]
start_geo=[]
end_geo=[]
start_geo=geometry
trial=[start_geo.landslide_interval[1],start_geo.landslide_interval[0],np.degrees(start_geo.eta)]
zero = optimize.minimize(func, trial , 
                      method='Nelder-Mead',
                      bounds = bounds,
                      options = {
                        'disp'      : False,
                        'xatol'     : 1e-3,
                        'fatol'     : 1e-4,
                        'maxiter'   : 100,
                        'return_all': True
                        }
                      )
calls.append(func.calls)
end_geo = circularSlipSurface.fromInOutAndEta(geometry.ground_surface,geometry.bounding_box,zero.x[0],zero.x[1],np.radians(zero.x[2]))
# print(f'Diff = {zero.x-trial}')

time_duration = time.perf_counter()- time_start
fig=geometry.plot(400)
end_geo.plotSlipSurface(num_points=400,color='blue')
print(f'start of simplex = {trial}, FoS = {res.factor_of_safety}')
print(f'end of simplex = {zero.x}, FoS = {zero.fun}, Func calls = {func.calls}')