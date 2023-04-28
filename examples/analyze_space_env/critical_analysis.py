"""Analyze the uncertainties for the top 100 CSI scored objects"""
import matplotlib.pyplot as plt
import scienceplots # pylint: disable=unused-import
from adr_toolbox.space_env import SpaceEnv
from adr_toolbox.util import load_data, save_data
plt.style.use('science')
plt.rcParams.update({'font.size': 14})

full_leo = load_data("full_leo_env_2024")

top_env = SpaceEnv()
# Pull in data for top X scored leo objects
top_env.from_api_data("top_50_hist")

# Propagate all historical orbit data
top_env.propagate_env(2024)

# Apply CSI scoring to top 100 objects with uncertainty
top_env.score_env(full_leo.spatial_density)

alts = []
eccs = []
alt_uncs = []
for sat in top_env.sat_dict.values():
    alts.append(sat.orbit_mean[0] - 6378)
    eccs.append(sat.orbit_mean[3])
    alt_uncs.append(sat.orbit_unc[0] * 3)

fig = plt.figure(1)
ax = plt.axes()
plt.scatter(eccs, alt_uncs)
#plt.title("TLE History Finite Differencing Errors from SGP4")
plt.xlabel("Eccentricity")
plt.ylabel("Altitude 3-Sigma Deviation [km]")
plt.grid()

top_scored_sat = list(top_env.sat_dict.values())[0]
top_alts = []
top_incs = []
top_raans = []
for alts in top_scored_sat.orbit_elems[0]:
    top_alts.append(alts - 6378)

for incs in top_scored_sat.orbit_elems[1]:
    top_incs.append(incs)

for raans in top_scored_sat.orbit_elems[2]:
    top_raans.append(raans)

fig = plt.figure(2)
plt.subplot(1, 3, 1)
plt.hist(top_alts, 15)
plt.ylabel("TLE Datapoint Frequency")
plt.xlabel("Altitude [km]")
plt.grid()

plt.subplot(1, 3, 2)
plt.hist(top_incs, 15)
plt.ylabel("TLE Datapoint Frequency")
plt.xlabel("Inclination [degs]")
plt.grid()

plt.subplot(1, 3, 3)
plt.hist(top_raans, 15)
plt.ylabel("TLE Datapoint Frequency")
plt.xlabel("RAAN [degs]")
plt.grid()

fig = plt.figure(3)
ax = plt.axes()
top_env.cluster_by_dv(0.2, 3)
for label, sat_dict in top_env.cluster_dict.items():
    alts = []
    incs = []
    alts_unc = []
    incs_unc = []
    for sat in sat_dict.values():
        alts.append(sat.orbit_mean[0] - 6378)
        if sat.satname == "COSMOS 2565":
            alts_unc.append(0)
        else:
            alts_unc.append(sat.orbit_unc[0] * 30)
        incs.append(sat.orbit_mean[1])
        incs_unc.append(sat.orbit_unc[1] * 300)
    plt.scatter(incs, alts, label=label)
    plt.errorbar(incs, alts, xerr=incs_unc, yerr=alts_unc, ls='none')
#plt.title("Clustering of Top 100 Scored Objects by Transfer $\Delta$V Cost")
plt.xlabel("Inclination [degs]")
plt.ylabel("Altitude [km]")
plt.legend(loc='lower left')
plt.grid()
plt.show()

save_data(top_env, "top_50_w_unc_clustered")
