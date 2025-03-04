# -*- coding: utf-8 -*-
"""
Created on 2025-03-04

@author: Leonardo Lalicata, Andrea Bressan

Bishop limit equilibrium method
"""

import scipy.optimize as optimize
import numpy as np


def bishop (geometry, soil_properties, soil_state, quadrature, options):
    """
    Inputs:

    geometry is a dictionary with entries
        - ground_surface, a map x to y
        - slip_surface, a map x to y
        - bounding_box
    soil_properties is a dictionary with entries
        - cohesion
        - friction_angle
        - dry_density
        _ porosity
        _ grain_density
        all are maps (x,y) to a real number
    soil_state is a dictionary
        _ saturation
        _ pore_pressure
        _ integrated_density
        all are maps (x,y) to a real number
    quadrature
        _ weights ( horizontal slice  width  )
        _ nodes   ( slice base middle points )
        more generally any quadrature
    options
        _ max_iteration
        _ tolerance

    Outputs:

    results a dictionary with entries
        _ factor_of_safety (scalar)
        _ nodes            2xn matrix
        _ depths
        _ weight_forces
        _ resisting_forces
        _ inter_slice_forces
    """

    #"geometric properties"
    x_nodes=quadrature.nodes
    y_nodes=geometry.slip_surface.value(x_nodes)
    t_nodes=geometry.slip_surface.derivative(x_nodes)
    l_nodes=np.sqrt(1+t_nodes**2)
    cos=1/l_nodes
    sin=np.sqrt(1-cos**2)
    #"soil properties" 
    tan_phi=np.tan(np.radians(soil_properties.friction_angle(x_nodes,y_nodes)))
    #"pressures" 
    u=soil_state.pore_pressure(x_nodes,y_nodes)*soil_state.saturation(x_nodes,y_nodes)*l_nodes
    w=soil_state.integrated_density(x_nodes,y_nodes)
    c=soil_properties.cohesion(x_nodes,y_nodes)*l_nodes
    p=w*cos  #"Fellenius method to init iteration of the Bishop method

    R=(c+(p-u)*tan_phi)*quadrature.weights
    O=w*sin*quadrature.weights
    Osum=np.sum(O,1)
    Fellenius_result=np.sum(R,1)/Osum

    #"start iteration of Bishop method"
    def FO_m(old_fos):
        m_alpha = cos * (1+1/old_fos * tan_phi * l_nodes)
        m_alpha = np.max(m_alpha,0.2) 
        p=1/m_alpha*(w-1/old_fos*sin*(c -u)*tan_phi)
        R=(c+(p-u)*tan_phi)*quadrature.weights
        increment = old_fos - np.sum(R,1)/Osum
        return increment

    result.factor_of_safety = optimize.newton(FO_m, Fellenius_result, options.tolerance , options.max_iteration)
    result.nodes=np.concatenate(x_nodes,y_nodes)
    result.depths=geometry.ground_surface(x_nodes)-y_nodes
    result.weight_forces=w*quadrature.weights
    result.resisting_forces=R
    result.inter_slice_forces=np.zeros(2,len(x_nodes))
    return result

