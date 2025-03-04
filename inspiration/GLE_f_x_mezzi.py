# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 10:50:35 2022

@author: Leonardo

    metodo di Bishop per terreno coesivo attritivo
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.optimize as optimize
from Geometry import geometry
from Geometry import SlopeHeigth
from Geometry import SlopeAngle

# from Grid import grid
# from Grid import soilsurface

from VanGenutchten import VG

##----------------------------------------------------------------------------#
def GLE(Ns , xa , ya , Ra , sds_in , sds_out , gamma , gamma_unsat , c , phi_rad, gammawater , P , N , Sr_res , alpha , wtdepth):
    """
    GLE : General Limit Equilibrium
    dovrebbe fare tutti i metodi insieme
    xa , ya , Ra = centro e raggio sds
    sds_in , sds_out = ingresso e uscita sds (solo ascissa) 
    gamma = peso totale terreno
    c , phi_rad = coesione e angolo d'attrito
    gammawater = peso specifico acqua
    """
    """
     SLICES
     
         25 slices     
    """
    # print(wtdepth)
    """
    0) Metodo generale:
        solo sds circolari
        definizioni:
            C : c*l
            U : u*l
            S : C + (P-U)*tan(phi)
            Fm : equilibrio momenti globale
            Ff : equilibrio forze globale
            Fm : sum(S) / sum(W*sen(alpha))
            Ff : sum(S*cos(alpha)) / sum(P*sen(alpha))
            
            m_a (m,f) : cos(alpha)*(1+ 1/F *tan(alpha)*tan(phi))
            P (m,f) : 1/m_a * (W - (Xr-Xl) - 1/F * (C*sen(alpha) + U*sen(alpha)*tan(phi)))
            
            El, Er : forze di interstriscia Normali left, right
            Xl, Xr : forze di interstriscia tangenziali " , "
            X = lambda*f(x)*E
    """
    """
    1) definisco la geometria delle strisce
    """
    soilsurface = geometry(SlopeHeigth , SlopeAngle)[-1]
    counter = np.linspace(1 , Ns , Ns)
    Ndivs = Ns   
    ##----------------------------------------------------------------------------#
    x_l = (sds_out + (counter - 1) * np.abs(sds_in - sds_out)/Ndivs)
    x_r = (sds_out + (counter ) * np.abs(sds_in - sds_out)/Ndivs)
    
    y_l_top = np.ones(len(counter)) * soilsurface.loc['A'][1]
    y_r_top = y_l_top
    
    m = x_l > soilsurface.loc['A'][0]
    y_l_top[m] = x_l[m] * np.tan(np.radians(SlopeAngle))
    m2 = x_l > soilsurface.loc['B'][0]
    y_l_top[m2] = soilsurface.loc['B'][1]
    
    m = x_r > soilsurface.loc['A'][0]
    y_r_top[m] = x_r[m] * np.tan(np.radians(SlopeAngle))
    m2 = x_r > soilsurface.loc['B'][0]
    y_r_top[m2] = soilsurface.loc['B'][1]      
        
    s = pd.DataFrame({'x_l': x_l , 'x_r': x_r , 'y_l_top' : y_l_top , 'y_r_top' : y_r_top}) 

    slices = s

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
    
    """
    distribuzione delle azioni di interstriscia
    """
    L = abs(slices['x_r'].max() - slices['x_l'].min())
    def fx(x):
        # fx = np.sin(np.pi*x/L)  # Morgenstern & Price
        fx = 1                  # Spencer
        return  fx

    """
    2) Calcolo Fm OMS (Orinary Method of slice) i.e. Fellenius
        si fa per calcolare il valore iniziale delle iterazioni
        metodo diretto
    """    
    slices['l.arm'] =  np.sin(slices['theta'])
    # pore pressure
    # slices['por [kPa]'] = 0
    # occhio che è il grado di saturazione efficace
    slices['Sr'] = 1
    slices['por [kPa]'] = -( slices['y_middle_bot'] - wtdepth )* gammawater
    mask = slices['por [kPa]'] < 0
    slices['Sr'] = slices['Sr'].mask(mask,
                          other = VG( s =  -slices['por [kPa]'] , P=P , N=N , Sr_res=Sr_res, alpha=alpha) ,
                          axis = 0)
    
    slices['U'] = slices['slicebase_inclined']  * slices['por [kPa]'] * slices['Sr']
    # calcolo gamma medio sulla striscia
    g_avg = []
    for i in range(len(slices)):
        h = np.linspace(slices['y_middle_bot'][i] , slices['y_middle_top'][i] , 11)
        u = -( h - wtdepth )* gammawater
        # Sr = VG( s =  -u , P=P , N=N ,  Sr_res=Sr_res, alpha=alpha)
        m = u > 0
        # Sr[m] = 1
        g = np.ones(len(h))*gamma_unsat
        g[m] = gamma
        g_medio = np.mean(g)
        # g_medio = np.mean(Gs*10 / (1+e) * (1 +Sr*e/Gs))
        g_avg.append(g_medio)
        
    slices['gamma'] = g_avg
    # slices['gamma'] = gamma
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
    res = optimize.newton(FO_m, Fellenius, tol=1.e-4 , maxiter=200)
    Bishop = res
