import numpy as np
import sys
sys.path.append("../limit-equilibrium")
from base_classes import SoilProperties,SoilState,UniformQuadrature,Options,np,plt
from bishop import bishop
from gridOfCircles import GridOptions, gridComputation,computeEtaMinForSurface
from circularSlipSurface import circularSlipSurface
import scipy.optimize as optimize


ground_surface=lambda x : 0*(x<=0)+ x*(0<x)*(x<=3) + 3*(x>3)
bounding_box=np.array([[-5,10],[-5,9]])
gOptions=GridOptions(in_interval=[3,10],out_interval=[-5,1],min_eta_inc=np.radians(5),num_in_pts=10,num_out_pts=10)

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
    tolerance = 1e-4
#    quadrature = lambda interval : UniformQuadrature(
#        x_interval=interval,
#        num=30
#        ) 
    )

[result,time_duration]=gridComputation(bishop, ground_surface,bounding_box,soil_properties,soil_state,gOptions,mOptions)
print(f'Bishop computation took {time_duration:.3f} seconds')
print(f'The grid contains {len(result):d} points')
fig=result[0].inputs[0].plot(400,dpc=240,x_cm=10)

for j in range(1,5):
    result[j].inputs[0].plotSlipSurface(400)


def func(v):
    x_in , x_out , eta = v[0] , v[1] , v[2]
    func.calls+=1
    if eta>computeEtaMinForSurface(ground_surface,bounding_box,x_in,x_out) and eta<np.pi/2:
        geometry=circularSlipSurface.fromInOutAndEta(ground_surface,bounding_box,x_in,x_out,eta)
        ff = bishop(geometry,soil_properties,soil_state,mOptions).factor_of_safety
    else:
        ff = 100.
    return ff

func.calls=0

bounds = ((1.5,10) ,
          (-10,0) , 
          (0, np.pi/2))

zero=[]
calls=[]
geos=[]
for j in range(0,5):
    trial=[result[j].inputs[0].landslide_interval[0],result[j].inputs[0].landslide_interval[1],result[j].inputs[0].eta]
    zero.append( optimize.minimize(func, trial , 
                          method='Nelder-Mead',
                          bounds = bounds,
                          options = {'disp':False  ,'xatol' : 1.e-2 , 'fatol':1e-2 , 'maxiter':100 , 'return_all':True}
                          )
    )
    calls.append(func.calls)
    print(f'Starting from grid FOS: {result[j].factor_of_safety:3f} the result is {zero[j].fun:3f} using {func.calls:d}')
    geos.append(circularSlipSurface.fromInOutAndEta(ground_surface,bounding_box,zero[j].x[0],zero[j].x[1],zero[j].x[2]))
    func.calls=0



plt.savefig("worst_simplex.svg")
print(result[0].factor_of_safety, result[-1].factor_of_safety)