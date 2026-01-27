# -*- coding: utf-8 -*-
"""
Created on 2025-12-23

@author: Leonardo Lalicata, Andrea Bressan, Simone Pittaluga

Input and output structures for searching of the critical slip surface
"""
from typing import List,Dict,Tuple,Callable
from abc import abstractmethod
from time import perf_counter
import sys
from pathlib import Path
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.searchCriticalF.searchInterface import searchDomain
from src.LEM.lemInterface import Geometry

class circularArc (Geometry):
    def __init__(self,
                ground_surface,
                center,
                radius,
                dist,
                out_pt,
                in_pt,
                middle,
                eta,
                alpha):
        self.center=center
        self.radius= radius
        self.dist=dist
        self.out_pt=out_pt
        self.in_pt=in_pt
        self.middle=middle
        self.eta=eta
        self.alpha=alpha    
        self.ground_surface=ground_surface
        interval=[self.in_pt[0],self.out_pt[0]]
        self.landslide_interval=np.array([np.min(interval),np.max(interval)])
        # max used to silence warnings due to small negative arguments of sqrt due to floating point approximation
        self.slip_surface= lambda x : self.center[1]-np.sqrt( np.maximum(self.radius**2-(self.center[0]-x)**2,0.0)) 
        self.slip_tangent= lambda x : (x-self.center[0])/np.sqrt( self. radius**2-(self.center[0]-x)**2)    

    @classmethod
    def fromCenterAndRadius(cls, ground_surface, center, radius):
        r=radius
        c=center
        xmin , xmax = c[0]-radius , c[0]+r
        xd=[xmin , xmax]
        f=lambda x:  r**2-(c[0]-x)**2-(c[1]-ground_surface(x))**2

        xs=np.linspace(xd[0],xd[1],50)
        ys=f(xs)
        sc=np.nonzero(ys[:-1]*ys[1:]<=0)[0]
        def bisect(f,l,r,fl,fr,tol):
            if np.any(np.abs(r-l)>tol):
                c=(l+r)/2
                fc=f(c)
                li= (fc*fl>=0)
                ri= (fc*fr>0)
                l[li]=c[li]; fl[li]=fc[li]
                r[ri]=c[ri]; fr[ri]=fc[ri]
                return bisect(f,l,r,fl,fr,tol)
            else: return (l+r)/2.0
        xs=bisect(f,xs[sc],xs[sc+1],ys[sc],ys[sc+1],1e-10)
        ys=ground_surface(xs)

        pos= int(ys[0]>=ys[1])
        out_pt=np.array([xs[pos],ys[pos]])
        in_pt=np.array([xs[1-pos],ys[1-pos]])

        m=(out_pt+in_pt)/2.0
        um=np.linalg.norm((out_pt-in_pt))/2.0
        d=r-np.linalg.norm((m-c))
        alpha=np.arcsin(um/r)
        eta=alpha+np.arcsin((m[1]-out_pt[1])/um)
        return cls(ground_surface=ground_surface,
            center=center,
            radius=radius,
            out_pt=out_pt,
            in_pt=in_pt,
            dist=d,
            middle=m,
            eta=eta,
            alpha=alpha)
    
    @classmethod
    def fromInOutAndEta(cls, ground_surface, in_x, out_x, eta):
        ex=in_x
        ux=out_x
        uy=ground_surface(ux)
        ey=ground_surface(ex)
        out_pt=np.array([ux,uy])
        in_pt=np.array([ex,ey])
        m=(out_pt+in_pt)/2
        nue=np.linalg.norm(out_pt-in_pt)
        alpha=eta+np.sign(out_x-in_x)*np.arcsin((m[1]-out_pt[1])/nue*2)
        if alpha>0:
            r=nue/np.sin(alpha)/2
            d=(1-np.cos(alpha))*r
            c=m+(r-d)*ortho(m,in_pt)
        else:
            r=+np.inf
            c=np.array([(-1)**int(ux>ex)*np.inf,np.inf])
            d=0
        return cls(ground_surface=ground_surface,
            center=c,
            radius=r,
            out_pt=out_pt,
            in_pt=in_pt,
            dist=d,
            middle=m,
            eta=eta,
            alpha=alpha)

    @classmethod
    def fromInOutAndDist(cls, ground_surface, in_x, out_x, dist):
        ex=in_x
        ux=out_x
        d=dist
        uy=ground_surface(ux)
        ey=ground_surface(ex)
        out_pt=np.array([ux,uy])
        in_pt=np.array([ex,ey])
        m=(out_pt+in_pt)/2
        nue=np.linalg.norm(out_pt-in_pt)
        if d==0:
            r=+np.inf
            c=np.array([(-1)**int(ux>ex)*np.inf,np.inf])
            alpha=0.0
            if ux==ex and uy==ey:
                eta=np.nan
            eta=np.arcsin((ey-uy)/nue)
        else:
            r=d+ (nue**2/4-d**2)/(2*d)
            c=m+(r-d)*ortho(m,in_pt)
            alpha=np.arcsin(nue/2/r)
            eta=alpha+np.arcsin((m[1]-out_pt[1])/nue*2)
        return cls(ground_surface=ground_surface,
            center=c,
            radius=r,
            out_pt=out_pt,
            in_pt=in_pt,
            dist=d,
            middle=m,
            eta=eta,
            alpha=alpha)
    
    @classmethod
    def fromThreePoints(cls, ground_surface, in_x, out_x):
        in_pt = np.array([in_x , ground_surface(in_x)])
        out_pt = np.array([out_x , ground_surface(out_x)])
        ZERO = np.array([0,0])
        # Calcolo dei determinanti
        temp = in_pt[0]**2 + in_pt[1]**2
        bc = (out_pt[0]**2 + out_pt[1]**2 - temp) / 2.0
        cd = (temp - ZERO[0]**2 - ZERO[1]**2) / 2.0
        det = (out_pt[0] - in_pt[0])*(in_pt[1] - ZERO[1]) - (in_pt[0] - ZERO[0])*(out_pt[1] - in_pt[1])
        # Coordinate del centro
        cx = (bc * (in_pt[1] - ZERO[1]) - cd * (out_pt[1] - in_pt[1])) / det
        cy = ((out_pt[0] - in_pt[0]) * cd - (in_pt[0] - ZERO[0]) * bc) / det
        # Raggio calcolato come distanza euclidea tra centro e uno dei punti
        dx = cx - out_pt[0]
        dy = cy - out_pt[1]
        r = (dx**2 + dy**2)**0.5
        return cls.fromCenterAndRadius(ground_surface=ground_surface,
            center=(cx, cy),
            radius=r)


