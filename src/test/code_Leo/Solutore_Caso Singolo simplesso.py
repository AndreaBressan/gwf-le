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
from GLE_Bishop import GLE # solo Bishop
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
Ns = 50
#-----------------------------------------------------------------------------#
"""
Caso singolo
"""
x_in , x_out , eta = 5. , 0. , 70.
sds_in  , sds_out = [x_in , SlopeHeigth] , [x_out , 0.]
xa , ya , Ra = circ_2pts_tan(sds_in , sds_out , np.tan(np.radians(eta)))
F_singolo = GLE(Ns , xa , ya , Ra , x_in , x_out , gamma[0] , c[0] , phi_rad)[-1]
Strisce = GLE(Ns , xa , ya , Ra , x_in , x_out , gamma[0] , c[0] , phi_rad)[0]
print('Caso Singolo:' , round(F_singolo,5))


def valid(sds_in , sds_out , eta):
    if sds_out[0] >= soilsurface.loc['A','x']:
        eta_min = np.degrees(np.arctan(sds_in[1]/ sds_in[0]))
    else:
        m_perp_in_0 =  - sds_in[0]/sds_in[1]
        xc_min = 0.5 * sds_out[0]
        yc_min = sds_in[1] + m_perp_in_0 * (xc_min - sds_in[0])
        eta_min = max(np.degrees(np.arctan(- (sds_in[0]  - xc_min ) / (sds_in[1]  - yc_min ))) , 
                      np.degrees(np.arctan(sds_in[1]/ sds_in[0])))
    return eta>eta_min


def func(v):
    x_in , x_out , eta = v[0] , v[1] , v[2]

    sds_in = [x_in, SlopeHeigth]
    sds_out = [x_out, x_out * np.tan(np.radians(SlopeAngle)) if x_out > soilsurface.loc['A','x'] else soilsurface.loc['A','y']]
    func.i+=1  
    if valid(sds_in , sds_out , eta):
        xa , ya , Ra = circ_2pts_tan(sds_in , sds_out , np.tan(np.radians(eta)))
        func.chiamate+=1
        ff = GLE(Ns , xa , ya , Ra , x_in , x_out , gamma[0] , c[0] , phi_rad)[-1]
    else:
        ff = 100.
    return ff

func.i=0
func.chiamate=0
##----------------------------------------------------------------------------#
start = time.time()
##----------------------------------------------------------------------------#

nomi = ['F' , 'sds_in' , 'sds_out' , 'eta' , 'xc' , 'yc' , 'R']
A = max(SlopeHeigth , soilsurface.loc['B','x'])
# bounds = ((soilsurface.loc['B'][0]+SlopeHeigth/25*0 , 3*A) ,
#           (-3*A , soilsurface.loc['B'][0]/4) , 
#           ( grid['angolo entrata'].min(), 90.))
bounds = ((2,10) ,
          (-10,1) , 
          (0, 90))
"""
 trial: vettore prova: ascissa ingresso , ascissa uscita , angolo ingresso
 prendo quello che viene dalla griglia
"""
trial = np.array([x_in, x_out, eta])
zero = optimize.minimize(func, trial , 
                          method='Nelder-Mead' , bounds = bounds , 
                                                  options = {'disp':True  ,'xatol' : 1.e-3 , 'fatol':1.e-4 , 'maxiter':100 , 'return_all':True})
sds_in = [zero['x'][0], SlopeHeigth]
sds_out = [zero['x'][1], zero['x'][1] * np.tan(np.radians(SlopeAngle)) if zero['x'][1] > soilsurface.loc['A','x'] else soilsurface.loc['A','y']]
lista = [[zero['fun']] , list(zero['x']) , list(circ_2pts_tan(sds_in , sds_out , np.tan(np.radians(zero['x'][2]))))]
flat_list = list(np.concatenate(lista).flat)

sommario = pd.DataFrame({'1' : flat_list , 'label' : nomi})
sommario.set_index('label', inplace = True)
slices = GLE(Ns , sommario.loc['xc'].values , sommario.loc['yc'].values , sommario.loc['R'].values ,
                sommario.loc['sds_in'].values ,sommario.loc['sds_out'].values , 
                gamma[0] , c[0] , phi_rad )[0]
method = GLE(Ns , sommario.loc['xc'].values , sommario.loc['yc'].values , sommario.loc['R'].values ,
                sommario.loc['sds_in'].values ,sommario.loc['sds_out'].values , 
                gamma[0] , c[0] , phi_rad )[-2]

print('Start:' , [x_in, x_out, eta] , F_singolo)
print('end:' , zero['x'] , zero['fun'] , func.chiamate)

