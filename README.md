# gwf-le

gwf-le is a small Python library for slope stability limit equilibrium analysis. It implements standard limit equilibrium methods for slope stability, including
Fellenius's, Bishop's simplified method, Spencer's and the Morgenstern-Price method. The library is also the computational basis for the QGIS plugin RaiseOfSlope (https://github.com/pitta1981/RaiseOfSlope).

## Usage

Define slope geometry, soil materials, and pore-water pressure conditions using the library's Python classes or configuration objects. Specify parameters by creating model objects for the slope, layers, materials, and water surface, then pass them to the solver with the chosen method. 

Examples are in the validation folder. The workflow is:

- import library classes 
- define the geometry of the terrain as a function of `x`:
```python
base, height = 10.0 , 5.0
ground_surface=lambda x : 0.0*(x<=0.0)+ height * x/base*(0.0<x)*(x<=base) + height*(x>base)
```
- define the soil material properties as functions of `x` and `y`:
```python
soil=Soil.soilWithVerticalSampling(
    cohesion      =lambda x,y: c*np.ones_like(x+y),
    friction_angle=lambda x,y: phi*np.ones_like(x+y),
    pore_pressure =lambda x,y: 0.0*np.ones_like(x+y),
    saturation    =lambda x,y: 0.0*np.ones_like(x+y),
    column_weight =lambda x,y: gamma*(ground_surface(x)-y),
    num_vertical_sample=1
    )
```

Then one can either:

- evaluate a method on a specific arc described in terms of an entry abscissa `x_in` an exit abscissa `x_out` and the entry angle `η`:
```python
geometry=circularArc.fromInOutAndEta(ground_surface, 4.0, 0.0, np.radians(70))

options=lemOptions()
result=fellenius(geometry,soil,options)
result=bishop(geometry,soil,options)
result=spencer(geometry,soil,options)
result=morgerstern_price(geometry,soil,options)
```
- or find the worst arcs in a parameter-grid
```python
searchDomain=circularSlipSearchDomain(
    ground_surface=ground_surface,
    in_range=(2.,5.),
    out_range=(-.5,1.)
    )

method=lemMethod(bishop,soil,options)
gridOptions={"num_in_points":5,"num_out_points":5}
result,time=find_critical  (method, searchDomain.sample_grid(gridOptions),num_geometries=10 )
```
- or use a combined worst case search algorithm that starts form a grid and optimizes the arc using the the simplex algorithm:
```python
domain=circularSlipSearchDomain(
    ground_surface=ground_surface,
    in_range=(2.,5.),
    out_range=(-.5,1.),
)
method=lemMethod(bishop,soil,options)
grid_options={
    "in_points":np.array([3.,4.,5.]),
    "out_points":np.array([-.5,0.,.5])}
result,time,calls=grid_simplex(domain=domain,method=method,grid_options=grid_options,num_geometries=1,      options={"num_grid_output":3 })
```


See [Lalicata, L. M., Bressan, A., Pittaluga, S., Tamellini, L., & Gallipoli, D. (2025). An efficient slope stability algorithm with physically consistent parametrisation of slip surfaces. International Journal of Civil Engineering, 23(4), 671-682](https://www.sciencedirect.com/science/article/pii/S0045782524006236) for further details on the parametrization and the search algorithm.
