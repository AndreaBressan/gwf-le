# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 10:49:36 2023

@author: Leonardo
"""
# import numpy as np

def circ_2pts_tan(sds_in , sds_out , slope_in):
    """
    trova il centro, il raggio e l'arco di cerchio dati 
    i punti di ingresso e uscita della sds e la tangente all'ingresso

    Parameters
    ----------
    sds_in : ingresso superficie di scorrimento
    sds_out : uscita superficie di scorrimento
    slope_in : pendenza superficie di scorrimento

    Returns
    -------
    xc , yc , R : coord-x del centro, coord-y del centro, raggio arco di circ

    """
    # P = punto intermedio tra sds_in e sds_out
    P = [(sds_in[0] + sds_out[0])/2 , (sds_in[1] + sds_out[1])/2]
    #
    # retta per sds_in: y = m*x+ q
    m = slope_in
    #
    # retta ortogonale alla retta per sds_in: y = m1*x+ q1
    m1 = -1/m
    q1 = sds_in[1] - m1 * sds_in[0]
    #
    # pendendza retta per sds_in e sds_out : = m_io
    m_io = (sds_in[1] - sds_out[1]) / (sds_in[0] - sds_out[0])
    #
    # pendendza retta ortogonale sds_in e sds_out : = m_io
    m2 = - 1 / m_io
    q2 = P[1] - m2 * P[0] 
    #
    # centro calcolato come intersezione tra le due rette 1 e 2
    # raggio come distanza tra C e sds_in
    xc = (q2 - q1) / ((m1 - m2))
    yc = m1 *xc + q1
    C = [xc , yc]
    R = ((C[1] - sds_in[1])**2 + (C[0] - sds_in[0])**2 )**0.5
    # if (m1-m2) == 0:
    #     print('---')
    #     print(sds_in[0] , sds_out[0] , np.degrees(np.arctan(slope_in)))
    #     print('xc:' , xc , 'm1:', m1 , 'm2:', m2)
    # print((m1 - m2))
    # print('pendenza ingresso=',m)
    # print('m1=',m1)
    # print('m2=',m2)
    # print('xc=', (q2 - q1) / ((m1 - m2)))
    
    return xc , yc , R

# sds_in = [2.2298118418716273, 5.0]
# sds_out = [0, 0.0]
# m = np.tan(np.radians(90))

# res = circ_2pts_tan(sds_in , sds_out , m)
    