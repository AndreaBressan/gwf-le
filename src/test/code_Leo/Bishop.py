# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 10:50:35 2022

@author: Leonardo

    metodo di Bishop per terreno coesivo attritivo
"""

import numpy as np
import pandas as pd
import scipy.optimize as optimize
import matplotlib.pyplot as plt

from Geometry import geometry
from Geometry import SlopeHeigth
from Geometry import SlopeAngle

# from Grid import grid
# from Grid import soilsurface

# from VanGenutchten import VG

##----------------------------------------------------------------------------#
def Bishop(Ns , xa , ya , Ra , sds_in , sds_out , gamma , c , phi_rad):
    """
    xa , ya , Ra = centro e raggio sds
    sds_in , sds_out = ingresso e uscita sds (solo ascissa) 
    gamma = peso totale terreno
    c , phi_rad = coesione e angolo d'attrito
    gammawater = peso specifico acqua
    """
    """
    1) definisco la geometria delle strisce
    """
    soilsurface = geometry(SlopeHeigth , SlopeAngle)[-1]
    counter = np.arange(1, Ns + 1) 
    
    # Estrai i punti della superficie del terreno
    x_surface = soilsurface['x'].values  # coordinata x
    y_surface = soilsurface['y'].values  # coordinata y
    
    # Interpolazione della superficie
    def interp_surface(x):
        return np.interp(x, x_surface, y_surface)
    # ##----------------------------------------------------------------------------#
    x_l = sds_out + (counter - 1) * np.abs(sds_in - sds_out) / Ns
    x_r = sds_out + counter * np.abs(sds_in - sds_out) / Ns
    
    # Calcolo della quota superiore interpolata
    y_l_top = interp_surface(x_l)
    y_r_top = interp_surface(x_r)

    slices = pd.DataFrame({'x_l': x_l , 'x_r': x_r , 'y_l_top' : y_l_top , 'y_r_top' : y_r_top}) 

    ###
    # Operazioni geometriche
    ###
    slices['x_middle'] = slices[['x_l', 'x_r']].mean(axis = 1)
    slices['y_middle_top'] = slices[['y_l_top', 'y_r_top']].mean(axis = 1)
    slices['y_l_bot'] = ya - ( Ra**2 - ( slices['x_l'] - xa )**2 )**0.5
    slices['y_r_bot'] = ya - ( Ra**2 - ( slices['x_r'] - xa )**2 )**0.5
    slices['y_r_bot'].fillna(slices['y_r_top'] , axis = 0 , inplace=True)
    # print(slices.loc[24,'y_r_bot'])
    #--------------------#
    slices['y_middle_bot'] = slices[['y_l_bot', 'y_r_bot']].mean(axis = 1)
    slices['slicebase'] = np.abs(slices['x_l']  - slices['x_r'])
    slices['sliceheight'] = slices['y_middle_top']  - slices['y_middle_bot']
    slices['theta'] = np.arctan( (slices['y_r_bot'] - slices['y_l_bot'] ) /slices['slicebase'] )
    slices['theta_deg'] = np.degrees(slices['theta'] )
    slices['slicebase_inclined'] = slices['slicebase'] / np.cos(slices['theta'])
    
    # """
    # distribuzione delle azioni di interstriscia
    # """
    # L = abs(slices['x_r'].max() - slices['x_l'].min())
    # def fx(x):
    #     fx = np.sin(np.pi*x/L)  # Morgenstern & Price
    #     # fx = 1                  # Spencer
    #     return  fx
    
    """
    2) Calcolo Fm OMS (Orinary Method of slice) i.e. Fellenius
        si fa per calcolare il valore iniziale delle iterazioni
        metodo diretto
    """    
    slices['l.arm'] =  np.sin(slices['theta'])
    # pore pressure
    slices['U'] = 0 # secco equivalente
    # slices['por [kPa]'] = -( slices['y_middle_bot'] - wtdepth )* gammawater
    # slices['U'] = slices['slicebase_inclined']  * slices['por [kPa]']
    # slices['Sr'] = 1
    
    # mask = slices['por [kPa]'] < 0
    # slices['Sr'] = slices['Sr'].mask(mask,
    #                       other = VG( s =  -slices['por [kPa]'] , se=se , n=n , Sr_res=Sr_res, alpha=alpha) ,
    #                       axis = 0)
    #
    # # calcolo gamma medio sulla striscia
    # g_avg = []
    # for i in range(len(slices)):
    #     h = np.linspace(slices['y_middle_bot'][i] , slices['y_middle_top'][i] , 11)
    #     u = -( h - wtdepth )* gammawater
    #     Sr = VG( s =  -u , se=se , n=n ,  Sr_res=Sr_res, alpha=alpha)
    #     m = u > 0
    #     Sr[m] = 1
    #     g_medio = np.mean(Gs*10 / (1+e) * (1 +Sr*e/Gs))
    #     g_avg.append(g_medio)
        
    # slices['gamma'] = g_avg
    slices['gamma'] = gamma
    #
    slices['W'] = slices['slicebase'] * slices['sliceheight'] * slices['gamma']
    slices['C'] = slices['slicebase_inclined'] * c
    slices['P'] = slices['W'] * np.cos(slices['theta'])
    slices['fric'] = ( slices['P'] - slices['U']) * np.tan(phi_rad)
    slices['S'] = slices['C'] + slices['fric']
    
    slices['ResMoment'] = slices['S'] 
    slices['OverMoment'] = slices['W'] * slices['l.arm']
    
    Fm = slices['ResMoment'].sum() / slices['OverMoment'].sum()

    Fellenius = Fm
    #------------------------------------------------------------------------------#
    """
    3) Metodo di Bishop
        impongo lambda=0
        provo a calcolare Bishop con un fne obiettivo
        funziona alla grande!
    """
    def FO_m(x):
        slices['m alpha'] = np.cos(slices['theta']) * ( 1 + 1/x * np.tan(phi_rad) * np.tan(slices['theta']))
        slices['m alpha'].mask(slices['m alpha']<0.2 , 0.2 , axis=0 ,  inplace=True)
        slices['P'] = 1/slices['m alpha'] * (slices['W'] - 1/x * np.sin(slices['theta']) * (slices['C'] - slices['U'] * np.tan(phi_rad)))
        slices['fric'] = ( slices['P'] - slices['U']) * np.tan(phi_rad)
        slices['S'] = slices['C'] + slices['fric']
        #
        slices['ResMoment'] = slices['S']
        ff = x - slices['ResMoment'].sum() / slices['OverMoment'].sum()
        # print('Bishop' , np.round(x,5))
        return ff
    res = optimize.newton(FO_m, Fellenius, tol=1.e-4 , maxiter=400)
    Bishop = res
    
    if Bishop<Fellenius:
        F = Fellenius
        method = 'Fellenius'
    else:
        F = Bishop
        method = 'Bishop'
#-----------------------------------------------------------------------------#   
    # ingresso e uscita della sds
    slipboundary = [[sds_out , min(soilsurface.loc['A'][1] , sds_out * np.tan(np.radians(SlopeAngle)))] ,
                    [sds_in , soilsurface.loc['B'][1]]]
#-----------------------------------------------------------------------------#
    return slices , slipboundary[0] , slipboundary[1] , method , F    
