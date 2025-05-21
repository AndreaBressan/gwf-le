# -*- coding: utf-8 -*-
"""
Created on 2025-05-20

@author: Leonardo Lalicata, Andrea Bressan

general limit equilibrium methods
"""

import scipy.optimize as optimize
import numpy as np
import base_classes as bc


def morgerstern_price(geometry, soil_properties, soil_state, options):
    L=np.abs(geometry.landslide_interval[0]-geometry.landslide_interval[1])
    return gle(geometry, soil_properties, soil_state, options, lambda x : np.sin(np.pi*x/L ))


def spencer(geometry, soil_properties, soil_state, options):
    return gle(geometry, soil_properties, soil_state, options, lambda x : 1)



def gle (geometry, soil_properties, soil_state, options, f):
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

    quad=options.quadrature(geometry.landslide_interval)
    #"geometric properties"
    x_nodes=quad.nodes
    y_nodes=geometry.slip_surface(x_nodes)
    t_nodes=geometry.slip_tangent(x_nodes)
    l_nodes=np.sqrt(1+t_nodes**2)
    cos=1/l_nodes
    sin=np.sqrt(1-cos**2)*np.sign(t_nodes)
    #"soil properties" 
    tan_phi=np.tan(np.radians(soil_properties.friction_angle(x_nodes,y_nodes)))
    #"pressures" 
    u=soil_state.pore_pressure(x_nodes,y_nodes)*soil_state.saturation(x_nodes,y_nodes)*l_nodes
    w=soil_state.integrated_density(x_nodes,y_nodes)
    c=soil_properties.cohesion(x_nodes,y_nodes)*l_nodes
    p=w*cos  #"Fellenius method to init iteration of the Bishop method

    R=(c+(p-u)*tan_phi)*quad.weights
    O=w*sin*quad.weights
    Osum=np.sum(O,0)
    Fellenius_result=np.sum(R,0)/Osum

    #"start iteration of Bishop method"
    def FO_m(old_fos):
        m_alpha = cos * (1+1/old_fos * tan_phi * t_nodes)
        m_alpha = np.maximum(m_alpha,0.2)
        p=1/m_alpha*(w-1/old_fos*sin*(c-u*tan_phi))
        nonlocal R
        R=(c+(p-u)*tan_phi)*quad.weights
        increment = old_fos - np.sum(R,0)/Osum
        return increment

    FoS_Bishop = optimize.newton(
            func=FO_m, x0=Fellenius_result,
            tol=options.tolerance,
            maxiter=options.max_iteration
            )
    
    
    

    # TODO evaluate add the following to the output of Bishop
    # R1=bishop(geometry, soil_properties, soil_state, options)
    #x_nodes=quad.nodes
    #y_nodes=geometry.slip_surface(x_nodes)
    #t_nodes=geometry.slip_tangent(x_nodes)
    #l_nodes=np.sqrt(1+t_nodes**2)
    #u=soil_state.pore_pressure(x_nodes,y_nodes)*soil_state.saturation(x_nodes,y_nodes)*l_nodes
    #w=soil_state.integrated_density(x_nodes,y_nodes)
    #c=soil_properties.cohesion(x_nodes,y_nodes)*l_nodes
    #cos=1/l_nodes
    #sin=np.sqrt(1-cos**2)*np.sign(t_nodes)
    #tan_phi=np.tan(np.radians(soil_properties.friction_angle(x_nodes,y_nodes)))

    f_x=f(x_nodes)
    
    def F_GLE (x):
        m_alpha = cos * (1+1/x[0] * tan_phi * t_nodes)
        m_alpha = np.maximum(m_alpha,0.2)
        m_alpha_star = sin - cos /x[0] * tan_phi
        Q = x[1]*f_x
        den = 1 / (m_alpha + m_alpha_star* Q)
        P = den * (w - 1/x[0] * (sin - cos* Q) *(c - u*tan_phi))
        fric = ( P - u ) * tan_phi
        S = c + fric

        rot_FoS   = (np.sum(S)/Osum - x[0])
        trasl_FoS = (np.sum(S * cos)/np.sum(P * sin) - x[0]) 
        
        x[1] = np.maximum(x[1],1.)
        x[1] = np.minimum(x[1],0.)
        print(x)
        return [rot_FoS,trasl_FoS]


    Lambda=0.0
    root=optimize.root(
            fun=F_GLE, x0=[FoS_Bishop, Lambda],
            tol=options.tolerance
            )
    return bc.Result(
        factor_of_safety = root.x[0],
        nodes=np.vstack((x_nodes,y_nodes)),
        depths=geometry.ground_surface(x_nodes)-y_nodes,
        weight_forces=w*quad.weights,
        resisting_forces=R,
        inter_slice_forces=np.zeros((2,len(x_nodes))),
        inputs=(geometry, soil_properties, soil_state, options,root.x[1])
        )