def ortho(pt1,pt2):
    dir=pt2-pt1
    dir=dir/np.linalg.norm(dir)
    return np.array([-dir[1],dir[0]])



class circularSlipSearchDomain (searchDomain):
    def __init__(self,
                 ground_surface : Callable,
                 in_range  : tuple[float,float],
                 out_range : tuple[float,float]
    ):
        self.ground_surface = ground_surface 
        self.in_range  = in_range  
        self.out_range = out_range
    def getParametersBound(self) -> np.ndarray:
        return np.array([self.in_range, self.out_range])
    
    def getParameters(self, geometry : Geometry) -> np.ndarray:
        if not isinstance(geometry,circularArc):
            return np.nan*np.ones(3)
        else:
            return np.array([geometry.in_pt[0],geometry.out_pt[0],geometry.eta])
        
    def sample_grid(self, options : Dict) -> List[Geometry]:
        has_interval = "in_interval" in options and "num_in_points" in options
        has_points   = "in_pts" in options
        if not (has_interval or has_points):
            raise Exception("Not enough info for in points: provide interval and num or a list")
        elif has_interval and has_points:
            raise Exception("in_pts are specified both by a list and other data,use only one")
        if has_points:
            in_pts=options["in_points"]
        else:
            interval=options["in_interval"]
            in_pts=np.linspace(interval[0],interval[1],options["num_in_pts"])

        has_interval = "out_interval" in options and "num_out_points" in options
        has_points   = "out_pts" in options
        if not (has_interval or has_points):
            raise Exception("Not enough info for out points: provide interval and num or a list")
        elif has_interval and has_points:
            raise Exception("out_pts are specified both by a list and other data,use only one")
        if has_points:
            out_pts=options["out_points"]
        else:
            interval=options["out_interval"]
            out_pts=np.linspace(interval[0],interval[1],options["num_out_pts"])
        
        if  "min_eta_inc" in options:
            min_eta_inc=options["min_eta_inc"]
        else:
            min_eta_inc=np.radians(5)

        geometries=[]
        params=np.array(3)
        for i in in_pts:
            for o in out_pts:
                eta_min=self.computeEtaMinForSurface(i,o)
                eta_max=np.pi/2
                num_eta=np.floor((eta_max-eta_min)/min_eta_inc)
                eta=np.linspace(eta_min,eta_max,int(num_eta))
                params[0]=i
                params[1]=o
                for e in eta:
                    params[2]=e
                    geometries.append(self.makeGeometry(params))
        return geometries
        
    def makeGeometry(self, param:np.ndarray) -> Geometry:
        return circularArc.fromInOutAndEta(self.ground_surface,param[0],param[1],param[2])

    def computeEtaMinForSurface(self, in_pt,out_pt,npts=500,tol=1e-4):
        test_pts=np.linspace(in_pt,out_pt,npts)
        # prova
        gl=self.ground_surface(test_pts)
        eta_max=np.pi/2
        eta_min=np.arctan((gl[0]-gl[-1])/(in_pt-out_pt))
        eta_mid=(eta_max+eta_min)/2
        test_pts=test_pts[1:-2]
        gl=gl[1:-2]
        params=np.array([in_pt,out_pt,eta_mid])
        for iter in range(0,13):
            params[2]=eta_mid
            mid_surf=self.makeGeometry(params)
            test=mid_surf.slip_surface(test_pts)
            if np.all(gl>test):
                eta_max=eta_mid
            else:
                eta_min=eta_mid
            eta_mid=(eta_max+eta_min)/2
        return eta_mid