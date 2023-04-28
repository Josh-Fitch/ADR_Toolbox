"""Test RAAN Precession"""
import numpy as np
import matplotlib.pyplot as plt
from astropy import units as u
from poliastro.bodies import Earth

# Set up some useful astrodynamic constants
MU_E = Earth.k.to_value(u.km**3 / u.s**2)
R_E = Earth.R_mean.to_value(u.km)
J2 = 1.08262668e-3

def calc_raan_dot(smj_ax, inc):
    """
    Compute RAAN precession

    Accepts:
        - smj_ax (float) [km]: semi-major axis in km
        - inc (float) [degs]: inclination in degrees

    Returns:
        - raan_dot (float) [degs/s]: raan precession in degrees per second
    """
    return np.rad2deg(-3/2 * J2 * R_E**2 / smj_ax**2 * \
        np.sqrt(MU_E / smj_ax**3) * np.cos(np.deg2rad(inc)))

fig = plt.figure()
smj_ax_list = np.linspace(600, 900, 21)
inc_list = np.linspace(65, 70, 21)
raan = np.zeros((len(smj_ax_list), len(inc_list)))
for i, smj_ax in enumerate(smj_ax_list):
    for j, inc in enumerate(inc_list):
        raan[i][j] = calc_raan_dot(R_E + smj_ax, inc)
plt.imshow(raan, cmap='hot', interpolation='none', extent=[65, 70, 600, 900], aspect='auto')
plt.title("RAAN Variation in Debris Cluster 1")
plt.xlabel("Inclination [degs]")
plt.ylabel("Altitude [km]")
plt.colorbar()
plt.show()
