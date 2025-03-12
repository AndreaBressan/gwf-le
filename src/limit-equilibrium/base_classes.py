# -*- coding: utf-8 -*-
"""
Created on 2025-03-12

@author: Leonardo Lalicata, Andrea Bressan

Input and output formats for limit equilibrium methods
"""

import numpy as np

class Geometry:
    """ Geometry describes terrain and a landslide by using the following data
        - ground_surface, a map x to y
        - slip_surface, a map x to y
        - bounding_box
        - landslide_interval
        """
    def __init__(self,ground_surface, slip_surface, slip_tangent, bounding_box, landslide_interval):
        self.ground_surface=ground_surface
        self.slip_surface=slip_surface
        self.slip_tangent=slip_tangent
        self.bounding_box=bounding_box
        self.landslide_interval=landslide_interval
    
class SoilProperties:
    """ SoilProperties describes the local properties of a terrain using maps (x,y) -> property
        - cohesion
        - friction_angle (degree)
        - dry_density
        _ porosity
        _ grain_density
        """
    def __init__(self, cohesion, friction_angle, dry_density, porosity, grain_density):
        self.cohesion=cohesion        
        self.friction_angle=friction_angle
        self.dry_density=dry_density
        self.porosity=porosity
        self.grain_density=grain_density

class SoilState:
    """ SoilState describes the local state of a terrain using maps (x,y) -> state variable
        _ saturation
        _ pore_pressure
        _ integrated_density
        """
    def __init__(self,saturation, pore_pressure, integrated_density):
        self.saturation=saturation
        self.pore_pressure=pore_pressure
        self.integrated_density=integrated_density

class Quadrature:
    def __init__(self, nodes, weights):
        self.nodes=nodes
        self.weights=weights

class UniformQuadrature(Quadrature):
    def __init__(self, x_interval, num):
        self.nodes=x_interval[0]+(x_interval[1]-x_interval[0])/num*(np.linspace(0,num-1,num)+1/2)
        self.weights=(x_interval[1]-x_interval[0])/num*np.ones(num)

class Options:
    def __init__(self, max_iteration, tolerance):
        self.max_iteration=max_iteration
        self.tolerance=tolerance

class Result:
    def __init__(self, factor_of_safety,nodes, depths, weight_forces, resisting_forces, inter_slice_forces):
        self.factor_of_safety=factor_of_safety        
        self.nodes=nodes
        self.depths=depths
        self.weight_forces=weight_forces
        self.resisting_forces=resisting_forces
        self.inter_slice_forces=inter_slice_forces