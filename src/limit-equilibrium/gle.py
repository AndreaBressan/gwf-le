# -*- coding: utf-8 -*-
"""
Created on 2025-05-20

@author: Leonardo Lalicata, Andrea Bressan

general limit equilibrium methods
"""

import scipy.optimize as optimize
import numpy as np
import base_classes as bc
from slices_data import slices_data 
from bishop import bishop_with_tuple


def morgerstern_price(geometry, soil_properties, soil_state, options):
    L=np.abs(geometry.landslide_interval[0]-geometry.landslide_interval[1])
    return gle(geometry, soil_properties, soil_state, options, lambda x : np.sin(np.pi*x/L ), "Morgestern-Price")


def spencer(geometry, soil_properties, soil_state, options):
    return gle(geometry, soil_properties, soil_state, options, lambda x : 1, "Spencer")



def gle (geometry, soil_properties, soil_state, options, f, name="GLE with given f"):
    """
    Inputs:

    geometry is a class with entries
        - ground_surface, a map x to y
        - slip_surface, a map x to y
        - bounding_box
    soil_properties is a class with entries
        - cohesion
        - friction_angle (degree)
        - dry_density
        _ porosity
        _ grain_density
        all are maps (x,y) to a real number
    soil_state is a class
        _ saturation
        _ pore_pressure
        _ integrated_density
        all are maps (x,y) to a real number
    options
        _ max_iteration
        _ tolerance
        _ quadrature
            _ weights ( horizontal slice  width  )
             _ nodes   ( slice base middle points )
            more generally any quadrature

    Outputs:

    results a class with entries
        _ factor_of_safety (scalar)
        _ nodes            2xn matrix
        _ depths
        _ weight_forces
        _ resisting_forces
        _ inter_slice_forces
        - program inputs
    """

    T=slices_data (geometry, soil_properties, soil_state, options)
    I=(geometry, soil_properties, soil_state, options)
    (x_nodes,y_nodes,t_nodes,l_nodes,
     cos,sin,
     tan_phi,
     u,w,c,depth,
     quad_weights)=T

    res_bishop= bishop_with_tuple(T,I)
    FoS_Bishop=res_bishop.factor_of_safety

    f_x=f(x_nodes)
    p=w*cos
    S=(c + ( p - u ) * tan_phi)*quad_weights
    O=w*sin*quad_weights
    Osum=np.sum(O,0)
    
    def F_GLE (x):
        m_alpha = cos * (1+ tan_phi * t_nodes / x[0])
        m_alpha = np.maximum(m_alpha,0.2)
        m_alpha_star = sin - cos * tan_phi / x[0] 

        Q = x[1]*f_x
        den = (m_alpha + m_alpha_star* Q)
        p =( w - ( sin - cos*Q ) * ( c - u*tan_phi ) / x[0] ) / den
        s = c + ( p - u ) * tan_phi
        nonlocal S
        S=s*quad_weights
        P=np.maximum(p*quad_weights,0)                           # force normal to the slice always compressive
        dE = P*sin - S*cos/x[0]                                  # increment in the normal force at the side of the slices
        E  = np.maximum(np.cumsum(dE), 1.e-6)                    # normal force at the side of each slice, oriented as x_nodes, always compressive
        """
        Leonardo: 21/11/2025
        BUG to FIX
        c_vert è la risultante della coesione lungo il lato verticale della striscia
        serve per calcolare la massima resistenza a taglio lungo questa superficie: c_vert + E*tan_phi
        
        se il mezzo è multi strato, ovvero se c e phi cambiano con la profondità allora l'espressione:
            c_vert + E*tan_phi
        deve essere modificata perchè ne c_vert ne phi sono necessariamente i valori alla base della striscia
        se la striscia attraversa 2 o più strati di terreno, non è banale capire sia il valore corretto da assegnare
        a c_vert e phi per questo calcolo
        
        in via conservativa propongo
        di considerare i valori minimi di c_vert e phi lungo l'allineamento verticale
        
        """
        c_vert = c/l_nodes*depth                                 # cohesion along the height of the slice
        X  = np.minimum(Q*E , c_vert + E*tan_phi)                # shear force at the side of each slice, limited by the strength of the material
        Q_check = X/E

        rot_FoS   = (np.sum(S)/Osum - x[0])
        trasl_FoS = (np.sum(S * cos)/np.sum(P * sin) - x[0])
        if np.any(Q>Q_check):
            return [np.inf, np.inf]
        else:
            return [rot_FoS,trasl_FoS]

    """
    Leonardo: 21/11/2025
    Lambda (x[1]) non può essere negativo, con Simone abbiamo visto che
    M&P non funziona se Lambda<0.
    Abbiamo provato:
        - inserire dei bounds in roots (cambiando funzione)
        - mettere un if nella F_GLE per escludere valori negativi
    entrambe le strategie non hanno funzionato.    
    
    il problema si corregge aumentando il numero delle strisce,
    perchè evidentemente l'equilibrio locale delle strisce è troppo sbilanciato
    se la discretizzazione (numero delle striscie) è "troppo" grossolana
    variabili: (de, E, X, Q)
    
    forse si potrebbe inserire un warning del tipo:
        se Lambda<0:
            'invalid solution, increase the number of slices'
        
        che ne pensi Andrea? ti vengono in mente soluzioni migliori?
    """
    Lambda=0.3
    root=optimize.root(
            fun=F_GLE, x0=[FoS_Bishop, Lambda],
            tol=options.tolerance
            )
    return bc.Result(
        method=name,
        factor_of_safety = root.x[0],
        Lambda = root.x[1],
        nodes=np.vstack((x_nodes,y_nodes)),
        depths=geometry.ground_surface(x_nodes)-y_nodes,
        weight_forces=w*quad_weights,
        resisting_forces=S,
        inter_slice_forces=np.zeros((2,len(x_nodes))),
        inputs=(geometry, soil_properties, soil_state, options)
        )

