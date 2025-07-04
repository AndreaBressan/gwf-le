# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 10:34:42 2022

@author: Leonardo
"""

import numpy as np
import pandas as pd
from Geometry import geometry
from Geometry import SlopeHeigth
from Geometry import SlopeAngle
from circle_line_segment_intersection import circle_line_segment_intersection
import matplotlib.pyplot as plt

from circ_2pts_tan import circ_2pts_tan
#--------------------------------------------------------------------------
#------------------------------------------------------
#%%
"""
 scegli centri e raggi a partire dai punti di ingresso e di uscita della sds
 griglia molto lasca. deve essere il punto di partenza del simplesso
"""
def grid():
    Ndivs = 3
    N2 = int(np.round(Ndivs/2, 0))
    soilsurface = geometry(SlopeHeigth , SlopeAngle)[-1]
    
    # entry and exit value of the max slipcircle
    H = SlopeHeigth
    B = SlopeHeigth / np.tan(np.radians(SlopeAngle))
    A = max(H,B)
    toe = np.array([- 1.0 * A , 0 ])
    crest = np.array( [ B + 1.0*A , H])
    
    sds_in =  np.linspace(soilsurface.loc['B'] , crest , Ndivs) 
    sds_out1 =  np.linspace(toe , soilsurface.loc['A'] , Ndivs) 
    sds_out2 = np.linspace(soilsurface.loc['B']/16 , soilsurface.loc['B']/4 , N2)
    sds_out = np.append(sds_out1 , sds_out2 , axis=0)
    #
    # gradi minimo
    eta_eps = 5
    xc , yc , raggio = [] , [] , [] 
    I , O , S  , PO , POy= [] , [] , [] , [] , []
    for i in sds_in:
        for o in sds_out:
            """
            sto cercando l la pendenza minima della retta tangente al cerchio punto in ingresso "sds in"
            per non avere intersezioni con il pendio prima di dell'uscita "sds out"
            
            eta_eps = 5° minimo intervallo di angolo per l'iterazione
                in questo modo la pendenza di ingresso "slope in" viene suddivisa in un intervallo di lunghezza variabile
                ma con passo minimo 5°.
                
                la diretta conseguenza è che:
                    per inclinazioni del pendio "beta" basse, ho tanti valori dell angolo eta su cui iterare
                    er inclinazioni del pendio "beta" alte, ho pochi valori dell angolo eta su cui iterare (al limite 1)
            """
            if o[0] >= soilsurface.loc['A','x']:
                eta_min = np.degrees(np.arctan(i[1]/ i[0]))
            else:
                m_perp_in_0 =  - i[0]/i[1]
                xc_min = 0.5 * o[0]
                yc_min = i[1] + m_perp_in_0 * (xc_min - i[0]) 
                eta_min = np.degrees(np.arctan(- (i[0]  - xc_min ) / (i[1]  - yc_min )))
                
            if eta_min < 0:
                eta_min = np.nan
                campioni_eta = 0
            else:
                eta_min = eta_min
                campioni_eta = np.ceil( (90  - eta_min) / eta_eps)    
                
            eta = np.linspace(eta_min+1 , 90 , int(campioni_eta) )
            eta = np.ravel(eta)  
                #
            slope_in = np.tan(np.radians(eta))
                
            for s in slope_in:
                x , y , r = circ_2pts_tan(i , o , s)
                xc.append(x)
                yc.append(y)
                raggio.append(r)
                I.append(i[0])
                O.append(o[0])
                S.append(s)
                PO.append(tuple(np.round(o,3)))
                POy.append(o[1])
    
    grid = pd.DataFrame({'xc': xc , 'yc': yc , 'Radius': raggio , 
                            'sds in': I , 'sds out': O , 'angolo entrata': np.degrees(np.arctan(S)) ,
                            'punto uscita' : PO , 'pt uscita-y' : POy})
    
    grid = grid.mask(grid['xc'] > soilsurface.loc['B','x']).dropna()
    grid = grid.reset_index()
    #-------------------------------------------------------------------------#
    # ora elimino i cerchi che escono dal pendio prima dell'uscita
    centre , res = [] , []
    for i in range(len(grid)):
        c = [grid['xc'][i] , grid['yc'][i]]
        centre.append(c)
    radius , pt1 , pt2 =  grid['Radius'] , soilsurface.loc['A'] , soilsurface.loc['B']
    for i in range(len(grid.index)):
        v = circle_line_segment_intersection(centre[i], radius[i], pt1, pt2 , full_line=True)
        res.append(v)
    res[res == 'none'] = [(0,1000) , (0 , 1000)]
    y = [x0[0][1] for x0 in res]
    punto = [x0[0] for x0 in res]
    dio = [tuple(np.round(p,3)) for p in punto]
    mask =( y > grid['pt uscita-y'])
    grid['int 1'] = dio
    grid = grid.mask(mask).dropna()   
    #------------------------------------------------------------------------#    
    grid = grid.reset_index()
    grid.drop(['level_0' , 'index' , 'pt uscita-y' ], axis = 1, inplace = True)
    
    return grid
#%%

# grid1 = grid()[0]
# soilsurface = grid()[1]
