"""Test impulsive delta-V calc"""
import numpy as np
from astropy import units as u
from poliastro.bodies import Earth
MU_E = Earth.k.to_value(u.km**3 / u.s**2)

a_0 = 6378 + 600
a_f = 6378 + 900
inc_0 = 67
inc_f = 69

# Hohmann
dv_1 = np.sqrt(MU_E / a_0) * (np.sqrt((2 * a_f)/(a_0 + a_f)) - 1)
dv_2 = np.sqrt(MU_E / a_f) * (1 - np.sqrt((2 * a_0)/(a_0 + a_f)))

# Inc change
delta_inc = np.deg2rad(np.abs(inc_0 - inc_f))
dv_3 = 2 * np.sqrt(MU_E / a_f) * np.sin(0.5 * delta_inc)

print(dv_1 + dv_2 + dv_3)

v1 = np.sqrt(MU_E / a_0)
v2 = np.sqrt(MU_E / a_f)
delta_v_3 = np.sqrt(v1**2 + v2**2 - 2*v1*v2*np.cos(np.deg2rad(np.abs(inc_0 - inc_f))))