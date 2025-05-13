# -*- coding: utf-8 -*-
"""
Created on 2025-03-04

@author: Leonardo Lalicata, Andrea Bressan

Bishop limit equilibrium method
"""

import scipy.optimize as optimize
import numpy as np
import base_classes as bc


def bishop (geometry, soil_properties, soil_state, options):
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

    # scipy.optimize.newton uses the secant method if not provided with the 
    # derivative of the cost function. This is what happens here
    return bc.Result(
        factor_of_safety = optimize.newton(
            func=FO_m, x0=Fellenius_result,
            tol=options.tolerance,
            maxiter=options.max_iteration
            ),
        nodes=np.vstack((x_nodes,y_nodes)),
        depths=geometry.ground_surface(x_nodes)-y_nodes,
        weight_forces=w*quad.weights,
        resisting_forces=R,
        inter_slice_forces=np.zeros((2,len(x_nodes))),
        inputs=(geometry, soil_properties, soil_state, options)
        )

