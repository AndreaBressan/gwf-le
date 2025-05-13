# -*- coding: utf-8 -*-
"""
Created on Wed Mar 15 08:09:45 2023

@author: leolalicata
"""

import numpy as np
import pandas as pd
import scipy.optimize as optimize
# from scipy.optimize import show_options
import matplotlib.pyplot as plt
import matplotlib.tri as tri
from circ_2pts_tan import circ_2pts_tan
from Bishop import Bishop
from Geometry import SlopeHeigth
from Geometry import SlopeAngle
from Geometry import geometry
import time
from Grid import grid
# from VanGenutchten import VG


soilsurface = geometry(SlopeHeigth , SlopeAngle)[-1]
"""
 Soil Parameters
"""
gamma = [18. , 'kN/m3'] # saturated unit weight of soil
c = [5.0 , 'kPa'] # soil coesion
phi = [30. , 'deg'] # friction angle
phi_rad = np.radians(phi[0])
##----------------------------------------------------------------------------#
Ns = 20
#-----------------------------------------------------------------------------#
def valid(sds_in , sds_out , eta):
    if sds_out[0] >= soilsurface.loc['A'][0]:
        eta_min = np.degrees(np.arctan(sds_in[1]/ sds_in[0]))
    else:
        m_perp_in_0 =  - sds_in[0]/sds_in[1]
        xc_min = 0.5 * sds_out[0]
        yc_min = sds_in[1] + m_perp_in_0 * (xc_min - sds_in[0]) # questo era leggermenete diverso
        eta_min = max(np.degrees(np.arctan(- (sds_in[0]  - xc_min ) / (sds_in[1]  - yc_min ))) , 
                      np.degrees(np.arctan(sds_in[1]/ sds_in[0])))
    return eta>eta_min


def func(v):
    """
    so che non dovrei farlo ma non capisco come funzionano le tolleranze
    """
    # x_in , x_out , eta = np.round(v[0] , 5) , np.round(v[1] , 5) , np.round(v[2] , 5)
    x_in , x_out , eta = v[0] , v[1] , v[2]

    sds_in = [x_in, SlopeHeigth]
    sds_out = [x_out, x_out * np.tan(np.radians(SlopeAngle)) if x_out > soilsurface.loc['A'][0] else soilsurface.loc['A'][1]]
    func.i+=1  
    if valid(sds_in , sds_out , eta):
        xa , ya , Ra = circ_2pts_tan(sds_in , sds_out , np.tan(np.radians(eta)))
        func.chiamate+=1
        ff = Bishop(Ns , xa , ya , Ra , x_in , x_out , gamma[0] , c[0] , phi_rad)[-1]
        # slices = Bishop(Ns , xa , ya , Ra , x_in , x_out , gamma[0] , c[0] , phi_rad)[0]
    else:
        ff = 30.
    # print('F: ' , ff , 'trial: ' , v)
    return ff

func.i=0
func.chiamate=0
# func([3.1111908868992098 , -0.0006803238741459544 , 90.0])
# func([3.1116096013399694 , -0.0006786536772452427 , 90.0])
##----------------------------------------------------------------------------#
start = time.time()
"""
 griglia lasca
"""
grid = grid()
xa , ya , Ra , sds_in , sds_out = grid['xc'] , grid['yc'] ,grid['Radius'] , grid['sds in'], grid['sds out']
            
FoS = [Bishop(Ns , xa[i] , ya[i] , Ra[i] ,sds_in[i] ,sds_out[i] , 
              gamma[0] , c[0] , phi_rad )[-1] for i in range(len(grid))]  
FS = FoS
##----------------------------------------------------------------------------#
grid['Safety Factor'] = FS
grid = grid.dropna(how='all')
grid = grid.mask(grid['Safety Factor'] < 0).dropna()
grid = grid.mask(grid['Safety Factor'] > 10).dropna()
FactorofSafety = min(grid['Safety Factor'])
mask = FactorofSafety

grid.set_index('Safety Factor' , inplace = True)
grid = grid.sort_index()
##----------------------------------------------------------------------------#

nomi = ['F' , 'sds_in' , 'sds_out' , 'eta' , 'xc' , 'yc' , 'R']
A = max(SlopeHeigth , soilsurface.loc['B'][0])
bounds = ((soilsurface.loc['B'][0]+SlopeHeigth/25*0 , 3*A) ,
          (-3*A , soilsurface.loc['B'][0]/4) , 
          ( grid['angolo entrata'].min(), 90.))
"""
 trial: vettore prova: ascissa ingresso , ascissa uscita , angolo ingresso
 prendo quello che viene dalla griglia
"""
trial = np.array([grid.loc[mask,'sds in'] , grid.loc[mask,'sds out'] , grid.loc[mask,'angolo entrata']])
# trial = [ 3.5 , 0  , 90]
zero = optimize.minimize(func, trial , 
                          method='Nelder-Mead' , bounds = bounds , 
                                                  options = {'disp':True  ,'xatol' : 1.e-2 , 'fatol':0.01 , 'maxiter':100 , 'return_all':True})
sds_in = [zero['x'][0], SlopeHeigth]
sds_out = [zero['x'][1], zero['x'][1] * np.tan(np.radians(SlopeAngle)) if zero['x'][1] > soilsurface.loc['A','x'] else soilsurface.loc['A','y']]
lista = [[zero['fun']] , list(zero['x']) , list(circ_2pts_tan(sds_in , sds_out , np.tan(np.radians(zero['x'][2]))))]
flat_list = list(np.concatenate(lista).flat)

