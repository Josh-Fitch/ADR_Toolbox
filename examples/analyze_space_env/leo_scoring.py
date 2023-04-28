"""Score large objects"""
import numpy as np
import matplotlib.pyplot as plt
import scienceplots # pylint: disable=unused-import
from adr_toolbox.space_env import SpaceEnv
from adr_toolbox.util import load_data, save_data
plt.style.use('science')
plt.rcParams.update({'font.size': 14})

all_leo = load_data("full_leo_env_2024")

leo_scoring = SpaceEnv()
# Pull in data for leo objects with RCS > 1m^2
leo_scoring.from_api_data("large_leo_data")

# Propagate these objects to Jan 1st 2024
leo_scoring.propagate_env(2024)

# Apply CSI scoring to large objects based on full leo spatial density
leo_scoring.score_env(all_leo.spatial_density)

scores = []
for sat in leo_scoring.sat_dict.values():
    if sat.score is not None:
        scores.append(sat.score)
print(sum(scores))

# Filter down the SpaceEnv instance to the top X scored objects
NUM_OBJS = 100
leo_scoring.filter_top_scores(NUM_OBJS)

top_200_scores = []
for sat in leo_scoring.sat_dict.values():
    top_200_scores.append(sat.score)
print(sum(top_200_scores))

save_data(leo_scoring, f"top_{NUM_OBJS}_CSI_scored_debris")

country_list = ["US", "CIS", "PRC", "EUME", "ESA", "JPN", "Other"]

alts = {}
incs = {}
raans = {}
eccs = {}
scores = {}
for country in country_list:
    alts[country] = []
    incs[country] = []
    raans[country] = []
    eccs[country] = []
    scores[country] = 0

others = {}
for sat in leo_scoring.sat_dict.values():
    if sat.country in country_list:
        key = sat.country
    else:
        key = "Other"
        if sat.country not in others.keys():
            others[sat.country] = 1
        else:
            others[sat.country] += 1
    alts[key].append(sat.orbit_mean[0] - 6378)
    incs[key].append(sat.orbit_mean[1])
    raans[key].append(sat.orbit_mean[2])
    eccs[key].append(sat.orbit_mean[3])
    scores[key] += sat.score
    print(f"{sat.satno}, {sat.satname}, {sat.country}, {sat.score}, {sat.obj_type}, {sat.mass}")

# Plot the distribution of key orbital elements top X objects
fig = plt.figure(1)
for key in alts.keys():
    plt.scatter(incs[key], alts[key], label=key)
#plt.title(f"Altitude and Inclination Distribution of Top {NUM_OBJS} Objects")
plt.xlabel("Inclination [degs]")
plt.ylabel("Altitude [km]")
plt.legend(loc="best")
plt.grid()

fig = plt.figure(2)
for key in alts.keys():
    plt.scatter(eccs[key], alts[key], label=key)
#plt.title(f"Eccentricity Distribution of Top {NUM_OBJS} Objects")
plt.xlabel("Eccentricity")
plt.ylabel("Altitude [km]")
plt.legend()
plt.grid()

fig = plt.figure(3)
for key in alts.keys():
    plt.scatter(raans[key], alts[key], label=key)
#plt.title(f"Altitude and RAAN Distribution of Top {NUM_OBJS} Objects")
plt.xlabel("Right Ascension of Ascending Node [degs]")
plt.ylabel("Altitude [km]")
plt.legend()
plt.grid()

fig = plt.figure(4)
for i in range(len(scores.keys())):
    plt.bar(scores.keys(), scores.values(), align='center', width=0.5)
#plt.title(f"Score Distribution by Country for Top {NUM_OBJS} Objects")
plt.xlabel("Country of Origin")
plt.ylabel("Cumulative Criticality of Spacecraft Index Score")
plt.grid()

plt.show()
