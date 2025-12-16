# -*- coding: utf-8 -*-
"""
Created on 2025-12-16

@author: Leonardo Lalicata, Andrea Bressan

Input and output structures for limit equilibrium methods
"""

import numpy as np

class SliceSubdivision:
    def __init__(self,
                 endpoints,
                 points_per_slice=1
                ):
        self.endpoints=endpoints
        self.points_per_slice=points_per_slice
        lengths=endpoints[1:]-endpoints[0:-1]
        centers=(endpoints[1:]+endpoints[0:-1])/2
        if points_per_slice==1:
            self.nodes=centers
            self.weights=lengths
        elif points_per_slice==2:
            gauss_position=np.array([-.5,.5])/np.sqrt(3.0)
            gauss_weight=np.array([.5,.5])
            self.nodes=(centers[:, None]+gauss_position*lengths[:, None]).ravel()
            self.weights=(lengths[:, None] * gauss_weight).ravel()
        else:
            raise ValueError("Integration order can be only one of 1,2")



def default_subdivision(interval,slice_num=50):
    return SliceSubdivision(
        np.linspace(interval[0],interval[1],slice_num+1),
        0)

# idea optional_outputs could be a list of names
# methods only fill requested data in a dictionary
# list could include inputs method_options geometry slices_base_data slices_side_data


class lemOptions:
    def __init__(self,
        max_iteration=100,
        tolerance=1e-4,
        optional_outputs=False,
        subdivision_method=default_subdivision
        ):
        self.max_iteration=max_iteration
        self.tolerance=tolerance
        self.optional_outputs=optional_outputs
        self.subdivision_method=subdivision_method

class Geometry:
    """ Geometry describes terrain and a landslide by using the following data
        - ground_surface, a map x to y
        - slip_surface, a map x to y
        - landslide_interval
        """
    def __init__(self,ground_surface, slip_surface, slip_tangent, landslide_interval):
        self.ground_surface=ground_surface
        self.slip_surface=slip_surface
        self.slip_tangent=slip_tangent
        self.landslide_interval=landslide_interval

class Soil:
    def __init__(self,
          cohesion,
          vertical_cohesion,
          friction_angle,
          vertical_friction_angle,
          pore_pressure,
          saturation,
          column_weight):
        self.cohesion=cohesion
        self.vertical_cohesion=vertical_cohesion
        self.friction_angle=friction_angle
        self.vertical_friction_angle=vertical_friction_angle        
        self.pore_pressure=pore_pressure
        self.saturation=saturation
        self.column_weight=column_weight
        
class lemResult:
    # methods fill optional_outputs that is a dictionary according to the MethodOption
    def __init__(self,
                method_name,
                factor_of_safety,
                Lambda,
                optional_outputs
                ):
        self.method_name=method_name
        self.factor_of_safety=factor_of_safety
        self.Lambda=Lambda       
        self.optional_outputs=optional_outputs
