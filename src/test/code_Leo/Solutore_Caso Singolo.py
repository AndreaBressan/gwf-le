# -*- coding: utf-8 -*-
"""
Created on Wed Mar 15 08:09:45 2023

@author: leolalicata
"""

import numpy as np
import pandas as pd
import scipy.optimize as optimize
# from scipy.optimize import show_options
import matplotlib.pyplot as plt
import matplotlib.tri as tri
from circ_2pts_tan import circ_2pts_tan
from GLE_Bishop import GLE # solo Bishop
from Geometry import SlopeHeigth
from Geometry import SlopeAngle
from Geometry import geometry
import time
from Grid import grid
# from VanGenutchten import VG


soilsurface = geometry(SlopeHeigth , SlopeAngle)[-1]
"""
 Soil Parameters
"""
gamma = [18. , 'kN/m3'] # saturated unit weight of soil
c = [5.0 , 'kPa'] # soil coesion
phi = [30. , 'deg'] # friction angle
phi_rad = np.radians(phi[0])
##----------------------------------------------------------------------------#
Ns = 50
#-----------------------------------------------------------------------------#
"""
Caso singolo
"""
x_in , x_out , eta = 5. , 0. , 70.
sds_in  , sds_out = [x_in , SlopeHeigth] , [x_out , 0.]
xa , ya , Ra = circ_2pts_tan(sds_in , sds_out , np.tan(np.radians(eta)))
F_singolo = GLE(Ns , xa , ya , Ra , x_in , x_out , gamma[0] , c[0] , phi_rad)[-1]
Strisce = GLE(Ns , xa , ya , Ra , x_in , x_out , gamma[0] , c[0] , phi_rad)[0]
print('Caso Singolo:' , round(F_singolo,5))
