import numpy as np
import pandas as pd
import sys
sys.path.append("../limit-equilibrium")
from base_classes import SoilProperties,SoilState,UniformQuadrature,Options,np,plt
from bishop import bishop
from slices_data import slices_data
from gridOfCircles import GridOptions, gridComputation,computeEtaMinForSurface
from circularSlipSurface import circularSlipSurface
import scipy.optimize as optimize
import time

# Aggiunta da Leo: così funziona
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 300

# Caso singolo
# beta = np.arange(15, 95 , 5)
beta = 35
slope_height = 5.
slope_base = slope_height / np.tan(np.radians(beta))
dist_max = max(slope_base,slope_height)

ground_surface=(lambda x : 0*(x<=0) 
                + x*np.tan(np.radians(beta)) *(0<x)*(x<=slope_base) 
                + slope_height*(x>slope_base))
bounding_box=np.array([[-3*dist_max,3*dist_max],[-1.5*slope_height,1.5*slope_height]])

gOptions=GridOptions(
    in_pts=[1.*slope_base,1/3*dist_max+slope_base, 2/3*dist_max+slope_base, 1*dist_max+slope_base],
    out_pts=[-1*dist_max,-1/2*dist_max ,-1/4*dist_max, 0., 1/8*slope_base, 1/4*slope_base],
    min_eta_inc=np.radians(5),
    num_in_pts=None,
    num_out_pts=None)


M=[2]
constant_dry_density=18.0
phi  = 20. # angolo d'attrito
soil_properties=SoilProperties( 
    cohesion       = lambda x,y : M * constant_dry_density * slope_height * np.tan(np.radians(phi))*np.ones_like(x+y),
    friction_angle = lambda x,y : phi*np.ones_like(x+y),
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

def func(v):
    x_in , x_out , eta = v[0] , v[1] , np.radians(v[2])
    func.calls+=1
    eta_min=computeEtaMinForSurface(ground_surface,bounding_box,x_in,x_out)
    if eta < eta_min:
        return np.nan
    else:
        geometry=circularSlipSurface.fromInOutAndEta(ground_surface,bounding_box,x_in,x_out,eta)
        return bishop(geometry,soil_properties,soil_state,mOptions).factor_of_safety


time_start=time.perf_counter()
func.calls=0
bounds = ((1*slope_base,5*dist_max+slope_base) ,
          (-5*dist_max,1/4*slope_base) , 
          (0., 90))

result=[]    
zero=[]
calls=[]
start_geo=[]
end_geo=[]
for j in range(0,len(M)):
    soil_properties=SoilProperties( 
        cohesion       = lambda x,y : M[j] * constant_dry_density * slope_height * np.tan(np.radians(phi))*np.ones_like(x+y),
        friction_angle = lambda x,y : phi*np.ones_like(x+y),
        dry_density    = lambda x,y : constant_dry_density*np.ones_like(x+y),
        porosity       = lambda x,y : 0.0*np.ones_like(x+y),
        grain_density  = lambda x,y : 0.0*np.ones_like(x+y)
        )
    [result,time_duration]=gridComputation(bishop, ground_surface,bounding_box,soil_properties,soil_state,gOptions,mOptions)
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
    # print(f'M={M[j]:.3f},', f'F/tan(phi)={zero[j].fun/np.tan(np.radians(phi)):.3f}')
    end_geo.append(circularSlipSurface.fromInOutAndEta(ground_surface,bounding_box,zero[j].x[0],zero[j].x[1],np.radians(zero[j].x[2])))
#    print(f'Eta = {np.degrees(zero[j].x[2]):.2f}, Eta_min = {np.degrees(computeEtaMinForSurface(ground_surface,bounding_box,zero[j].x[0],zero[j].x[1])):.2f}')
    # print(f'Diff = {zero[j].x-trial}')
    # print(np.degrees(start_geo.eta) , zero[j].x[2])
    # print(f'M={M[j]:.2f} : after-optimization-FOS={zero[j].fun:.3f}, starting-FOS={result[j].factor_of_safety:.3f}, using {calls[j]:d} evaluations')
    # print(f'M={M[j]:.2f} : F/tan(phi)={zero[j].fun/np.tan(np.radians(phi)):.3f}')
    


time_duration = time.perf_counter()- time_start
print(f'\nThe simplex method took {time_duration:.3f}s per start, {time_duration:.3f}s in total\n')


# Print ending cases
plt.figure()
end_geo[0].plot(300,x_cm=10)
for j in range(0,len(M)):
    end_geo[j].plotSlipSurface(200)

plt.show()
plt.savefig('simplex_ending_geometries.svg')
plt.close()

# voglio estrarre i dati delle strisce
circle = circularSlipSurface.fromInOutAndEta(ground_surface,bounding_box,zero[0].x[0],zero[0].x[1],np.radians(zero[0].x[2]))
bishopp = bishop(circle, soil_properties, soil_state, mOptions)
strisce = slices_data(circle, soil_properties, soil_state, mOptions)
striscia = pd.DataFrame({'x'           : strisce[0],
                         'y'           : strisce[1],
                         'C. coesione' : strisce[-2]*strisce[-1],
                         'Peso'        : strisce[-3]*strisce[5]*strisce[-1]})

C = bishopp.resisting_cohesive.sum()
PHI = bishopp.resisting_frictional.sum()
TOT = bishopp.resisting_forces.sum()
A = bishopp.weight_forces.sum()

print('Factor of safety:')
print(f'{bishopp.factor_of_safety:.3f}, {C/A:.3f}, {PHI/A:.3f}\n' )
print('Normalised Factor of safety')
print(f'{bishopp.factor_of_safety/strisce[6][0]:.3f}, {C/A/strisce[6][0]:.3f}, {PHI/A/strisce[6][0]:.3f}\n')


cohesion = soil_properties.cohesion(0,0)
friction_angle = phi
# Analisi solo coesiva (phi=0) per la sds critica dell'analisi completa
cohesion_only=SoilProperties( 
    cohesion       = lambda x,y : cohesion*np.ones_like(x+y),
    friction_angle = lambda x,y : 0*friction_angle*np.ones_like(x+y),
    dry_density    = lambda x,y : constant_dry_density*np.ones_like(x+y),
    porosity       = lambda x,y : 0.0*np.ones_like(x+y),
    grain_density  = lambda x,y : 0.0*np.ones_like(x+y)
    )
F_cohesion = bishop(circle, cohesion_only, soil_state, mOptions)

# Analisi solo attritiva (c=0) per la sds critica dell'analisi completa
friction_only=SoilProperties( 
    cohesion       = lambda x,y : 0*cohesion*np.ones_like(x+y),
    friction_angle = lambda x,y : friction_angle*np.ones_like(x+y),
    dry_density    = lambda x,y : constant_dry_density*np.ones_like(x+y),
    porosity       = lambda x,y : 0.0*np.ones_like(x+y),
    grain_density  = lambda x,y : 0.0*np.ones_like(x+y)
    )
F_friction = bishop(circle, friction_only, soil_state, mOptions)

print(f'Global factor of safety: {bishopp.factor_of_safety:.3f}' )
print(f'Cohesive factor of safety: {F_cohesion.factor_of_safety:.3f}' )
print(f'Frictional factor of safety: {F_friction.factor_of_safety:.3f}' )
diff = bishopp.factor_of_safety - (F_friction.factor_of_safety+F_cohesion.factor_of_safety)
print(f'difference: {diff}' )
