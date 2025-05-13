# -*- coding: utf-8 -*-
"""
Created on 2025-03-12

@author: Leonardo Lalicata, Andrea Bressan

Input and output formats for limit equilibrium methods
"""
import matplotlib.pyplot as plt
import numpy as np

class Geometry:
    """ Geometry describes terrain and a landslide by using the following data
        - ground_surface, a map x to y
        - slip_surface, a map x to y
        - bounding_box
        - landslide_interval
        """
    def __init__(self,ground_surface, slip_surface, slip_tangent, bounding_box, landslide_interval):
        self.ground_surface=ground_surface
        self.slip_surface=slip_surface
        self.slip_tangent=slip_tangent
        self.bounding_box=bounding_box
        self.landslide_interval=landslide_interval

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
        inch=2.54

        plt.figure(1,dpi=dpc*inch,figsize=(x_cm/inch,y_cm/inch))
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

    
class SoilProperties:
    """ SoilProperties describes the local properties of a terrain using maps (x,y) -> property
        - cohesion
        - friction_angle (degree)
        - dry_density
        _ porosity
        _ grain_density
        """
    def __init__(self, cohesion, friction_angle, dry_density, porosity, grain_density):
        self.cohesion=cohesion        
        self.friction_angle=friction_angle
        self.dry_density=dry_density
        self.porosity=porosity
        self.grain_density=grain_density

class SoilState:
    """ SoilState describes the local state of a terrain using maps (x,y) -> state variable
        _ saturation
        _ pore_pressure
        _ integrated_density
        """
    def __init__(self,saturation, pore_pressure, integrated_density):
        self.saturation=saturation
        self.pore_pressure=pore_pressure
        self.integrated_density=integrated_density

class Quadrature:
    def __init__(self, nodes, weights):
        self.nodes=nodes
        self.weights=weights

class UniformQuadrature(Quadrature):
    def __init__(self, x_interval, num):
        self.nodes=x_interval[0]+(x_interval[1]-x_interval[0])/num*(np.linspace(0,num-1,num)+1/2)
        self.weights=(x_interval[1]-x_interval[0])/num*np.ones(num)

class Options:
    def __init__(self, max_iteration, tolerance, quadrature=lambda interval:UniformQuadrature(interval,30)):
        self.max_iteration=max_iteration
        self.tolerance=tolerance
        self.quadrature=quadrature

class Result:
    def __init__(self, factor_of_safety,nodes, depths, weight_forces, resisting_forces, inter_slice_forces,sim_inputs):
        self.factor_of_safety=factor_of_safety        
        self.nodes=nodes
        self.depths=depths
        self.weight_forces=weight_forces
        self.resisting_forces=resisting_forces
        self.inter_slice_forces=inter_slice_forces
        self.inputs=sim_inputs