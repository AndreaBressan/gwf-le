import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.LEM.lemInterface import Geometry
from src.LEM.geometryPlot import *


geo=Geometry(lambda x:x+1, lambda x: x*x, lambda x: 2*x,np.array([1-np.sqrt(5),1+np.sqrt(5)])/2)

pltGeo=GeometryPlot(geo,np.array([[-2,2],[-1,3]]))
plt.figure()
pltGeo.plot(200)

plt.show()
plt.close()
