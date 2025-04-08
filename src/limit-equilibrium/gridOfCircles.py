from base_classes import np
from circularSlipSurface import circularSlipSurface

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


def computeEtaMinForSurface(ground_surface,bounding_box,in_pt,out_pt):
    test_pts=np.linspace(in_pt,out_pt,500)
    gl=ground_surface(test_pts)
    eta_max=np.pi/2
    eta_min=np.arctan((gl[0]-gl[-1])/(in_pt-out_pt))
    eta_mid=(eta_max+eta_min)/2
    for iter in range(1,int(np.ceil(np.log2(eta_max/eta_min)))+2):
        lower=circularSlipSurface.fromInOutAndEta(ground_surface,bounding_box,in_pt,out_pt,eta_mid)
        test_circ=gl-lower.slip_surface(test_pts)
        if np.any(test_circ<0):
            eta_min=eta_mid
            eta_mid=(eta_max+eta_min)/2
        else:
            eta_max=eta_mid
            eta_mid=(eta_max+eta_min)/2
    return eta_mid
    
