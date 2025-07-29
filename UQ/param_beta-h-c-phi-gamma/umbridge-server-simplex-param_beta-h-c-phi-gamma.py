import umbridge
import sys
import numpy as np
import time
sys.path.append("../../src/limit-equilibrium")
from base_classes import SoilProperties,SoilState,UniformQuadrature,Options,np,plt
from circularSlipSurface import circularSlipSurface
from bishop import bishop
from gle import spencer,morgerstern_price
from gridOfCircles import GridOptions, gridComputation,computeEtaMinForSurface
from gridSimplexComputation import simplexComputation


class bishop_parametric(umbridge.Model):

    def __init__(self):
        super().__init__("forward")

    def get_input_sizes(self, config):
        return [5]

    def get_output_sizes(self, config):
        return [1]

    def __call__(self, parameters, config):
        beta=parameters[0][0]
        H = parameters[0][1]
        c=parameters[0][2]
        friction_angle=parameters[0][3]
        gamma=parameters[0][4]
        
        tan_beta=np.tan(np.radians(beta))
        slope_end=H/tan_beta
        dist_max=max(slope_end,H)

        ground_surface=lambda x : 0*(x<=0)+ tan_beta*x*(0<x)*(x<=slope_end) + H*(x>slope_end)
        bounding_box=np.array([[-5,dist_max+5],[-5,dist_max+5]])

        gOptions=GridOptions(
            in_pts=[1.*slope_end,1/3*dist_max+slope_end, 2/3*dist_max+slope_end, 1*dist_max+slope_end],
            out_pts=[-1*dist_max,-1/2*dist_max ,-1/4*dist_max, 0., 1/8*slope_end, 1/4*slope_end],
            min_eta_inc=np.radians(5),
            num_in_pts=None,
            num_out_pts=None)

        constant_dry_density=gamma
        phi  = friction_angle # angolo d'attrito
        soil_properties=SoilProperties( 
            cohesion       = lambda x,y : c*np.ones_like(x+y),
            friction_angle = lambda x,y : phi*np.ones_like(x+y),
            dry_density    = lambda x,y : constant_dry_density*np.ones_like(x+y),
            porosity       = lambda x,y : 0.0*np.ones_like(x+y),
            grain_density  = lambda x,y : 0.0*np.ones_like(x+y)
            )
        soil_state=SoilState(
            saturation         = lambda x,y : 1.0*np.ones_like(x+y),
            pore_pressure      = lambda x,y : 0.0*np.ones_like(x+y),
            integrated_density = lambda x,y : constant_dry_density*(ground_surface(x)-y)
            )
        mOptions=Options(
            max_iteration = 200,
            tolerance = 1e-4,
            quadrature = lambda interval : UniformQuadrature(
                x_interval=interval,
                num=50
                ) 
            )
        bounds = ((1*slope_end,5*dist_max+slope_end), 
          (-5*dist_max,1/4*slope_end), 
          (0., 90))
        res=simplexComputation(bishop, ground_surface,bounding_box,soil_properties,soil_state,gOptions,mOptions,bounds)[0]
        print(res)
        return [[res.fun]]

    def supports_evaluate(self):
        return True


model = bishop_parametric()
umbridge.serve_models([model], 4242)