sommario = pd.DataFrame({'1' : flat_list , 'label' : nomi})
sommario.set_index('label', inplace = True)
slices = Bishop(Ns , sommario.loc['xc'].values , sommario.loc['yc'].values , sommario.loc['R'].values ,
                sommario.loc['sds_in'].values ,sommario.loc['sds_out'].values , 
                gamma[0] , c[0] , phi_rad )[0]
method = Bishop(Ns , sommario.loc['xc'].values , sommario.loc['yc'].values , sommario.loc['R'].values ,
                sommario.loc['sds_in'].values ,sommario.loc['sds_out'].values , 
                gamma[0] , c[0] , phi_rad )[-2]
#%%
# sommario = pd.DataFrame((b))
# sommario.columns = nomi
end = time.time()
print("The time of execution of the loop is :", end-start)
print("----")
print("the Safety Factor is :", float(sommario.loc['F']))
print("----")
print("Method :", method)
StabNum = (gamma[0]*SlopeHeigth) / c[0]
x_Steward = 1/StabNum * 1/float(sommario.loc['F'])
y_Steward = np.tan(phi_rad) * 1/float(sommario.loc['F'])
limite_sup = 1/StabNum * 1/np.tan(phi_rad)
print("----")
print("Numero Stabilità:", format((StabNum) , '.2f') , "; c/gH * 1/F :" , format(x_Steward , '.2f') , "; tan(phi) /F :" , format(y_Steward , '.2f'))
print("----")
print("----")
print("limite sup:", format(limite_sup , '.4f') )
print("----")
# #%%
#----------------------------------------------------------------------------#
teta = np.arange(0 , 361 , 0.1)
tetarad = np.radians(teta)
#----------------------------------------------------------------------------#
"""
  PLOT
"""
fsText = ' $Simplesso=$'+\
    str(format(float(sommario.loc['F']), '.3f'))
fsText_griglia = ' $FoS=$'+\
    str(format(float(grid.index.min()), '.3f'))

plt.figure(1)
plt.title('Bishop Method')
plt.axis('equal')
# plt.xlim(-15 , 15)
# plt.ylim(-5 , 25)
plt.xlabel('$x$ distance')
plt.ylabel('$y$ distance')
plt.plot(soilsurface['x'], soilsurface['y'] , c = 'black' , linewidth=2)

plt.text(soilsurface.loc['B','x'], 1.5*SlopeHeigth , fsText , fontsize = 11 , color='red')
plt.text(soilsurface.loc['B','x'], 2*SlopeHeigth , fsText_griglia , fontsize = 11 , color = 'blue')
# Plot SF contours
# x = grid['xc']
# y = grid['yc']
# triang = tri.Triangulation(x, y)
# plt.tricontour(triang, grid.index, 10, linewidths=0.15, colors='k')
# plt.tricontourf(triang, grid.index, 10, cmap=plt.cm.jet_r)
# plt.colorbar(aspect=30, orientation='horizontal', format='%.1f')
# Plot Slices
# for i in range(len(slices)):
#     plt.plot(slices.iloc[i,[0 , 0]] ,slices.iloc[i,[2, 6]] , color = 'dimgray' ,linewidth=0.5 )
# plt.plot(slices.iloc[-1,[1 , 1]] ,slices.iloc[-1,[3, 7]] , color = 'dimgray' ,linewidth=0.5 )
"""
    Slip Surface
"""
"""
 critical circle
"""
xa , ya , Ra  = (float(sommario.loc['xc']) , float(sommario.loc['yc']) , float(sommario.loc['R']))
xcirc = xa + Ra * np.sin(tetarad)
ycirc = ya + Ra * np.cos(tetarad)
Circ = pd.DataFrame({'xcirc': xcirc , 'ycirc': ycirc} ,  index=teta )
"""
  define the slipboudaries for plotting
"""
slipboundary = [float(sommario.loc['sds_out']) , float(sommario.loc['sds_in'])]
maskk = (Circ['xcirc'] < slipboundary[0]) | (Circ['xcirc'] > slipboundary[1]) | (Circ['ycirc'] >= SlopeHeigth + 0.1)
Circ = Circ.mask(maskk).dropna()
plt.plot(Circ['xcirc'], Circ['ycirc'], c = 'red', linewidth=1)
# plt.plot(xa , ya , marker = 'o' , c = 'black')
#
"""
 critical circle griglia
"""
xa , ya , Ra  = (float(grid.loc[mask,'xc']) , float(grid.loc[mask,'yc']) , float(grid.loc[mask,'Radius']))
xcirc = xa + Ra * np.sin(tetarad)
ycirc = ya + Ra * np.cos(tetarad)
Circ = pd.DataFrame({'xcirc': xcirc , 'ycirc': ycirc} ,  index=teta )
"""
  define the slipboudaries for plotting
"""
slipboundary = [float(grid.loc[mask,'sds out']) , float(grid.loc[mask,'sds in'])]
maskk = (Circ['xcirc'] < slipboundary[0]) | (Circ['xcirc'] > slipboundary[1]) | (Circ['ycirc'] >= SlopeHeigth + 0.1)
Circ = Circ.mask(maskk).dropna()
plt.plot(Circ['xcirc'], Circ['ycirc'], c = 'blue', linewidth=1)
# plt.plot(xa , ya , marker = 'o' , c = 'blue')


# plt.savefig('beta=30°_confronto_simplesso.png' , dpi=300 , bbox_inches='tight')