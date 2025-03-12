import base_classes
import numpy as np

class circularSplipSurface:
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
        self.slip_surface= lambda x : self.center[1]-np.sqrt( self. radius**2-(self.center[0]-x)**2)
        self.slip_tangent= lambda x : (self.center[0]-x)/np.sqrt( self. radius**2-(self.center[0]-x)**2)

    @classmethod
    def fromCenterAndRadious(cls, ground_surface, bounding_box, center, radius):
        r=radius
        c=center
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
        ys=profilo(xs)

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
        alpha=eta-np.arcsin((m[1]-out_pt[1])/nue*2)
        if alpha>0:
            r=nue/np.sin(alpha)/2
            d=(1-np.cos(alpha))*r
            c=m+(r-d)*ortho(m,in_pt)
        else:
            r=+np.Infinity
            c=np.array([(-1)**int(ux>ex)*np.Infinity,np.Infinity])
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
            r=+np.Infinity
            c=np.array([(-1)**int(ux>ex)*np.Infinity,np.Infinity])
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


def ortho(pt1,pt2):
    dir=pt2-pt1
    dir=dir/np.linalg.norm(dir)
    return np.array([-dir[1],dir[0]])
#
#def plotSeg(pt1,pt2,label=None):
#    plt.plot([pt1[0],pt2[0]],[pt1[1],pt2[1]],color='r')
#    if not label is None:
#        plt.annotate(label, (pt1+pt2)/2, ha='center')
#
#def plotAng(c,r1,r2,label=None):
#    r1=r1/np.linalg.norm(r1)
#    r2=r2/np.linalg.norm(r2)
#    clip=plp.Polygon([c+r1,c,c+r2],closed=False,color='r',fill=False)
#    circ=plp.Circle(c,.75, clip_on=True,color='r',fill=False)
#    ax = plt.gca()
#    ax.add_patch(clip)
#    ax.add_patch(circ)
#    circ.set_clip_path(clip)
#    if not label is None:
#        plt.annotate(label, c+.375*(r1+r2), ha='center')
#
#def plotCircle(circ,param=False,color='r'):
#    if np.isinf(circ.r):
#        plotSeg(circ.out_pt,circ.in_pt)
#    else:
#        x_min=min(circ.out_pt[0],circ.in_pt[0])
#        x_max=max(circ.out_pt[0],circ.in_pt[0])
#        y_min=circ.c[1]-circ.r if (circ.c[0]>x_min and circ.c[0]<x_max) else min(circ.out_pt[1],circ.in_pt[1])
#        y_max=max(circ.out_pt[1],circ.in_pt[1])
#        clipBox=plp.Rectangle([x_min,y_min],x_max-x_min,y_max-y_min,fill=False, facecolor="none", edgecolor="none")
#        c=plp.Circle(circ.c,circ.r,clip_on=True,color=color,fill=False)
#        if param:
#            txt="${var}={value:.1f}$"
#            txt2="${var}=({v1:.1f},{v2:.1f})$"
#            txt3="${var}={value:.1f} \pi$"
#            plt.plot(circ.c[0], circ.c[1], 'ro')
#            plt.annotate(txt2.format(var="\mathbf{c}",v1=circ.c[0],v2=circ.c[1]),circ.c)
#            plt.annotate(txt2.format(var="\mathbf{out_pt}",v1=circ.out_pt[0],v2=circ.out_pt[1]),circ.out_pt)
#            plt.annotate(txt2.format(var="\mathbf{in_pt}",v1=circ.in_pt[0],v2=circ.in_pt[1]),circ.in_pt)
#            plotSeg(circ.c,circ.out_pt,txt.format(var="r",value=circ.r))
#            plotSeg(circ.out_pt,circ.in_pt,"$\overline{\mathbf{ue}}$")
#            dir=circ.m-circ.c
#            dir=dir/np.linalg.norm(dir)*circ.d
#            de=circ.m+dir
#            plotSeg(circ.m,de,txt.format(var="d",value=circ.d))
#            plotAng(circ.in_pt,[1,0],ortho(circ.c,circ.in_pt),txt3.format(var="\\eta",value=circ.eta/np.pi))
#            plotAng(circ.c,circ.m-circ.c,circ.in_pt-circ.c,txt3.format(var="\\alpha",value=circ.alpha/np.pi))
#        ax = plt.gca()
#        ax.add_patch(clipBox)
#        ax.add_patch(c)
#        c.set_clip_path(clipBox)