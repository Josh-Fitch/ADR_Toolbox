"""Analyze the uncertainties for the top 100 CSI scored objects"""
import numpy as np
import matplotlib.pyplot as plt
import scienceplots # pylint: disable=unused-import
from adr_toolbox.space_env import SpaceEnv
from adr_toolbox.util import load_data, save_data
plt.style.use('science')
plt.rcParams.update({'font.size': 22})

full_leo = load_data("full_leo_env_2024")

top_100_env = SpaceEnv()
# Pull in data for top 100 scored leo objects
top_100_env.from_api_data("top_100_hist")

# Propagate all historical orbit data
top_100_env.propagate_env(2025)

# Apply CSI scoring to top 100 objects with uncertainty
top_100_env.score_env(full_leo.spatial_density)

alts = []
eccs = []
alt_uncs = []
for sat in top_100_env.sat_dict.values():
    alts.append(sat.orbit_mean[0] - 6378)
    eccs.append(sat.orbit_mean[3])
    alt_uncs.append(sat.orbit_unc[0] * 3)

print(np.median(alt_uncs))
print(np.max(alt_uncs))
print(np.min(alt_uncs))

fig = plt.figure(1)
ax = plt.axes()
plt.scatter(eccs, alt_uncs)
plt.title("TLE History Finite Differencing Errors from SGP4")
plt.xlabel("Eccentricity")
plt.ylabel("3 Sigma Deviation [km]")
plt.grid()

top_scored_sat = list(top_100_env.sat_dict.values())[0]
top_alts = []
for alt in top_scored_sat.orbit_elems[0]:
    top_alts.append(alt - 6378)

print(f"\nEcc = {top_scored_sat.orbit_mean[3]}")
print(f"Alt = {top_scored_sat.orbit_mean[0]}")

fig = plt.figure(2)
ax = plt.axes()
plt.hist(top_alts, 15)
plt.title(f"SGP4 Altitude Distribution for Sat {top_scored_sat.satno}")
plt.xlabel("Past TLE")
plt.ylabel("Altitude [km]")
plt.grid()

fig = plt.figure(3)
ax = plt.axes()
top_100_env.cluster_by_dv(0.2, 3)
for label, sat_dict in top_100_env.cluster_dict.items():
    alts = []
    incs = []
    alts_unc = []
    incs_unc = []
    for sat in sat_dict.values():
        alts.append(sat.orbit_mean[0] - 6378)
        if sat.orbit_unc[0] * 3 > 200:
            alts_unc.append(sat.orbit_unc[0] * 3)
        else:
            alts_unc.append(sat.orbit_unc[0] * 30)
        incs.append(sat.orbit_mean[1])
        incs_unc.append(sat.orbit_unc[1] * 300)
    plt.scatter(incs, alts, label=label)
    plt.errorbar(incs, alts, xerr=incs_unc, yerr=alts_unc, ls='none')
plt.title("Clustering of Top 100 Scored Objects by Transfer delta-V Cost")
plt.xlabel("Inclination [degs]")
plt.ylabel("Altitude [km]")
plt.legend(loc='lower left')
plt.grid()
plt.show()

save_data(top_100_env, "top_100_w_unc_clustered")