#------------------------------------------------------------------------------#
    """
    4) Jambu semplificato
        impongo lambda=0
        
        provo a calcolare Bishop con un fne obiettivo
        funziona alla grande!
    """
    def FO_f(x):
        slices['m alpha'] = np.cos(slices['theta']) * ( 1 + 1/x * np.tan(phi_rad) * np.tan(slices['theta']))
        slices['m alpha'].mask(slices['m alpha']<0.2 , 0.2 , axis=0 ,  inplace=True)
        slices['P'] = 1/slices['m alpha'] * (slices['W'] - 1/x * np.sin(slices['theta']) * (slices['C'] - slices['U'] * np.tan(phi_rad)))
        slices['fric'] = ( slices['P'] - slices['U']) * np.tan(phi_rad)
        slices['S'] = slices['C'] + slices['fric']
        #
        slices['ResForce'] = slices['S'] * np.cos(slices['theta'])
        slices['OverForce'] = slices['P'] * np.sin(slices['theta'])
        ff = x - slices['ResForce'].sum() / slices['OverForce'].sum()
        # print('Jambu' , np.round(x,5))
        return ff
    res = optimize.newton(FO_f, Fm, tol=1.e-4 , maxiter=200)
    Jambu = res
#-----------------------------------------------------------------------------#        
    """
    5) Metodo rigoroso (Spencer o Morgestern e Price a seconda di f_x)
        sistema di 2 equazioni (F da rotazione , F da traslazione) in due incognite (F, lambda)
    """
    """
     in questa versione valuto la fx a meta striscia:
         dX = dE *f(x/2)
    """
    q0=0.3
    f_x = fx(slices['x_middle'].values)

    def P(x):
        slices['Q'] = x[1]*f_x
        m_alpha = np.cos(slices['theta']) * ( 1 + 1/x[0] * np.tan(phi_rad) * np.tan(slices['theta']))
        m_alpha_star = np.cos(slices['theta']) * ( np.tan(slices['theta']) - 1/x[0] * np.tan(phi_rad) )
        DEN = 1 / (m_alpha + m_alpha_star* slices['Q'])
        P = DEN * (slices['W']
                   - 1/x[0] * slices['C'] * np.cos(slices['theta'])* (np.tan(slices['theta']) - slices['Q'])
                   + 1/x[0] * slices['U'] * np.cos(slices['theta']) * np.tan(phi_rad)* (np.tan(slices['theta']) - slices['Q']))
        return P
    
    def FoS_m(x):
        fric = ( P(x) - slices['U']) * np.tan(phi_rad)
        S= slices['C'] + fric
        resisting_moment = S
        return (np.sum(resisting_moment)/slices['OverMoment'].sum() - x[0])
    
    def FoS_f(x):
        fric = ( P(x) - slices['U']) * np.tan(phi_rad)
        S= slices['C'] + fric
        res_force = S*np.cos(slices['theta'])
        return (np.sum(res_force)/np.sum(P(x)*np.sin(slices['theta'])) - x[0]) 
    
    def FoS_func(x):
        return([FoS_m(x), FoS_f(x)])
    
    sol = optimize.root(FoS_func, [Bishop, q0])
    FoS = sol.x[0]
    lambd = sol.x[1]
    # print(sol.x)
#-----------------------------------------------------------------------------#   
    # ingresso e uscita della sds
    slipboundary = [[sds_out , min(soilsurface.loc['A'][1] , sds_out * np.tan(np.radians(SlopeAngle)))] ,
                    [sds_in , soilsurface.loc['B'][1]]]
#-----------------------------------------------------------------------------#
    slices['P'] = P(sol.x)
    slices['m alpha'] = np.cos(slices['theta']) * ( 1 + 1/FoS * np.tan(phi_rad) * np.tan(slices['theta']))
    slices['dE'] = slices['P'] * np.sin(slices['theta']) - 1/FoS*(slices['C'] + (slices['P']- slices['U']) * np.tan(phi_rad)) * np.cos(slices['theta'])
    slices['dX'] = lambd * slices['dE']
    # if slices['dE'].sum() !=0:
    #     FoS = np.nan
    # else:
    #     FoS = FoS
    return slices , slipboundary[0] , slipboundary[1] , Bishop , Jambu , FoS , lambd


# soilsurface = geometry(SlopeHeigth , SlopeAngle)[-1]
# wt = watertable(wtdepth)

# plt.plot(soilsurface['x'], soilsurface['y'] , c = 'black' , linewidth=2)
# plt.plot(wt['x'], wt['zw'] , c = 'blue' , linewidth=2)
# for i in range(len(slices)):
#     plt.plot(slices.iloc[i,[0 , 0]] ,slices.iloc[i,[2, 6]] , color = 'dimgray' ,linewidth=0.5 )
# plt.plot(slices.iloc[-1,[1 , 1]] ,slices.iloc[-1,[3, 7]] , color = 'dimgray' ,linewidth=0.5 )