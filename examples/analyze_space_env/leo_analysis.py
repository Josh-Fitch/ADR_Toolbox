"""Analyze LEO environment"""
import numpy as np
import matplotlib.pyplot as plt
from adr_toolbox.space_env import SpaceEnv
from adr_toolbox.util import save_data

all_leo = SpaceEnv()
# Pull in full LEO environment
all_leo.from_api_data("all_leo_data")
all_leo.propagate_env(2024)
all_leo.calc_spatial_density(10, exclude_starlink=True)
save_data(all_leo, "full_leo_env_2024")

fig = plt.figure()
ax = plt.axes()
for i in range(7):
    all_leo.propagate_env(2024 + i)
    all_leo.calc_spatial_density(20)
    plt.plot(all_leo.spatial_density.keys(), all_leo.spatial_density.values(), label=f"{2024 + i}")
ax.legend()
plt.xticks(np.linspace(200, 2200, 11))
plt.yticks(np.linspace(0, 2000, 6))
plt.title("Evolution of LEO Spatial Density Distribution with Altitude based on SGP4")
plt.xlabel("Altitude [km]")
plt.ylabel("Spatial Density [# Objects / km^3]")
plt.grid()
plt.show()
