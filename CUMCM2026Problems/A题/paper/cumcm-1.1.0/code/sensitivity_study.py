"""Sensitivity with Celsius offsets and explicit transport/geometric perturbations."""
import json
from dataclasses import replace
import numpy as np
from scipy.interpolate import PchipInterpolator
import solve_drying as s


def scaled_property(prop, factor):
    def wrapped(t,c):
        rho,cp,k,d=prop(t,c)
        return rho,cp,k,d*factor
    wrapped.moisture_exponent=prop.moisture_exponent
    return wrapped


def run():
    env=s.load_environment(); history=s.load_radius_history()
    original_q4=s.property_q4;original_hm=s.H_M
    cases=[('baseline',0,1,1,1,1),('temperature_minus_2C',-2,1,1,1,1),
           ('temperature_plus_2C',2,1,1,1,1),('ambient_moisture_minus_5pct',0,.95,1,1,1),
           ('ambient_moisture_plus_5pct',0,1.05,1,1,1),('diffusivity_minus_5pct',0,1,.95,1,1),
           ('diffusivity_plus_5pct',0,1,1.05,1,1),('mass_transfer_minus_5pct',0,1,1,.95,1),
           ('mass_transfer_plus_5pct',0,1,1,1.05,1),('shrinkage_amplitude_minus_5pct',0,1,1,1,.95),
           ('shrinkage_amplitude_plus_5pct',0,1,1,1,1.05)]
    results={}
    try:
        for name,offset,ce,ds,hs,rs in cases:
            s.H_M=original_hm*hs
            s.property_q4=scaled_property(original_q4,ds)
            kwargs=dict(dt_s=20.,output_interval_s=3600.,nodes=81,early_dt_s=2.,
                        terminal_temp_offset_c=offset,terminal_moisture_scale=ce)
            radius=s.R_FIXED-(s.R_FIXED-history.radius_m)*rs
            interp=PchipInterpolator(history.time_s,radius)
            rh=replace(history,radius_m=radius,interp=interp,derivative=interp.derivative())
            if rs!=1:
                q3_h=results['baseline']['q3_drying_time_h']
            else:
                q3=s.simulate_fixed(env,scaled_property(s.property_q23,ds),None,
                                    stop_at_threshold=True,**kwargs)
                q3_h=q3['threshold_time_s']/3600
            q4=s.simulate_moving(env,rh,**kwargs)
            results[name]=dict(q3_drying_time_h=q3_h,q4_drying_time_h=q4['threshold_time_s']/3600,
                               temperature_offset_c=offset,ambient_moisture_scale=ce,
                               diffusivity_scale=ds,mass_transfer_scale=hs,shrinkage_amplitude_scale=rs,
                               nodes=81,dt_s=20,early_dt_s=2)
            s.write_summary(s.RESULTS_DIR/'sensitivity.json',results)
            print(json.dumps({name:results[name]}),flush=True)
    finally:
        s.H_M=original_hm;s.property_q4=original_q4

if __name__=='__main__':
    run()
