"""Full-duration axisymmetric validation with matched 1D grid and time step.

z=0 is the symmetry mid-plane; z=L/2 is the exposed end.
For Q4 both solvers use the homogeneous material-shrinkage closure.
"""
import json, math, sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
import solve_drying as m

LENGTH=.25

def geometry(nr,nz,radius):
    r=m.radial_grid(nr,radius);z=m.radial_grid(nz,LENGTH/2)
    area,_=m.node_control_volumes(r)
    faces=(z[1:]+z[:-1])/2
    dz=np.diff(np.r_[0.,faces,LENGTH/2])
    return r,z,area,dz,area[:,None]*dz[None,:]


def step2d(old,storage,k,dt,h,ambient,geom):
    r,z,area,dz,volume=geom;nr,nz=old.shape
    ids=np.arange(nr*nz).reshape(nr,nz)
    a=ids[:-1,:].ravel();b=ids[1:,:].ravel()
    gr=(2*np.pi*((r[1:]+r[:-1])/2)[:,None]*dz[None,:]*
        (k[1:,:]+k[:-1,:])/2/np.diff(r)[:,None]).ravel()
    c=ids[:,:-1].ravel();d=ids[:,1:].ravel()
    gz=(area[:,None]*(k[:,1:]+k[:,:-1])/2/np.diff(z)[None,:]).ravel()
    first=np.r_[a,c];second=np.r_[b,d];g=np.r_[gr,gz]
    capacity=(storage*volume/dt).ravel()
    diagonal=capacity+np.bincount(first,weights=g,minlength=old.size)+np.bincount(second,weights=g,minlength=old.size)
    rhs=capacity*old.ravel()
    side=ids[-1,:];end=ids[:,-1]
    bs=h*2*np.pi*r[-1]*dz;be=h*area
    diagonal[side]+=bs;rhs[side]+=bs*ambient
    diagonal[end]+=be;rhs[end]+=be*ambient
    ix=np.arange(old.size)
    matrix=coo_matrix((np.r_[diagonal,-g,-g],(np.r_[ix,first,second],np.r_[ix,second,first])),shape=(old.size,old.size)).tocsc()
    return spsolve(matrix,rhs).reshape(old.shape)


def run_case(question,nr,nz,dt):
    env=m.load_environment();rh=m.load_radius_history()
    prop={1:m.property_q1,3:m.property_q23,4:m.property_q4}[question]
    temperature=np.full((nr,nz),m.INITIAL_T);moisture=np.full_like(temperature,m.INITIAL_C)
    one_t=temperature[:,0].copy();one_c=moisture[:,0].copy()
    td2=td1=None;maxdiff_t=maxdiff_c=0.;max_end_c=0.;max_location=None
    previous2=previous1=m.INITIAL_C
    maximum=1800 if question==1 else (float(rh.time_s[-1]) if question==4 else 4*86400)
    steps=0
    for t in np.arange(dt,maximum+dt/2,dt):
        radius=rh.values(float(t))[0] if question==4 else m.R_FIXED
        geom=geometry(nr,nz,radius)
        ambient_t,ambient_c=env.values(float(t))
        guess_t=temperature.copy();guess_c=moisture.copy()
        for iteration in range(30):
            rho,cp,k,_=prop(guess_t,guess_c)
            new_t=step2d(temperature,rho*cp,k,dt,m.H_T,ambient_t,geom)
            _,_,_,diffusivity=prop(new_t,guess_c)
            new_c=step2d(moisture,np.ones_like(moisture),diffusivity,dt,m.H_M,ambient_c,geom)
            et=np.max(np.abs(new_t-guess_t));ec=np.max(np.abs(new_c-guess_c))
            guess_t,guess_c=new_t,new_c
            if et<1e-8 and ec<1e-10: break
        else: raise RuntimeError('2D Picard failed')
        temperature,moisture=guess_t,guess_c
        one_t,one_c,_=m.advance_coupled(one_t,one_c,dt,radius,0.,ambient_t,ambient_c,prop,question==4)
        maxdiff_t=max(maxdiff_t,float(np.max(np.abs(temperature[:,0]-one_t))))
        maxdiff_c=max(maxdiff_c,float(np.max(np.abs(moisture[:,0]-one_c))))
        max_end_c=max(max_end_c,float(np.max(np.abs(moisture[:,-1]-moisture[:,0]))))
        current2=float(moisture.max());current1=float(one_c.max())
        if td2 is None and current2<=m.THRESHOLD_C:
            td2=float(t-dt+dt*(previous2-m.THRESHOLD_C)/(previous2-current2))
            ij=np.unravel_index(np.argmax(moisture),moisture.shape)
            max_location=[float(geom[0][ij[0]]),float(geom[1][ij[1]])]
        if td1 is None and current1<=m.THRESHOLD_C:
            td1=float(t-dt+dt*(previous1-m.THRESHOLD_C)/(previous1-current1))
        previous2,previous1=current2,current1;steps+=1
        if steps%720==0:print('2D',question,nr,nz,'time h',t/3600,flush=True)
        if td2 is not None and td1 is not None:break
    return {'question':question,'nr':nr,'nz':nz,'dt_s':dt,'end_s':float(t),
        'terminal_temperature_c':m.TERMINAL_TEMPERATURE_C,'terminal_moisture':m.TERMINAL_MOISTURE,
        'threshold_2d_h':None if td2 is None else td2/3600,'threshold_matched_1d_h':None if td1 is None else td1/3600,
        'relative_threshold_difference':None if td2 is None else abs(td2-td1)/td2,
        'global_control_r_z_m':max_location,'whole_run_midplane_max_temperature_difference':maxdiff_t,
        'whole_run_midplane_max_moisture_difference':maxdiff_c,
        'whole_run_end_midplane_max_moisture_difference':max_end_c,
        'final_midplane_temperature_difference':float(np.max(np.abs(temperature[:,0]-one_t))),
        'final_midplane_moisture_difference':float(np.max(np.abs(moisture[:,0]-one_c)))}


def run():
    path=m.RESULTS_DIR/'long_2d_verification.json'
    previous=json.loads(path.read_text()) if path.exists() else []
    # Q1 ends before the terminal boundary begins and remains valid. Recompute
    # every long-duration Q3/Q4 case whenever this script is run.
    records=[x for x in previous if x['question']==1]
    for q,nr,nz,dt in [(3,41,21,30.),(4,41,21,30.),(3,81,41,30.),(4,81,41,30.)]:
        record=run_case(q,nr,nz,dt);records.append(record)
        path.write_text(json.dumps(records,indent=2));print(record,flush=True)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');run()
