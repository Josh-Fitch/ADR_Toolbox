"""Test Poliastro function
https://docs.poliastro.space/en/stable/autoapi/poliastro/twobody/thrust/change_a_inc/index.html
"""
from astropy import units as u
import poliastro.twobody.thrust as model
import matplotlib.pyplot as plt

MU = 398600.440 # km^3/s^2
THRUST = 60e-2 # Newtons
MASS = 3000 # kg
NUM_ENGINES = 4
A0 = 7000 # km
I0 = 28 # degs
AF = 42200 # km
IF = 0 # degs

k = MU << u.km**3 / u.s**2
a_0 = A0 << u.km
a_f = AF << u.km
inc_0 = I0 << u.deg
inc_f = IF << u.deg
f = THRUST / MASS * NUM_ENGINES << u.m / u.s**2
f = 3.5e-7 << u.km / u.s**2
out = model.change_a_inc(k, a_0, a_f, inc_0, inc_f, f)

print(out[1])
print(out[2] / 24 / 3600)

# Evaluate dependence on acceleration
a0s = [600, 700] << u.km
afs = [800, 900] << u.km
dVs = [[[],[]],[[],[]]]
inc0 = 50 << u.deg
incf = 55 << u.deg
fs = [1e-4, 5e-4, 1e-3, 5e-3, 1e-2] << u.m / u.s**2
for i, a0 in enumerate(a0s):
    for j, af in enumerate(afs):
        for f in fs:
            out = model.change_a_inc(k, a0, af, inc0, incf, f)
            dVs[i][j].append(out[2].to_value(u.s) / 24 / 3600)

# Plot Performance-Cost Pareto Frontier
fig = plt.figure()
ax = plt.axes()
ax.plot(fs, dVs[0][0], label="a0=500; af=1500", ls='-', marker='.')
ax.plot(fs, dVs[0][1], label="a0=500; af=3000", ls='-', marker='.')
ax.plot(fs, dVs[1][0], label="a0=1000; af=1500", ls='-', marker='.')
ax.plot(fs, dVs[1][1], label="a0=1000; af=3000", ls='-', marker='.')
ax.legend()
plt.title("Low-Thrust Delta-V Dependence on Acceleration")
plt.xlabel("Thrust Acceleration [m/s^2]")
plt.ylabel("Delta-V [km/s]")
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})
plt.show()
