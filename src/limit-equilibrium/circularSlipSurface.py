import base_classes
import numpy as np

class circularSlipSurface(base_classes.Geometry):
    def __init__(self, ground_surface, bounding_box, center,  radius, dist, out_pt, in_pt, middle, eta, alpha):
        self.center=center
        self. radius= radius
        self.dist=dist
        self.out_pt=out_pt
        self.in_pt=in_pt
        self.middle=middle
        self.eta=eta
        self.alpha=alpha
        
        self.ground_surface=ground_surface
        self.bounding_box=bounding_box
        interval=[self.in_pt[0],self.out_pt[0]]
        self.landslide_interval=np.array([np.min(interval),np.max(interval)])
        # max used to silence warnings due to small negative arguments of sqrt due to floating point approximation
        self.slip_surface= lambda x : self.center[1]-np.sqrt( np.maximum(self.radius**2-(self.center[0]-x)**2,0.0)) 
        self.slip_tangent= lambda x : (x-self.center[0])/np.sqrt( self. radius**2-(self.center[0]-x)**2)

    @classmethod
    def fromCenterAndRadius(cls, ground_surface, bounding_box, center, radius):
        r=radius
        c=center
        xmin , xmax = bounding_box[0] , bounding_box[1]
        xd=[max(xmin,c[0]-r), min(xmax,c[0]+r)]
        f=lambda x:  r**2-(c[0]-x)**2-(c[1]-ground_surface(x))**2
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
        xs=np.linspace(xd[0],xd[1],50)
        ys=f(xs)
        sc=np.nonzero(ys[:-1]*ys[1:]<=0)
        sc=sc[0]
        sc=sc[-2*part:len(sc)-2*(part-1)+1]
    
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
            bounding_box=bounding_box,
            center=center,
            radius=radius,
            out_pt=out_pt,
            in_pt=in_pt,
            dist=d,
            middle=m,
            eta=eta,
            alpha=alpha)
    
    @classmethod
    def fromInOutAndEta(cls, ground_surface, bounding_box, in_x, out_x, eta):
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
            bounding_box=bounding_box,
            center=c,
            radius=r,
            out_pt=out_pt,
            in_pt=in_pt,
            dist=d,
            middle=m,
            eta=eta,
            alpha=alpha)

    @classmethod
    def fromInOutAndDist(cls, ground_surface, bounding_box, in_x, out_x, dist):
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
                eta=np.NaN
            eta=np.arcsin((ey-uy)/nue)
        else:
            r=d+ (nue**2/4-d**2)/(2*d)
            c=m+(r-d)*ortho(m,in_pt)
            alpha=np.arcsin(nue/2/r)
            eta=alpha+np.arcsin((m[1]-out_pt[1])/nue*2)
        return cls(ground_surface=ground_surface,
            bounding_box=bounding_box,
            center=center,
            radius=radius,
            out_pt=out_pt,
            in_pt=in_pt,
            dist=d,
            middle=m,
            eta=eta,
            alpha=alpha)
    
    @classmethod
    def fromThreePoints(cls, ground_surface, bounding_box, in_x, out_x):
        
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
        
        return cls(ground_surface=ground_surface,
            bounding_box=bounding_box,
            center=(cx, cy),
            radius=r,
            out_pt=out_pt,
            in_pt=in_pt,
            dist=None,
            middle=None,
            eta=None,
            alpha=None)


def ortho(pt1,pt2):
    dir=pt2-pt1
    dir=dir/np.linalg.norm(dir)
    return np.array([-dir[1],dir[0]])
