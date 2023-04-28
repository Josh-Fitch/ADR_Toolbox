"""Test Poliastro function
https://docs.poliastro.space/en/stable/autoapi/poliastro/twobody/thrust/change_a_inc/index.html
"""
import numpy as np
from astropy import units as u
import poliastro.twobody.thrust as model
import matplotlib.pyplot as plt
import scienceplots # pylint: disable=unused-import
plt.style.use('science')
plt.rcParams.update({'font.size': 22})

MU = 398600.440 # km^3/s^2
THRUST = 360e-3 # Newtons
MASS = 3000 # kg
NUM_ENGINES = 1
A0 = 6378 + 800 # km
I0 = 67 # degs
AF = 6378 + 900 # km
IF = 68 # degs

k = MU << u.km**3 / u.s**2
a_0 = A0 << u.km
a_f = AF << u.km
inc_0 = np.deg2rad(I0) << u.rad
inc_f = np.deg2rad(IF) << u.rad
f = THRUST / MASS * NUM_ENGINES << u.m / u.s**2
out = model.change_a_inc(k, a_0, a_f, inc_0, inc_f, f)

print(out[1])
print(out[2] / 60 / 60 / 24)

# Evaluate dependence on acceleration
a0s = [600, 700] << u.km
afs = [800, 900] << u.km
dVs = [[[],[]],[[],[]]]
inc0 = 50 << u.deg
incf = 52 << u.deg
fs = [1e-6, 1e-5, 1e-4, 1e-3, 1e-2]
for i, a0 in enumerate(a0s):
    for j, af in enumerate(afs):
        for f in fs:
            out = model.change_a_inc(k, a0, af, inc0, incf, f << u.m / u.s**2)
            dVs[i][j].append(out[1])

# Plot Performance-Cost Pareto Frontier
fig = plt.figure()
ax = plt.axes()
ax.plot(fs, dVs[0][0], label="a0=600; af=800", ls='-', marker='.')
ax.plot(fs, dVs[0][1], label="a0=600; af=900", ls='-', marker='.')
ax.plot(fs, dVs[1][0], label="a0=700; af=800", ls='-', marker='.')
ax.plot(fs, dVs[1][1], label="a0=700; af=900", ls='-', marker='.')
ax.legend()
#plt.title("Low-Thrust ToF Dependence on Acceleration for 2 degree Inclination Change")
plt.xlabel("Thrust Acceleration [$m/s^2$]")
plt.ylabel("$\Delta$V [km/s]")
#ax.set_yscale('log')
ax.set_xscale('log')
plt.show()
