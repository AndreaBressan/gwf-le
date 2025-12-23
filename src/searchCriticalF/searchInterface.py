# -*- coding: utf-8 -*-
"""
Created on 2025-12-23

@author: Leonardo Lalicata, Andrea Bressan, Simone Pittaluga

Input and output structures for searching of the critical slip surface
"""
from typing import List,Dict
from abc import abstractmethod
from time import perf_counter
import numpy as np


from LEM.lemInterface import Geometry, lemOptions, lemResult, Soil

class searchDomain:
    def __init__(self,
                ground_surface
                ):
        self.ground_surface = ground_surface
    @abstractmethod
    def getParametersBound(self) -> np.ndarray:
        pass
    @abstractmethod
    def getParameters(self, geometry : Geometry) -> np.ndarray:
        pass
    @abstractmethod
    def sample_grid(self, options : Dict) -> List[Geometry]:
        pass
    @abstractmethod
    def makeGeometry(self, param:np.ndarray) -> Geometry:
        pass

class lemMethod:
    def __init__(self,
                func,
                soil    : Soil,
                options : lemOptions,
                ):
        self.func    = func
        self.soil    = soil
        self.options = options
   

def find_critical  (domain : searchDomain, method : lemMethod, geometries: List[Geometry], num_geometries: int=1):
    time_start = perf_counter()
    result=[
            (geo, 
                method.func(
                    geometry=geo,
                    options=method.options,
                    soil=method.soil)) for geo in geometries]
    result.sort(key=lambda x: x[1].factor_of_safety)
    return result[:num_geometries], perf_counter()-time_start


def simplex     (domain : searchDomain, method : lemMethod, initialGeometries: List[Geometry], num_geometries: int=1):
    

def grid_simplex(domain : searchDomain, method : lemMethod, initialGeometries: List[Geometry], num_geometries: int=1):
    
