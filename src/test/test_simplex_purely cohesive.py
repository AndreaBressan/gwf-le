import numpy as np
import pandas as pd
import sys
sys.path.append("../limit-equilibrium")
from base_classes import SoilProperties,SoilState,UniformQuadrature,Options,np,plt
from bishop import bishop
from gridOfCircles import GridOptions, gridComputation,computeEtaMinForSurface
from circularSlipSurface import circularSlipSurface
import scipy.optimize as optimize
import time

# Aggiunta da Leo: così funziona
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 300

# parametrizzo la geometria e le bounding box in funzione dell'angolo
beta = np.arange(15, 95 , 5)
# beta = 35
slope_height = 1.


##

constant_dry_density=1.0
phi  = 00. # angolo d'attrito
soil_properties=SoilProperties( 
    cohesion       = lambda x,y : 1.0*np.ones_like(x+y),
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


result=[]    
zero=[]
calls=[]
start_geo=[]
end_geo=[]
for j in range(len(beta)):
    slope_base = slope_height / np.tan(np.radians(beta[j]))
    dist_max = max(slope_base,slope_height)

    ground_surface=(lambda x : 0*(x<=0) 
                    + x*np.tan(np.radians(beta[j])) *(0<x)*(x<=slope_base) 
                    + slope_height*(x>slope_base))
    bounding_box=np.array([[-3*dist_max,3*dist_max],[-1.5*slope_height,1.5*slope_height]])
    gOptions=GridOptions(
        in_interval=[1.*slope_base,5*dist_max],
        out_interval=[-5*dist_max,1/4*slope_base*0],
        min_eta_inc=np.radians(5),
        num_in_pts=15,
        num_out_pts=15)
    
    # anche i bounds
    bounds = ((1*slope_base,10*dist_max) ,
              (-10*dist_max,1/16*slope_base*0.) , 
              (0., 90))
    
    [l_result,time_duration]=gridComputation(bishop, ground_surface,bounding_box,soil_properties,soil_state,gOptions,mOptions)
    result.append(l_result[0])
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
    end_geo.append(circularSlipSurface.fromInOutAndEta(ground_surface,bounding_box,zero[j].x[0],zero[j].x[1],np.radians(zero[j].x[2])))
    print(f'beta={beta[j]:.2f} : after-optimization-FOS={zero[j].fun:.3f}, starting-FOS={result[j].factor_of_safety:.3f}, using {calls[j]:d} evaluations')
    plt.figure()
    end_geo[j].plot(300,x_cm=10)
    start_geo.plotSlipSurface(200, 'blue')
    end_geo[j].plotSlipSurface(200, 'red')

    


time_duration = time.perf_counter()- time_start
print(f'\nThe simplex method took {time_duration:.3f}s per start, {time_duration:.3f}s in total')

#%%
"""
save data in a decent format
"""

def res_data(x):
    F_list = []
    in_x_list = []
    out_x_list = []
    eta_list = []
    x_c_list = []
    y_c_list = []
    r_list = []

    for j in range(len(x)):
        F = zero[j].fun
        in_x, out_x, eta_rad = zero[j].x[0], zero[j].x[1], np.radians(zero[j].x[2])

        # chiama la funzione solo una volta
        slip_surface = circularSlipSurface.fromInOutAndEta(ground_surface, bounding_box, in_x, out_x, eta_rad)
        x_c, y_c, r = slip_surface.center[0], slip_surface.center[1], slip_surface.radius

        # Aggiunta ai risultati
        F_list.append(F)
        in_x_list.append(in_x)
        out_x_list.append(out_x)
        eta_list.append(np.degrees(eta_rad))  # convertiamo di nuovo in gradi per leggibilità
        x_c_list.append(x_c)
        y_c_list.append(y_c)
        r_list.append(r)

    # Costruzione del DataFrame
    res = pd.DataFrame({
        'F': F_list,
        'x_in (m)': in_x_list,
        'x_out (m)': out_x_list,
        'eta (°)': eta_list,
        'x_c (m)': x_c_list,
        'y_c (m)': y_c_list,
        'r (m)': r_list
    }, index=x)

    res.index.name = 'beta (°)'
    
    norm_res = pd.DataFrame({
        'F/tan(phi)': F_list/np.tan(np.radians(phi)),
        'X_in (-)': np.array(in_x_list)/slope_height,
        'x_out (-)': np.array(out_x_list)/slope_height,
        'eta (°)': eta_list,
        'X_c (-)': np.array(x_c_list)/slope_height,
        'Y_c (-)': np.array(y_c_list)/slope_height,
        'R (-)': np.array(r_list)/slope_height
        }, index=x)
    norm_res.index.name = 'beta (°)'
    return res , norm_res


real_data = res_data(beta)[0]
norm_data = res_data(beta)[1]


real_data['F'].plot()

with pd.ExcelWriter("Bishop_purely cohesive.xlsx" ) as writer: #first iter
    real_data.to_excel(writer, sheet_name='real data')
    norm_data.to_excel(writer, sheet_name='norm data')
