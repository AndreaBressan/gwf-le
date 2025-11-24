import time
from gridOfCircles import gridOfCircles , computeEtaMinForSurface, gridComputation
from circularSlipSurface import circularSlipSurface
from base_classes import UniformQuadrature,Options,np, optimize

def simplexComputation(method,ground_surface, bounding_box,soil_properties,soil_state,gridOptions,methodOptions,bounds):
    def func(v):
        x_in , x_out , eta = v[0] , v[1] , np.radians(v[2])
        func.calls+=1
        eta_min=computeEtaMinForSurface(ground_surface,bounding_box,x_in,x_out)
        if eta < eta_min+1.e-3 or eta>np.pi/2 or x_in<bounds[0][0] or\
          x_in>bounds[0][1] or x_out<bounds[1][0] or x_out>bounds[1][1]:
            return np.inf
        else:
            geometry=circularSlipSurface.fromInOutAndEta(ground_surface,bounding_box,x_in,x_out,eta)
            return method(geometry,soil_properties,soil_state,methodOptions).factor_of_safety
    func.calls=0
    [result,time_duration]=gridComputation(method, ground_surface,bounding_box,soil_properties,soil_state,gridOptions,methodOptions)
    start_geo=result[0].inputs[0]
    trial=[start_geo.landslide_interval[1],start_geo.landslide_interval[0],np.degrees(start_geo.eta)]
    # probabilmente le opzioni del simplesso andrebbero definite da qualche parte
    simplex_result = optimize.minimize(func, trial , 
                          method='Nelder-Mead',
                          bounds = bounds,
                          options = {
                            'disp'      : False,
                            'xatol'     : 1e-3,
                            'fatol'     : 1e-4,
                            'maxiter'   : 100,
                            'return_all': True
                            }
                          )
    
    return simplex_result,func.calls

