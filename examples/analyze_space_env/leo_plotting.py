"""Analyze LEO environment"""
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import scienceplots # pylint: disable=unused-import
from adr_toolbox.space_env import SpaceEnv
plt.style.use('science')
plt.rcParams.update({'font.size': 16})

all_leo = SpaceEnv()
# Pull in full LEO environment
all_leo.from_api_data("all_leo_data")
all_leo.propagate_env(2024)

alts = []
incs = []
raans = []
eccs = []
masses = []
countries = {}
obj_type = {}
for sat in all_leo.sat_dict.values():
    if len(sat.orbit_mean) == 0:
        continue
    elif sat.orbit_mean[0] > 6378 + 2000 or sat.orbit_mean[0] < 6378:
        continue
    elif sat.mass is not None:
        if sat.mass > 10000:
            continue
    if sat.mass is not None:
        alts.append(sat.orbit_mean[0] - 6378)
        incs.append(sat.orbit_mean[1])
        raans.append(sat.orbit_mean[2])
        eccs.append(sat.orbit_mean[3])
        masses.append(sat.mass)
    if sat.country not in countries.keys():
        if sat.country is None:
            continue
        else:
            if sat.mass is not None:
                countries[sat.country] = sat.mass
    else:
        if sat.country is None:
            continue
        else:
            if sat.mass is not None:
                countries[sat.country] += sat.mass
    if sat.obj_type not in obj_type.keys():
        if sat.obj_type is None:
            continue
        else:
            obj_type[sat.obj_type] = 1
    else:
        if sat.obj_type is None:
            continue
        else:
            obj_type[sat.obj_type] += 1

total_mass = sum(masses)
countries_to_remove = []
for key, value in countries.items():
    if (value / total_mass) * 100 < 0.5:
        countries_to_remove.append(key)

for key in countries_to_remove:
    countries.pop(key, None)

"""
fig = plt.figure(1)
plt.subplot(2, 2, 1)
plt.scatter(incs, alts, 1)
plt.xlabel("Inclination [degs]")
plt.ylabel("Altitude [km]")

plt.subplot(2, 2, 2)
plt.scatter(raans, alts, 1)
plt.xlabel("RAAN [degs]")
plt.ylabel("Altitude [km]")

plt.subplot(2, 2, 3)
plt.scatter(incs, raans, 1)
plt.xlabel("Inclination [degs]")
plt.ylabel("RAAN [degs]")

plt.subplot(2, 2, 4)
plt.scatter(eccs, alts, 1)
plt.xlabel("Eccentricity [n.d.]")
plt.ylabel("Altitude [km]")

plt.suptitle("Projected LEO Debris Population Orbital Distribution in 2024")
"""

"""
fig = plt.figure(3)
plt.scatter(incs, alts, masses)
plt.xlabel("Inclination [degs]")
plt.ylabel("Altitude [km]")
plt.title("Distribution of Mass over Altitude and Inclination")

fig = plt.figure(2)
plt.hist(masses, 10)
plt.xlabel("Mass [kg]")
plt.ylabel("Number of Objects")
plt.title("Distribution of Masses")
"""

fig = plt.figure(4)
ax = plt.axes()
countries_descend = {
    k: v for k, v in sorted(countries.items(), key=lambda item: item[1], reverse = True)
    }
data = countries_descend.values()
labels = countries_descend.keys()
patches, texts = plt.pie(data, startangle=90,
                         wedgeprops = {"edgecolor" : "black",
                      'linewidth': 2,
                      'antialiased': True})
#plt.xlabel("Country Code")
#plt.ylabel("Number of Objects")
plt.title("Breakdown of LEO Object Mass by Country Ownership")
#plt.xticks(rotation=45, ha='right')
plt.legend(patches, labels, bbox_to_anchor=(1,0.5), loc="center right", fontsize=14)
theme = plt.get_cmap('cool')
ax.set_prop_cycle("color", [theme(1. * i / len(data))
                             for i in range(len(data))])

fig = plt.figure(5)
ax = plt.axes()
type_descend = {
    k: v for k, v in sorted(obj_type.items(), key=lambda item: item[1], reverse = True)
    }
data = type_descend.values()
labels = type_descend.keys()
patches, texts = plt.pie(data, startangle=90,
                         wedgeprops = {"edgecolor" : "black",
                      'linewidth': 2,
                      'antialiased': True})
#plt.xlabel("Object Classification")
#plt.ylabel("Number of Objects")
plt.title("Breakdown of LEO Objects by Classifications")
#plt.xticks(rotation=25, ha='right')
plt.legend(patches, labels, bbox_to_anchor=(1.5,0.5), loc="center right", fontsize=14)
theme = plt.get_cmap('cool')
ax.set_prop_cycle("color", [theme(1. * i / len(data))
                             for i in range(len(data))])

fig = plt.figure(6, figsize=(10,10))
ax = plt.axes()
h = ax.hist2d(incs, alts, weights=masses, bins=40, \
    norm=matplotlib.colors.LogNorm(), cmap="inferno_r")
fig.colorbar(h[3], ax=ax)
#plt.title("Mass Distribution over Alt + Inc of LEO Objects")
plt.xlabel("Inclination [degrees]")
plt.ylabel("Altitude [km]")
plt.xlim((0, 180))
plt.ylim((0, 2000))

plt.show()

print(np.median(eccs))
print(np.std(eccs))
