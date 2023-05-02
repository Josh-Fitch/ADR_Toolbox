""" Plot results from notional fleet mission design """
import matplotlib.pyplot as plt
import scienceplots # pylint: disable=unused-import
import seaborn as sns
from adr_toolbox.util import load_data
plt.style.use('science')
plt.rcParams.update({'font.size': 22})

# Load in the shuttle mission data
shuttle_mission = load_data("cluster3_fleet3_combo_05score_05num")
#shuttle_mission = load_data("cluster3_fleet3_combo_08score_02tof")
#shuttle_mission = load_data("cluster3_fleet3_combo_08score_02tof_0gamma")

alts = []
alts_unc = []
incs = []
incs_unc = []
raans = []
raans_unc = []
score = []
for target in shuttle_mission.targets:
    alts.append(target.orbit_mean[0] - 6378)
    alts_unc.append(30*target.orbit_unc[0])
    incs.append(target.orbit_mean[1])
    incs_unc.append(30*target.orbit_unc[1])
    raans.append(target.orbit_mean[2])
    raans_unc.append(300*target.orbit_unc[2])
    score.append(2000 * target.score ** 2)
    #print(f"{target.satno}, {target.satname}, {target.country}, {target.mass}, {target.score}")

fig = plt.figure()
plt.scatter(incs, alts, s=score)
plt.errorbar(incs, alts, xerr=incs_unc, yerr=alts_unc, ls='none')
plt.xlabel("Inclination [degs]")
plt.ylabel("Altitude [km]")
plt.grid()

fig = plt.figure()
plt.scatter(raans, alts, s=score)
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
    capt_scores = []
    rel_scores = []
    for i, time in enumerate(data["times"]):
        if data["captured"][i] is not None:
            captured_times.append(time/3600/24/365)
            captured_alts.append(data["a_profile"][i]-6378)
            capt_scores.append(score[data["captured"][i]])
        elif data["released"][i] is not None:
            released_times.append(time/3600/24/365)
            released_alts.append(data["a_profile"][i]-6378)
            rel_scores.append(score[data["released"][i]])
    if len(serv_times) > 1:
        plt.plot(serv_times, serv_alts, color=colors[j], label=f"{name} Routing")
        plt.scatter(captured_times, captured_alts, s=capt_scores, \
                    color=colors[j], marker="v", label=f"Target Captured by {name}")
        plt.scatter(released_times, released_alts, s=rel_scores, \
                    color=colors[j], marker="X",  label=f"Target Released by {name}")
    j+=1
#plt.title("Servicer Altitude Temporal Routing and Debris Remediation over Time")
plt.xlabel("Time [years]")
plt.ylabel("Altitude [km]")
plt.legend(fontsize = 12, bbox_to_anchor=(1,1), loc="upper left")
plt.tight_layout()
plt.grid()

fig = plt.figure()
j = 0
for name, data in shuttle_mission.raan_data.items():
    serv_times = [x/3600/24/365 for x in data["times"]]
    serv_raans = data["raan_profile"]
    if len(serv_times) > 1:
        plt.plot(serv_times, serv_raans, color=colors[j], label=f"{name} Routing")
    j+=1
j = 0
for name, data in shuttle_mission.data_log.items():
    captured_times = []
    captured_raans = []
    released_times = []
    released_raans = []
    capt_scores = []
    rel_scores = []
    for i, time in enumerate(data["times"]):
        if data["captured"][i] is not None:
            captured_times.append(time/3600/24/365)
            captured_raans.append(data["raan_profile"][i])
            capt_scores.append(score[data["captured"][i]])
        elif data["released"][i] is not None:
            released_times.append(time/3600/24/365)
            released_raans.append(data["raan_profile"][i])
            rel_scores.append(score[data["released"][i]])
    if len(captured_times) >= 1:
        plt.scatter(captured_times, captured_raans, s=capt_scores, \
                    color=colors[j], marker="v", label=f"Target Captured by {name}")
    if len(released_times) >= 1:
        plt.scatter(released_times, released_raans, s=rel_scores, \
                    color=colors[j], marker="X",  label=f"Target Released by {name}")
    j+=1
#plt.title("Servicer RAAN Temporal Routing and Debris Remediation over Time")
plt.xlabel("Time [years]")
plt.ylabel("RAAN [degs]")
plt.legend(fontsize = 12, bbox_to_anchor=(1,1), loc="upper left")
plt.tight_layout()
plt.grid()

fig = plt.figure()
plt.scatter(incs, alts, s=score, c='r', marker="X", label="Targets")
i = 0
for name, data in shuttle_mission.data_log.items():
    serv_alts = [x - 6378 for x in data["a_profile"]]
    serv_incs = data["inc_profile"]
    if i == 0:
        plt.scatter(serv_incs[0], serv_alts[0], c='k', s=100, label="Deployment Orbit")
    if len(serv_alts) > 1:
        plt.plot(serv_incs, serv_alts, color=colors[i], label=name)
    i+=1
#plt.title("Servicer Alt-Inc Optimal Routing")
plt.xlabel("Inclination [degs]")
plt.ylabel("Altitude [km]")
plt.legend(fontsize = 10, bbox_to_anchor=(1,1), loc="upper left")
plt.tight_layout()
plt.grid()

fig = plt.figure()
ax = plt.gca()
ax2 = ax.twinx()
j = 0
for name, data in shuttle_mission.data_log.items():
    serv_times = [x/3600/24/365 for x in data["times"]]
    serv_mass = data["prop_mass"]
    serv_refuels = data["refuels"]
    if len(serv_times) > 1:
        ax.plot(serv_times, serv_mass, color=colors[j], marker="o", label=f"{name} Mass")
        ax2.plot(serv_times, serv_refuels, "--", color=colors[j], label=f"{name} Refuels")
    j+=1
#plt.title("Servicer Propellant Usage")
ax.set_xlabel("Time [years]")
ax.set_ylabel("Servicer Propellant Mass [kg]")
ax2.set_ylabel("Remaining Refuels")
ax.legend(fontsize = 12, bbox_to_anchor=(1.08,1), loc="upper left")
ax2.legend(fontsize = 12, bbox_to_anchor=(1.08,0.7), loc="upper left")
plt.tight_layout()
plt.grid()

ga = shuttle_mission.ga_evo
fig = plt.figure()
ax = plt.axes()
ax.scatter(ga["gens"], ga["avg"], label="GA Average", s=80, marker='o')
ax.scatter(ga["gens"], ga["best"], label="GA Best", s=40, marker='o')
#plt.title("Mission Design Performance Evolution")
plt.xlabel("Generation")
plt.ylabel("Fitness")
plt.legend()
plt.grid()
plt.show()
