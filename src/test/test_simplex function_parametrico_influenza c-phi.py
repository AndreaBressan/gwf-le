import numpy as np
import pandas as pd
import sys
sys.path.append("../LEM")
from base_classes import SoilProperties,SoilState,UniformQuadrature,Options,np,plt
from bishop import bishop
from slices_data import slices_data
from gle import spencer,morgerstern_price
from gridOfCircles import GridOptions, gridComputation,computeEtaMinForSurface
from gridSimplexComputation import simplexComputation
from circularSlipSurface import circularSlipSurface
import scipy.optimize as optimize
import time

# Aggiunta da Leo: così funziona
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 300

# parametrizzo la geometria e le bounding box in funzione dell'angolo
# beta = np.arange(15, 95 , 5)
beta = 70
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

# parametro del matriale
M = np.round(np.concatenate((np.linspace(0 , 0.2 , 21),
                             np.linspace(.3, 1 , 8),
                             np.linspace(2 , 6 , 5) ,
                             np.array([8 , 10 , 15 , 20 , 30 , 60 , 100 , 200])))
             , 3) # parametro adimensionale che lega coesione ad angolo d'attrito e geometria
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

time_start=time.perf_counter()
bounds = ((1*slope_base,5*dist_max+slope_base) ,
          (-5*dist_max,1/4*slope_base) , 
          (0., 90))
  
zero=[]
calls=[]
end_geo=[]
for j in range(len(M)):
    soil_properties=SoilProperties( 
        cohesion       = lambda x,y : M[j] * constant_dry_density * slope_height * np.tan(np.radians(phi))*np.ones_like(x+y),
        friction_angle = lambda x,y : phi*np.ones_like(x+y),
        dry_density    = lambda x,y : constant_dry_density*np.ones_like(x+y),
        porosity       = lambda x,y : 0.0*np.ones_like(x+y),
        grain_density  = lambda x,y : 0.0*np.ones_like(x+y)
        )
    
    [l_zero , l_calls ] = simplexComputation(bishop, ground_surface, bounding_box, soil_properties, soil_state, gOptions,mOptions, bounds) 
    zero.append(l_zero)
    calls.append(l_calls)
    # print(f'M={M[j]:.3f},', f'F/tan(phi)={zero[j].fun/np.tan(np.radians(phi)):.3f}')
    end_geo.append(circularSlipSurface.fromInOutAndEta(ground_surface,bounding_box,zero[j].x[0],zero[j].x[1],np.radians(zero[j].x[2])))
#    print(f'Eta = {np.degrees(zero[j].x[2]):.2f}, Eta_min = {np.degrees(computeEtaMinForSurface(ground_surface,bounding_box,zero[j].x[0],zero[j].x[1])):.2f}')
    # print(f'Diff = {zero[j].x-trial}')
    # print(f'M={M[j]:.2f}' , zero[j].x[2])
    print(f'M={M[j]:.2f} : after-optimization-FOS={zero[j].fun:.3f}, using {calls[j]:d} evaluations')
    


time_duration = time.perf_counter()- time_start
print(f'\nThe simplex method took {time_duration:.3f}s per start, {time_duration:.3f}s in total')


# Print ending cases
plt.figure()
end_geo[0].plot(300,x_cm=10)
for j in range(0,len(M)):
    end_geo[j].plotSlipSurface(200)

plt.show()
plt.savefig('simplex_ending_geometries.svg')
plt.close()


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

    res.index.name = 'M'
    
    norm_res = pd.DataFrame({
        'F/tan(phi)': F_list/np.tan(np.radians(phi)),
        'X_in (-)': np.array(in_x_list)/slope_height,
        'x_out (-)': np.array(out_x_list)/slope_height,
        'eta (°)': eta_list,
        'X_c (-)': np.array(x_c_list)/slope_height,
        'Y_c (-)': np.array(y_c_list)/slope_height,
        'R (-)': np.array(r_list)/slope_height
        }, index=x)
    norm_res.index.name = 'M'
    return res , norm_res


real_data = res_data(M)[0]
norm_data = res_data(M)[1]

# Crea la figura e gli assi
fig, ax1 = plt.subplots()

# Primo asse y (sinistro)
norm_data[['X_in (-)', 'x_out (-)']].plot(ax=ax1)
ax1.set_ylabel('X_in, x_out')
ax1.set_ylim(0, 1)  # Limiti asse sinistro

# Secondo asse y (destro)
ax2 = ax1.twinx()
norm_data['eta (°)'].plot(ax=ax2, style='g-', label='eta (°)')
ax2.set_ylabel('eta (°)')
ax2.set_ylim(0, 90)  # Limiti asse destro

# Gestione legende (combinate senza 'right')
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc='best')


#limiti
ax1.set_xlim(0,10)
ax1.set_ylim(-0.5,2)
ax2.set_ylim(0,100)

