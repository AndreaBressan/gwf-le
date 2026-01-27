# -*- coding: utf-8 -*-
"""
Created on 2026-01-20

@author: Leonardo Lalicata, Andrea Bressan, Simone Pittaluga

general limit equilibrium methods
"""
import numpy as np
import lemInterface

def slices_bottom_data(geometry : Geometry, soil :Soil, options: lemOptions) -> dict:
    quad=options.subdivision_method(geometry.landslide_interval)
    #"geometric properties"
    x_nodes=quad.nodes
    y_nodes=geometry.slip_surface(x_nodes)
    t_nodes=geometry.slip_tangent(x_nodes)
    l_nodes=np.sqrt(1+t_nodes**2)
    cos=1/l_nodes
    sin=np.sqrt(1-cos**2)*np.sign(t_nodes)
    depth = geometry.ground_surface(x_nodes)-y_nodes
    #"soil and water properties" 
    tan_phi=np.tan(np.radians(soil.friction_angle(x_nodes,y_nodes)))
    c=soil.cohesion(x_nodes,y_nodes)*l_nodes
    u=soil.pore_pressure(x_nodes,y_nodes)*soil.saturation(x_nodes,y_nodes)*l_nodes
    w=soil.column_weight(x_nodes,y_nodes)
    return locals()


def fellenius (geometry : Geometry, soil :Soil, options : lemOptions) -> lemResult:
    slice_data=slices_bottom_data(geometry,soil, options)   
    locals().update(slice_data)
    p=w*cos 
    sign=np.sign(y_nodes[-1]-y_nodes[1])
    R=(c+(p-u)*tan_phi)*quad_weights
    O=sign*w*sin*quad_weights
    Osum=np.sum(O,0)
    slice_data.update({"p":p , "R":R, "O": O})
    return lemResult(
        method_name="Fellenius",
        factor_of_safety=np.sum(R,0)/Osum,
        Lambda=np.nan,
        optional_outputs=dict((k,slice_data[k]) for k in options.optional_outputs if k in slice_data)
        )

def bishop    (geometry : Geometry, soil :Soil, options : lemOptions) -> lemResult:
    required=["y_nodes","t_nodes","cos","sin","tan_phi","c","u","w","O"]
    sub_options=options.copy()
    sub_options.optional_output.join(required )
    start=fellenius(geometry,soil, sub_options)
    slice_data=start.optional_outputs
    locals().update(dict((k,start[k]) for k in required if k in start))
    sign=np.sign(y_nodes[-1]-y_nodes[1])
    Osum=np.sum(O)    

    def F(old_fos):
        nonlocal R, p, m_alpha
        m_alpha = cos * (1+1/old_fos * tan_phi * t_nodes*sign) 
        m_alpha = np.maximum(m_alpha,0.2)
        p=1/m_alpha*(w-1/old_fos*sin*(c-u*tan_phi)*sign)
        R=(c+(p-u)*tan_phi)*quad_weights
        increment = old_fos - np.sum(R,0)/Osum
        return increment

    from scipy import optimize

    Bishop_result = optimize.newton(
                func=F, x0=start.factor_of_safety,
                tol=options.tolerance,
                maxiter=options.max_iteration
                )
    slice_data.update({"p":p , "R":R, "O": O , "m_alpha": m_alpha})
    return lemResult(
        method_name="Bishop",
        factor_of_safety=np.max(Bishop_result, start.factor_of_safety),
        Lambda= 0.0,
        optional_outputs=dict((k,[k]) for k in options.optional_outputs if k in slice_data)
        )



def morgerstern_price(geometry : Geometry, soil :Soil, options : lemOptions) -> lemResult:
    return gle(geometry, soil, options, lambda x : np.sin(np.pi*x ), "Morgestern-Price")


def spencer(geometry : Geometry, soil :Soil, options : lemOptions) -> lemResult:
    return gle(geometry, soil, options, lambda x : 1, "Spencer")


def gle( geometry : Geometry, soil :Soil, options : lemOptions, lambdaFunc, name="GLE with given f") -> lemResult:
    required=["y_nodes","t_nodes","cos","sin","tan_phi","c","u","w","O"]
    sub_options=options.copy()
    sub_options.optional_output.join(required )
    start=bishop(geometry,soil, sub_options)
    slice_data=start.optional_outputs
    locals().update(dict((k,start[k]) for k in required if k in start))
    
    FoS_Bishop=start.factor_of_safety

    # TODO fix orientation of the slope!!
    # TODO lateral cohesion and forces
    
    L=geometry.landslide_interval[0]-geometry.landslide_interval[1]
    f_x=f((geometry.landslide_interval[0]-x_nodes)/L)
    p=w*cos
    S=(c + ( p - u ) * tan_phi)*quad_weights
    O=w*sin*quad_weights
    Osum=np.sum(O,0)
    
    def F(x):
        nonlocal R, p, m_alpha, Q, S, E

        m_alpha = cos * (1+ tan_phi * t_nodes / x[0])
        m_alpha = np.maximum(m_alpha,0.2)
        m_alpha_star = sin - cos * tan_phi / x[0] 

        Q = x[1]*f_x
        den = (m_alpha + m_alpha_star* Q)
        p =( w - ( sin - cos*Q ) * ( c - u*tan_phi ) / x[0] ) / den
        s = c + ( p - u ) * tan_phi
        S=s*quad_weights
        P=np.maximum(p*quad_weights,0)                           # force normal to the slice always compressive
        dE = P*sin - S*cos/x[0]                                  # increment in the normal force at the side of the slices
        E  = np.maximum(np.cumsum(dE), 1.e-6)
        c_vert = c/l_nodes*depth                                 # cohesion along the height of the slice
        X  = np.minimum(Q*E , c_vert + E*tan_phi)                # shear force at the side of each slice, limited by the strength of the material
        Q_check = X/E

        rot_FoS   = (np.sum(S)/Osum - x[0])
        trasl_FoS = (np.sum(S * cos)/np.sum(P * sin) - x[0])
        if np.any(Q>Q_check):
            return [np.inf, np.inf]
        else:
            return [rot_FoS,trasl_FoS]

    from scipy import optimize

    Lambda=0.3
    root=optimize.root(
            fun=F, x0=[FoS_Bishop, Lambda],
            tol=options.tolerance
            )
    slice_data.update({"p":p , "R":R, "O": O , "m_alpha": m_alpha, "S":S})
    return lemResult(
        method=name,
        factor_of_safety = root.x[0],
        Lambda = root.x[1],
        optional_outputs=dict((k,[k]) for k in options.optional_outputs if k in slice_data)
    )

# TODO check names of the following and if they are needed
#bc.Result(
#        method=name,
#        factor_of_safety = root.x[0],
#        Lambda = root.x[1],
#        nodes=np.vstack((x_nodes,y_nodes)),
#        depths=geometry.ground_surface(x_nodes)-y_nodes,
#        weight_forces=w*quad_weights,
#        resisting_forces=S,
#        resisting_cohesive=c*quad_weights,
#        resisting_frictional=(p-u)*tan_phi*quad_weights,
#        inter_slice_forces=np.zeros((2,len(x_nodes))),
#        inputs=(geometry, soil_properties, soil_state, options)
#        )
