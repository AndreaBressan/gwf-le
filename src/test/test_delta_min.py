# -*- coding: utf-8 -*-
"""
Created on Thu Jun 19 10:54:28 2025

@author: leolalicata
"""

import numpy as np
import pandas as pd
import sys
sys.path.append("../LEM")
from base_classes import SoilProperties,SoilState,UniformQuadrature,Options,np,plt
from bishop import bishop
from gridOfCircles import GridOptions, gridComputation,computeEtaMinForSurface
from circularSlipSurface import circularSlipSurface
import scipy.optimize as optimize
import time

# Aggiunta da Leo: così funziona
import matplotlib as mpl


beta = 60
slope_height = 1.
slope_base = slope_height / np.tan(np.radians(beta))
dist_max = max(slope_base,slope_height)

ground_surface=(lambda x : 0*(x<=0) 
                + x*np.tan(np.radians(beta)) *(0<x)*(x<=slope_base) 
                + slope_height*(x>slope_base))
bounding_box=np.array([[-3*dist_max,3*dist_max],[-1.5*slope_height,1.5*slope_height]])

in_pt = np.array([1.5*dist_max , slope_height])
out_pt = np.array([-1.5*dist_max , 0])

delta_min_rad = np.arctan( (2*in_pt[0]-out_pt[0]) / ((in_pt[0]**2 - in_pt[0]*out_pt[0] - 1)) )
delta_min_Domenico = np.degrees(delta_min_rad)
print(delta_min_Domenico)


delta_min_rad=computeEtaMinForSurface(ground_surface,bounding_box,in_pt[0],out_pt[0])
delta_min_Andrea = np.degrees(delta_min_rad)
print(delta_min_Andrea)


r = 1.888
in_pt = [1.387 , 1.0]
center = [-0.288 , 1.872]
pendenza_centro_in = ((in_pt[1] - center[1]) / (in_pt[0] - center[0]))
delta = np.degrees(np.arctan(-1/pendenza_centro_in))
print(delta)