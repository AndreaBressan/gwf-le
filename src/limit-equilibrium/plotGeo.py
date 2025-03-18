import matplotlib.pyplot as plt
import matplotlib.patches as plp
import matplotlib.transforms as pltr
import matplotlib as mpl
import matplotlib.cm as cm
import numpy as np

p=np.vectorize(lambda x: f[1] if(x>=f[0]) else x*f[1]/f[0] if(x>0.0) else 0.0)

def plotGeo(geometry,name):
    ocra=(205/255,133/255,63/255)
    ocra2=(205/511,133/511,63/511)
    red=(1,0,0)

    xs=np.linspace(geometry.bounding_box[0,0],geometry.bounding_box[0,1],600)
    gs=geometry.ground_surface(xs)
    bt=geometry.bounding_box[1,0]*np.ones_like(gs)

    plt.fill_between(xs, gs, bt, interpolate=True, color=ocra)
    plt.plot(xs, gs, lw=1,color=ocra2)
    plt.ylim((geometry.bounding_box[1,0],geometry.bounding_box[1,1]))
    plt.xlim((geometry.bounding_box[0,0],geometry.bounding_box[0,1]))

    xl=np.linspace(geometry.landslide_interval[0],geometry.landslide_interval[1],300)
    yl=geometry.slip_surface(xl)
    
    plt.plot(xl, yl, lw=1,color=red)
    plt.title('Geometry plot')
    plt.savefig( name)



