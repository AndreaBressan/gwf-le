# -*- coding: utf-8 -*-
"""
Created on 2025-12-16

@author: Leonardo Lalicata, Andrea Bressan

Input and output structures for limit equilibrium methods
"""

import numpy as np


def uniform_subdivision(interval,slice_num=50):
    endpoints=np.linspace(interval[0],interval[1],slice_num+1)
    centers=(endpoints[1:]+endpoints[0:-1])/2
    return endpoints,centers

# idea optional_outputs could be a list of names
# methods only fill requested data in a dictionary
# list could include inputs method_options geometry slices_base_data slices_side_data


class lemOptions:
    def __init__(self,
        max_iteration=100,
        tolerance=1e-4,
        optional_outputs=None,
        subdivision_method=lambda interval: uniform_subdivision(interval,50)
    ):
        self.max_iteration=max_iteration
        self.tolerance=tolerance
        self.optional_outputs=optional_outputs if optional_outputs is not None else []
        self.subdivision_method=subdivision_method
    
    def copy(self):
        """Create a copy of this lemOptions object"""
        return lemOptions(
            max_iteration=self.max_iteration,
            tolerance=self.tolerance,
            optional_outputs=self.optional_outputs,
            subdivision_method=self.subdivision_method
        )

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
    
    @staticmethod
    def sample_vertical(x,y_bot,y_top,f,num_samples):
        r=np.linspace(0,1,num_samples+1)
        r=(r[1:]+r[:-1])/2
        ys=np.outer(y_bot,r)+np.outer(y_top,1.0-r)
        return f(np.repeat(x[:,np.newaxis],num_samples,axis=1 ),ys)

    @(classmethod)
    def soilWithVerticalSampling(cls,
        cohesion,
          friction_angle,
          pore_pressure,
          saturation,
          column_weight,
          num_vertical_sample=1  
        ):
        return cls(
            cohesion=cohesion,
            friction_angle=friction_angle,
            pore_pressure=pore_pressure,
            saturation=saturation,
            column_weight=column_weight,
            vertical_cohesion=
                lambda x,y,ytop: Soil.sample_vertical(x,y,ytop,cohesion,num_vertical_sample),
            vertical_friction_angle=
                lambda x,y,ytop: Soil.sample_vertical(x,y,ytop,friction_angle,num_vertical_sample)
            )


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
