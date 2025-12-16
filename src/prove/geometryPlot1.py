import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.append("../LEM")
from lemInterface import Geometry
from geometryPlot import *


geo=Geometry(lambda x:x+1, lambda x: x*x, lambda x: 2*x,np.array([1-np.sqrt(5),1+np.sqrt(5)])/2)

pltGeo=GeometryPlot(geo,np.array([[-2,2],[-1,3]]))
plt.figure()
pltGeo.plot(200)

plt.show()
plt.close()
