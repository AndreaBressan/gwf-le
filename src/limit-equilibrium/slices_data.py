# -*- coding: utf-8 -*-
"""
Created on 2025-06-03

@author: Leonardo Lalicata, Andrea Bressan

Common computations between all limit equilibrium methods
"""
import numpy as np


"""
Return the following data computed at the lices' base midpoints

Geometric outputs
    -x_nodes abscissa                (L)
    -y_nodes ordinata                (L)
    -t_nodes tangent of the slope angle
    -l_nodes slices lengths          (L)
    -cos
    -sin
Soil outputs
    -tan_phi friction coefficient
Force  outputs
    -u pore pressure per unit length (F/L)
    -w weigth per unit length        (F/L)
    -c cohesion per unit length      (F/L)

"""
def slices_data (geometry, soil_properties, soil_state, options):
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
    return (x_nodes,y_nodes,t_nodes,l_nodes,cos,sin,tan_phi,u,w,c,quad.weights)