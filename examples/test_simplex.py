import numpy as np
import sys
sys.path.append("../src/LEM")
sys.path.append("../src/searchCriticalF")
from base_classes import SoilProperties,SoilState,UniformQuadrature,Options,np,plt
from bishop import bishop
from gridOfCircles import GridOptions, gridComputation,computeEtaMinForSurface
from circularSlipSurface import circularSlipSurface
import scipy.optimize as optimize
import time

# Aggiunta da Leo: così funziona
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 300

#import warnings
#warnings.filterwarnings("error")

ground_surface=lambda x : 0*(x<=0)+ x*(0<x)*(x<=3) + 3*(x>3)
bounding_box=np.array([[-5,10],[-5,9]])
gOptions=GridOptions(
    in_interval=[2,10],
    out_interval=[-5,1],
    min_eta_inc=np.radians(7),
    num_in_pts=15,
    num_out_pts=15)

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
        num=50
        ) 
    )

[result,time_duration]=gridComputation(bishop, ground_surface,bounding_box,soil_properties,soil_state,gOptions,mOptions)
print(f'The grid contains {len(result):d} points, all evaluations took {time_duration:.3f} seconds')

nstart=10
# Plot worst nstart cases
result[0].inputs[0].plot(300,x_cm=10)
for j in range(1,nstart):
    result[j].inputs[0].plotSlipSurface(200)
plt.savefig('simplex_starting_points.svg')
plt.close()

def func(v):
    x_in , x_out , eta = v[0] , v[1] , np.radians(v[2])
    func.calls+=1
    eta_min=computeEtaMinForSurface(ground_surface,bounding_box,x_in,x_out)
    if eta < eta_min:
        return 100
    else:
        geometry=circularSlipSurface.fromInOutAndEta(ground_surface,bounding_box,x_in,x_out,eta)
        return bishop(geometry,soil_properties,soil_state,mOptions).factor_of_safety


time_start=time.perf_counter()
func.calls=0
bounds = ((2,10) ,
          (-10,1) , 
          (0, 90))
        
zero=[]
calls=[]
start_geo=[]
end_geo=[]
for j in range(0,nstart):
    start_geo=result[j].inputs[0]
    trial=[start_geo.landslide_interval[1],start_geo.landslide_interval[0],np.degrees(start_geo.eta)]
    zero.append( optimize.minimize(func, trial , 
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
    )
    calls.append(func.calls)
    func.calls=0
    print(f'{j:d}.',end='')
    end_geo.append(circularSlipSurface.fromInOutAndEta(ground_surface,bounding_box,zero[j].x[0],zero[j].x[1],np.radians(zero[j].x[2])))
#    print(f'Eta = {np.degrees(zero[j].x[2]):.2f}, Eta_min = {np.degrees(computeEtaMinForSurface(ground_surface,bounding_box,zero[j].x[0],zero[j].x[1])):.2f}')
    print(f'Diff = {zero[j].x-trial}')


time_duration = time.perf_counter()- time_start
print(f'\nThe simplex method took {time_duration/nstart:.3f}s per start, {time_duration:.3f}s in total')

# Print per case summary and plot surfaces
for j in range(0,nstart):
    print(f'Case {j:2d}: after-optimization-FOS={zero[j].fun:3f}, starting-FOS={result[j].factor_of_safety:3f}, using {calls[j]:d} evaluations')
    plt.figure()
    result[j].inputs[0].plot(300)
    end_geo[j].plotSlipSurface(200,color=(0,0,1))
    plt.savefig(f'simplex_comparison_{j:2d}.svg')
    plt.show()
    plt.close()

# Print ending cases
plt.figure()
end_geo[0].plot(300,x_cm=10)
for j in range(1,nstart):
    end_geo[j].plotSlipSurface(200,color=(0,0,1))
plt.show()
plt.savefig('simplex_ending_geometries.svg')
plt.close()

print('End')
