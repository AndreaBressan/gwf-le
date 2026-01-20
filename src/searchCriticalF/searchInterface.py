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
    def paramIsValid(self, param:np.ndarray)-> bool:
        return np.all(param>=self.getParametersBound[:,0]) and np.all(paramv=self.getParametersBound[:,1])

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


def simplex     (domain : searchDomain, method : lemMethod, initialGeometries: List[Geometry], num_geometries: int=1,
                 options={
                            'disp'      : False,
                            'xatol'     : 1e-3,
                            'fatol'     : 1e-4,
                            'maxiter'   : 100,
                            'return_all': True
                            }):
    time_start = perf_counter()
    from scipy import optimize
    def func(v):
        func.calls+=1
        if not domain.paramIsValid(v):
            return np.nan
        else:
            geometry=domain.makeGeometry(v)
            return method.func(geometry,method.soil,method.options).factor_of_safety
    func.calls=0
    
    optimized_params=[optimize.minimize(func, domain.getParameters(geo), 
                          method='Nelder-Mead',
                          bounds = searchDomain.getParametersBound,
                          options = options
                          ) for geo in initialGeometries]
    optimized_params.sort(key=lambda z: z.fun)
    result=[ (domain.makeGeometry(v.x),method.func(domain.makeGeometry(v.x),method.soil,method.options)) for v in optimized_params[:num_geometries] ]    
    return result, perf_counter()-time_start, func.calls

def grid_simplex(domain : searchDomain, method : lemMethod, initialGeometries: List[Geometry], num_geometries: int=1,
                 options = { 'num_grid_output': 1 }):
    grid_result,t1=find_critical(domain,method,initialGeometries,options['num_grid_output'])
    simplex_start_geo=[g[0] for g in grid_result]
    optimized,  t2,calls=simplex(domain,method,simplex_start_geo,num_geometries)
    return optimized,t1+t2,calls