plt.show()
plt.close()

# Crea la figura e gli assi
fig, ax = plt.subplots()

# Primo asse y (sinistro)
norm_data['F/tan(phi)'].plot(ax=ax, label=f'{beta:.0f}°')
ax.set_ylabel('F')


# # Gestione legende (combinate senza 'right')
# h1, l1 = ax1.get_legend_handles_labels()
# h2, l2 = ax2.get_legend_handles_labels()
# ax1.legend(h1 + h2, l1 + l2, loc='best')


#limiti
ax.set_xlim(0,10)
ax.set_ylim(0,50)

plt.show()
plt.close()

# with pd.ExcelWriter(f"Bishop={beta:.0f}°.xlsx" ) as writer:
#     real_data.to_excel(writer, sheet_name='real data')
#     norm_data.to_excel(writer, sheet_name='norm data')

#%%
"""
analyse frictional and cohesive components
"""
F_list = []
F_c_list = []
F_phi_list = []
F_cohesion_list = []
F_friction_list = []

for j in range(len(M)):
    # separo il contributo della parte attritiva e di quella coesiva dall'analisi completa
    soil_properties=SoilProperties( 
        cohesion       = lambda x,y : M[j] * constant_dry_density * slope_height * np.tan(np.radians(phi))*np.ones_like(x+y),
        friction_angle = lambda x,y : phi*np.ones_like(x+y),
        dry_density    = lambda x,y : constant_dry_density*np.ones_like(x+y),
        porosity       = lambda x,y : 0.0*np.ones_like(x+y),
        grain_density  = lambda x,y : 0.0*np.ones_like(x+y)
        )
    circle = circularSlipSurface.fromInOutAndEta(ground_surface,bounding_box,zero[j].x[0],zero[j].x[1],np.radians(zero[j].x[2]))
    bishopp = bishop(circle, soil_properties, soil_state, mOptions)

    F = bishopp.factor_of_safety
    C = bishopp.resisting_cohesive.sum()
    PHI = bishopp.resisting_frictional.sum()
    TOT = bishopp.resisting_forces.sum()
    A = bishopp.weight_forces.sum()
    
    # Aggiunta ai risultati
    F_list.append(F)
    F_c_list.append(C/A)
    F_phi_list.append(PHI/A)
    
    # cohesion = soil_properties.cohesion(0,0)
    # friction_angle = phi
    # # Analisi solo coesiva (phi=0) per la sds critica dell'analisi completa
    # cohesion_only=SoilProperties( 
    #     cohesion       = lambda x,y : cohesion*np.ones_like(x+y),
    #     friction_angle = lambda x,y : 0*friction_angle*np.ones_like(x+y),
    #     dry_density    = lambda x,y : constant_dry_density*np.ones_like(x+y),
    #     porosity       = lambda x,y : 0.0*np.ones_like(x+y),
    #     grain_density  = lambda x,y : 0.0*np.ones_like(x+y)
    #     )
    # F_cohesion = bishop(circle, cohesion_only, soil_state, mOptions).factor_of_safety
    # F_cohesion_list.append(F_cohesion)

    # # Analisi solo attritiva (c=0) per la sds critica dell'analisi completa
    # friction_only=SoilProperties( 
    #     cohesion       = lambda x,y : 0*cohesion*np.ones_like(x+y),
    #     friction_angle = lambda x,y : friction_angle*np.ones_like(x+y),
    #     dry_density    = lambda x,y : constant_dry_density*np.ones_like(x+y),
    #     porosity       = lambda x,y : 0.0*np.ones_like(x+y),
    #     grain_density  = lambda x,y : 0.0*np.ones_like(x+y)
    #     )
    # F_friction = bishop(circle, friction_only, soil_state, mOptions).factor_of_safety
    # F_friction_list.append(F_friction)

    
risultati = pd.DataFrame({'F'  : F_list,
                          'F_c': F_c_list,
                          'F_phi': F_phi_list,
                          # 'F_cohesion only': F_cohesion_list,
                          # 'F_friction only': F_friction_list
                          },
                         index=M
                         )
risultati.index.name = 'M'
tan_phi = np.tan(np.radians(soil_properties.friction_angle(0,0)))
risultati_norm = risultati/tan_phi


rapporti = pd.DataFrame([risultati[e]/risultati['F'] for e in risultati.columns],
                        columns= risultati.index,
                        index=risultati.columns).T

# risultati['errore (%)'] = (1 - (risultati['F_cohesion only'] + risultati['F_friction only'])/risultati['F'])*100




with pd.ExcelWriter(f"Analisi c-phi={beta:.0f}°.xlsx" ) as writer:
    risultati.to_excel(writer, sheet_name='actual F values')
    risultati_norm.to_excel(writer, sheet_name='F_tan(phi)')
    rapporti.to_excel(writer, sheet_name='cohesive and fric ratio')