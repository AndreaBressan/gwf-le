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
import scipy.optimize as optimize


class GLE_model(umbridge.Model):

    def __init__(self):
        super().__init__("forward")

    def get_input_sizes(self, config):
        return [1]

    def get_output_sizes(self, config):
        return [1]

    def __call__(self, parameters, config):

        ground_surface=lambda x : 0*(x<=0)+ x*(0<x)*(x<=3) + 3*(x>3)
        bounding_box=np.array([[-5,10],[-5,9]])

        gOptions=GridOptions(
            in_interval=[2,10],
            out_interval=[-5,1],
            min_eta_inc=np.radians(7),
            num_in_pts=15,
            num_out_pts=15)
  
        constant_dry_density=18.0
        soil_properties=SoilProperties( 
            cohesion       = lambda x,y : parameters[0][0]*np.ones_like(x+y),
            friction_angle = lambda x,y : 30.0*np.ones_like(x+y),
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
            quadrature = lambda interval : UniformQuadrature(x_interval=interval,num=50) 
            )

        res=gridComputation(morgerstern_price, ground_surface,bounding_box,soil_properties,soil_state,gOptions,mOptions)[0][0]
	
        triplet = res.inputs[0].slip_surface;

        return [[res.factor_of_safety]]


        #return [res.factor_of_safety, res.inputs[0].slip_surface.in_pt, res.inputs[0].slip_surface.out_pt, np.degrees(res.inputs[0].slip_surface.eta)]

    def supports_evaluate(self):
        return True


model = GLE_model()

umbridge.serve_models([model], 4242)
