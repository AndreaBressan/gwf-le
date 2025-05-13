from base_classes import np
from circularSlipSurface import circularSlipSurface
import time
from base_classes import UniformQuadrature,Options,np

def gridOfCircles(ground_surface, bounding_box, in_interval,out_interval,min_eta_inc,num_in_pts,num_out_pts):
    in_pts=np.linspace(in_interval[0],in_interval[1],num_in_pts)
    out_pts=np.linspace(out_interval[0],out_interval[1],num_out_pts)
    out_geometries=[]
    for i in in_pts:
        for o in out_pts:
            eta_min=computeEtaMinForSurface(ground_surface,bounding_box,i,o)
            eta_max=np.pi/2
            num_eta=np.floor((eta_max-eta_min)/min_eta_inc)
            eta=np.linspace(eta_min,eta_max,int(num_eta))
            for e in eta:
                out_geometries.append(circularSlipSurface.fromInOutAndEta(ground_surface,bounding_box,i,o,e))
    return out_geometries


def computeEtaMinForSurface(ground_surface,bounding_box,in_pt,out_pt,npts=500,tol=1e-4):
    test_pts=np.linspace(in_pt,out_pt,npts)
    # prova
    gl=ground_surface(test_pts)
    eta_max=np.pi/2
    eta_min=np.arctan((gl[0]-gl[-1])/(in_pt-out_pt))
    eta_mid=(eta_max+eta_min)/2
    test_pts=test_pts[1:-2]
    gl=gl[1:-2]
    
    for iter in range(0,20):
        mid_surf=circularSlipSurface.fromInOutAndEta(ground_surface,bounding_box,in_pt,out_pt,eta_mid)
        test=mid_surf.slip_surface(test_pts)
        if np.all(gl>test):
            eta_max=eta_mid
        else:
            eta_min=eta_mid
        eta_mid=(eta_max+eta_min)/2
    return eta_mid
    
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