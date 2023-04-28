""" Plot results from shuttle mission design """
import matplotlib.pyplot as plt
import scienceplots # pylint: disable=unused-import
import seaborn as sns
from adr_toolbox.util import load_data
plt.style.use('science')
plt.rcParams.update({'font.size': 22})

# Load in the shuttle mission data
#shuttle_mission = load_data("cluster3_fleet3_combo_07score_03tof")
shuttle_mission = load_data("cluster3_fleet3_combo_05score_05num")

alts = []
alts_unc = []
incs = []
incs_unc = []
raans = []
raans_unc = []
for target in shuttle_mission.targets:
    alts.append(target.orbit_mean[0] - 6378)
    alts_unc.append(30*target.orbit_unc[0])
    incs.append(target.orbit_mean[1])
    incs_unc.append(30*target.orbit_unc[1])
    raans.append(target.orbit_mean[2])
    raans_unc.append(300*target.orbit_unc[2])
    #print(f"{target.satno}, {target.satname}, {target.country}, {target.mass}, {target.score}")

fig = plt.figure()
plt.scatter(incs, alts)
plt.errorbar(incs, alts, xerr=incs_unc, yerr=alts_unc, ls='none')
plt.xlabel("Inclination [degs]")
plt.ylabel("Altitude [km]")
plt.grid()

fig = plt.figure()
plt.scatter(raans, alts)
plt.errorbar(raans, alts, xerr=raans_unc, yerr=alts_unc, ls='none')
plt.xlabel("Right Ascension of Ascending Node [degs]")
plt.ylabel("Altitude [km]")
plt.grid()

fig = plt.figure()
colors = sns.color_palette()
j = 0
for name, data in shuttle_mission.data_log.items():
    serv_times = [x/3600/24/365 for x in data["times"]]
    serv_alts = [x - 6378 for x in data["a_profile"]]
    captured_times = []
    captured_alts = []
    released_times = []
    released_alts = []
    for i, time in enumerate(data["times"]):
        if data["captured"][i] is not None:
            captured_times.append(time/3600/24/365)
            captured_alts.append(data["a_profile"][i]-6378)
        elif data["released"][i] is not None:
            released_times.append(time/3600/24/365)
            released_alts.append(data["a_profile"][i]-6378)
    plt.plot(serv_times, serv_alts, color=colors[j], label=f"{name} Routing")
    plt.scatter(captured_times, captured_alts, \
                color=colors[j], marker="v", label=f"Target Captured by {name}")
    plt.scatter(released_times, released_alts, \
                color=colors[j], marker="X",  label=f"Target Released by {name}")
    j+=1
plt.title("Servicer Altitude Temporal Routing and Debris Remediation over Time")
plt.xlabel("Time [years]")
plt.ylabel("Altitude [km]")
plt.legend(fontsize = 10)
plt.grid()

fig = plt.figure()
j = 0
for name, data in shuttle_mission.raan_data.items():
    serv_times = [x/3600/24/365 for x in data["times"]]
    serv_raans = data["raan_profile"]
    plt.plot(serv_times, serv_raans, color=colors[j], label=f"{name} Routing")
    j+=1
j = 0
for name, data in shuttle_mission.data_log.items():
    captured_times = []
    captured_raans = []
    released_times = []
    released_raans = []
    for i, time in enumerate(data["times"]):
        if data["captured"][i] is not None:
            captured_times.append(time/3600/24/365)
            captured_raans.append(data["raan_profile"][i])
        elif data["released"][i] is not None:
            released_times.append(time/3600/24/365)
            released_raans.append(data["raan_profile"][i])
    plt.scatter(captured_times, captured_raans, \
                color=colors[j], marker="v", label=f"Target Captured by {name}")
    plt.scatter(released_times, released_raans, \
                color=colors[j], marker="X",  label=f"Target Released by {name}")
    j+=1
plt.title("Servicer RAAN Temporal Routing and Debris Remediation over Time")
plt.xlabel("Time [years]")
plt.ylabel("RAAN [degs]")
plt.legend(fontsize = 10)
plt.grid()

fig = plt.figure()
plt.scatter(incs, alts, c='r', marker="X", label="Targets")
i = 0
for name, data in shuttle_mission.data_log.items():
    serv_alts = [x - 6378 for x in data["a_profile"]]
    serv_incs = data["inc_profile"]
    if i == 0:
        plt.scatter(serv_incs[0], serv_alts[0], c='k', s=100, label="Deployment Orbit")
    plt.plot(serv_incs, serv_alts, color=colors[i], label=name)
    i+=1
plt.title("Servicer Alt-Inc Optimal Routing")
plt.xlabel("Inclination [degs]")
plt.ylabel("Altitude [km]")
plt.legend(fontsize = 10)
plt.grid()

fig = plt.figure()
ax = plt.gca()
ax2 = ax.twinx()
j = 0
for name, data in shuttle_mission.data_log.items():
    serv_times = [x/3600/24/365 for x in data["times"]]
    serv_mass = data["prop_mass"]
    serv_refuels = data["refuels"]
    ax.plot(serv_times, serv_mass, color=colors[j], marker="o", label=f"{name} Mass")
    ax2.plot(serv_times, serv_refuels, "--", color=colors[j], label=f"{name} Refuels")
    j+=1
plt.title("Servicer Propellant Usage")
ax.set_xlabel("Time [years]")
ax.set_ylabel("Servicer Propellant Mass [kg]")
ax2.set_ylabel("Remaining Refuels")
plt.legend(fontsize = 10)
plt.grid()

ga = shuttle_mission.ga_evo
fig = plt.figure()
ax = plt.axes()
ax.scatter(ga["gens"], ga["avg"], label="GA Average", s=80, marker='o')
ax.scatter(ga["gens"], ga["best"], label="GA Best", s=40, marker='o')
plt.title("Mission Design Performance Evolution")
plt.xlabel("Generation")
plt.ylabel("Fitness")
plt.legend()
plt.grid()
plt.show()
