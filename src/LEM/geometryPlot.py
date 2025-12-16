# -*- coding: utf-8 -*-
"""
Created on 2025-12-16

@author: Leonardo Lalicata, Andrea Bressan

Input and output structures for limit equilibrium methods
"""

import numpy as np
import matplotlib.pyplot as plt
from lemInterface import Geometry

class GeometryPlot(Geometry):
    def __init__(self,geometry,bounding_box):
        super().__init__(
            ground_surface=geometry.ground_surface,
            slip_surface=geometry.slip_surface,
            slip_tangent=geometry.slip_tangent,
            landslide_interval=geometry.landslide_interval.copy()
            )
        self.bounding_box=bounding_box.copy()

    def plot(self,num_points,dpc=100,x_cm=np.nan,y_cm=np.nan):
        ocra=(205/255,133/255,63/255)
        ocra2=(205/511,133/511,63/511)
        if np.isnan(x_cm):
            if np.isnan(y_cm):
                x_cm=10
                y_cm=x_cm/np.sqrt(2)
            else:
                x_cm=y_cm*np.sqrt(2)
        else:
            if np.isnan(y_cm):
                y_cm=x_cm/np.sqrt(2)

        xs=self.getGroundPlotPoints(num_points)
        gs=self.ground_surface(xs)
        bt=self.bounding_box[1,0]*np.ones_like(gs)

        plt.fill_between(xs, gs, bt, interpolate=True, color=ocra)
        plt.plot(xs, gs, lw=1,color=ocra2)
        plt.ylim((self.bounding_box[1,0],self.bounding_box[1,1]))
        plt.xlim((self.bounding_box[0,0],self.bounding_box[0,1]))
        self.plotSlipSurface(num_points)

        plt.title('Geometry plot')
        return plt.gcf()

    def plotSlipSurface(self,num_points,color=(1,0,0)):
        xl=self.getLandslidePlotPoints(num_points)
        yl=self.slip_surface(xl)
        plt.plot(xl, yl, lw=1,color=color)
    
    def getGroundPlotPoints(self,num_points):
        xs=np.linspace(self.bounding_box[0,0],self.bounding_box[0,1],num_points)
        xs=np.sort(np.concatenate((xs,self.landslide_interval)))
        return xs

    def getLandslidePlotPoints(self,num_points):
        g_width=self.bounding_box[0,1]-self.bounding_box[0,0]
        l_width=self.landslide_interval[1]-self.landslide_interval[0]
        scaledNum=np.maximum(2.0,np.ceil(num_points*l_width/g_width)).astype(int)
        xs=np.linspace(self.landslide_interval[0],self.landslide_interval[1],scaledNum)
        return xs