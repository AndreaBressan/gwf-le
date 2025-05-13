# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 10:28:37 2022

@author: Leonardo
"""

import numpy as np
import pandas as pd

"""
    GEOMETRY
        SlopeHeigth = Height of the slope [m]
        SlopeAngle = inclination of the slope [°]
        Xlft = left boundary of the model [m]
        Xrht = right boundary of the model [m]
        
        A = [ 0 , 0 ] toe of the slope
        B = [ SlopeHeigth / tan(SlopeAngle) , SlopeHeigth ] crest of the slope
"""
SlopeHeigth = 3.
SlopeAngle = 45.

def geometry(SlopeHeigth , SlopeAngle):
    
    BB = SlopeHeigth / np.tan(np.radians(SlopeAngle))
    AA = max(SlopeHeigth,BB)
    
    Xlft = [ -3 * AA , 0 ]
    Xrht = [  3 * AA , SlopeHeigth ]
    A = [ 0 , 0 ]
    B = [ SlopeHeigth / np.tan(np.radians(SlopeAngle)) , SlopeHeigth ]
    
    l = [Xlft , A , B , Xrht]
    label = ['Xlft' , 'A' , 'B' , 'Xrht']
    Geometry = pd.DataFrame(l, index=label)
    Geometry.columns = ['x', 'y']
    return SlopeHeigth , SlopeAngle , A , B , Geometry