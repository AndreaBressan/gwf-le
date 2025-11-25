import time
from gridOfCircles import gridOfCircles
from ..LEM.base_classes import UniformQuadrature,Options,np


class GridOptions:
    def __init__(self,in_interval,out_interval,min_eta_inc=np.radians(5),num_in_pts=10,num_out_pts=10):
        self.in_interval=in_interval
        self.out_interval=out_interval
        self.min_eta_inc=min_eta_inc
        self.num_in_pts=num_in_pts
        self.num_out_pts=num_out_pts



def gridComputation(method,ground_surface, bounding_box,soil_properties,soil_state,gridOptions,methodOptions):
    geometries=gridOfCircles(ground_surface, bounding_box, gridOptions.in_interval,gridOptions.out_interval,gridOptions.min_eta_inc,gridOptions.num_in_pts,gridOptions.num_out_pts)
    time_start = time.perf_counter()
    result=[method(geometry,soil_properties,soil_state,methodOptions) for geometry in geometries]
    time_duration = time.perf_counter()- time_start
    result.sort(key=lambda x: x.factor_of_safety)
    return result,time_duration