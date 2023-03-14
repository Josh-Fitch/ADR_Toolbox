"""Score large objects"""
import numpy as np
import matplotlib.pyplot as plt
from adr_toolbox.space_env import SpaceEnv
from adr_toolbox.util import load_data, save_data

all_leo = load_data("full_leo_env_2024")

leo_scoring = SpaceEnv()
# Pull in data for leo objects with RCS > 1m^2
leo_scoring.from_api_data("large_leo_data")

# Propagate these objects to Jan 1st 2024
leo_scoring.propagate_env(2024)

# Apply CSI scoring to large objects based on full leo spatial density
leo_scoring.score_env(all_leo.spatial_density)

# Filter down the SpaceEnv instance to the top X scored objects
NUM_OBJS = 100
leo_scoring.filter_top_scores(NUM_OBJS)

save_data(leo_scoring, f"top_{NUM_OBJS}_CSI_scored_debris")

alts = []
incs = []
raans = []
eccs = []
for sat in leo_scoring.sat_dict.values():
    alts.append(sat.orbit_mean[0] - 6378)
    incs.append(sat.orbit_mean[1])
    raans.append(sat.orbit_mean[2])
    eccs.append(sat.orbit_mean[3])

# Plot the distribution of key orbital elements top X objects
fig = plt.figure(1)
plt.scatter(incs, alts)
plt.title(f"Altitude and Inclination Distribution of Top {NUM_OBJS} Objects")
plt.xlabel("Inclination [degs]")
plt.ylabel("Altitude [km]")
plt.grid()

fig = plt.figure(2)
plt.scatter(np.linspace(1,NUM_OBJS,NUM_OBJS), eccs)
plt.title(f"Eccentricity Distribution of Top {NUM_OBJS} Objects")
plt.xlabel("Object")
plt.ylabel("Eccentricity")
plt.grid()

fig = plt.figure(3)
plt.scatter(raans, alts)
plt.title(f"Altitude and RAAN Distribution of Top {NUM_OBJS} Objects")
plt.xlabel("Right Ascension of Ascending Node [degs]")
plt.ylabel("Altitude [km]")
plt.grid()

plt.show()
