"""Independent flux quadrature, cylindrical eigenmode, and closed-shrinkage checks."""
import json
import math
import numpy as np
from scipy.integrate import quad
from scipy.special import j0, j1
import solve_drying as s


def run():
    flux_errors=[]
    for prop in [s.property_q1,s.property_q23,s.property_q4]:
        for lo,hi in [(0.05,0.15),(0.05,2.55),(1,1.0001)]:
            got=s.moisture_faces(np.array([50.,50.]),np.array([lo,hi]),prop)[0]
            expected=quad(lambda c:float(prop(np.array([50.]),np.array([c]))[3][0]),lo,hi,epsabs=1e-25)[0]/(hi-lo)
            flux_errors.append(abs(got/expected-1))
    assert max(flux_errors)<1e-6
    benchmark=[]
    radius=.02;diffusivity=1e-7;beta=1.0
    h=diffusivity/radius*beta*j1(beta)/j0(beta)
    for n in [41,81,161]:
        r=np.linspace(0,radius,n);old=j0(beta*r/radius);dt=.5
        for i in range(1200):
            old=s.implicit_radial_step(old,np.ones(n),np.full(n,diffusivity),dt,r,1,2*math.pi*radius*h,0)
        exact=j0(beta*r/radius)*np.exp(-diffusivity*beta**2*600/radius**2)
        benchmark.append({'nodes':n,'dt_s':dt,'max_abs_error':float(np.max(abs(old-exact)))})
    assert benchmark[-1]['max_abs_error']<2e-5
    # No heat or mass exchange, uniform material state: shrinkage alone must not change C.
    old_ht,old_hm=s.H_T,s.H_M
    try:
        s.H_T=s.H_M=0
        t=np.full(41,28.);c=np.full(41,2.55)
        for radius in [.02,.018,.015,.012]:
            t,c,_=s.advance_coupled(t,c,10,radius,-1e-6,28,2.55,s.property_q4,True)
        uniform_error=float(np.max(abs(c-2.55)))
        assert uniform_error<1e-10
    finally:
        s.H_T,s.H_M=old_ht,old_hm
    payload={'kirchhoff_quadrature_max_relative_error':max(flux_errors),
             'bessel_robin_eigenmode':benchmark,'closed_uniform_shrinkage_max_error':uniform_error,
             'all_pass':True}
    s.write_summary(s.RESULTS_DIR/'independent_numerics.json',payload)
    print(json.dumps(payload,indent=2))

if __name__=='__main__':
    run()
