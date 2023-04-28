"""Test CSI Calculations"""
import numpy as np
import matplotlib.pyplot as plt

altitude = [300, 400, 500, 600, 700, 800, 900, 1000]

lifetime = []
for alt in altitude:
    life = np.exp(14.18 * alt ** 0.1831 - 42.94)
    lifetime.append(life)

fig = plt.figure()
ax = plt.axes()
sc = ax.scatter(altitude, lifetime, s=30)
plt.title("Orbital Lifetime as a Function of Altitude")
plt.xlabel("Altitude [km]")
plt.ylabel("Lifetime [years]")
plt.yscale("log")
plt.grid()

plt.show()
