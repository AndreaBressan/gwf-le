# -*- coding: utf-8 -*-
"""
Created on 2025-03-04

@author: Leonardo Lalicata, Andrea Bressan

Bishop limit equilibrium method
"""

import scipy.optimize as optimize
import numpy as np
import base_classes as bc
from slices_data import slices_data 


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
        - program inputs
    """

    T=slices_data (geometry, soil_properties, soil_state, options)
    I=(geometry, soil_properties, soil_state, options)
    return bishop_with_tuple(T,I)


def bishop_with_tuple(T,I):
    (x_nodes,y_nodes,t_nodes,l_nodes,
     cos,sin,
     tan_phi,
     u,w,c,depth,
     quad_weights)=T
    p=w*cos  #"Fellenius method to init iteration of the Bishop method

    sign=np.sign(y_nodes[-1]-y_nodes[1])
    R=(c+(p-u)*tan_phi)*quad_weights
    O=sign*w*sin*quad_weights
    Osum=np.sum(O,0)
    Fellenius_result=np.sum(R,0)/Osum

    #"start iteration of Bishop method"
    def FO_m(old_fos):
        # TODO fix me
        # BUG here
        # t_nodes cambia significato rispetto alla fisica a seconda che il 
        # pendio salga o scenda da sx a dx
        m_alpha = cos * (1+1/old_fos * tan_phi * t_nodes*sign) 
        m_alpha = np.maximum(m_alpha,0.2)
        p=1/m_alpha*(w-1/old_fos*sin*(c-u*tan_phi)*sign)
        nonlocal R
        R=(c+(p-u)*tan_phi)*quad_weights
        increment = old_fos - np.sum(R,0)/Osum
        return increment

    # scipy.optimize.newton uses the secant method if not provided with the 
    # derivative of the cost function. This is what happens here

    options=I[-1]
    geometry=I[0]
    soil_properties=I[1]
    Bishop_result = optimize.newton(
                func=FO_m, x0=Fellenius_result,
                tol=options.tolerance,
                maxiter=options.max_iteration
                )
    if Bishop_result<Fellenius_result:
        factor_of_safety = Fellenius_result
    else:
        factor_of_safety = Bishop_result
        
    return bc.Result(
        method="Bishop",
        factor_of_safety = factor_of_safety,
        Lambda = 0.0,
        nodes=np.vstack((x_nodes,y_nodes)),
        depths=geometry.ground_surface(x_nodes)-y_nodes,
        weight_forces=w*quad_weights,
        resisting_forces=R,
        inter_slice_forces=np.zeros((2,len(x_nodes))),
        inputs=I
        )