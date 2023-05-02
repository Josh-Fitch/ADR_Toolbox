""" Plot results from architecture design """
import numpy as np
import matplotlib.pyplot as plt
import scienceplots # pylint: disable=unused-import
import seaborn as sns
from adr_toolbox.util import load_data
plt.style.use('science')
plt.rcParams.update({'font.size': 18})
colors = sns.color_palette()

fig = plt.figure()
ax = plt.gca()
ax2 = ax.twinx()
for j, gamma in enumerate([0, 1, 2]):
    # Load in the architecture data
    arch = load_data(f"commercial_architecture_top_50_debris_{gamma}gamma")
    scores = []
    costs_in_mil = []
    arch_efficiency = []
    for i, score in enumerate(arch.arch_data["total score"]):
        time = arch.arch_data["max tof"][i]
        cost = arch.arch_data["total cost"][i]
        scores.append(score)
        costs_in_mil.append(cost)
        arch_efficiency.append(score / time / cost)
    ax.scatter(costs_in_mil, scores, color=colors[j],
               marker="o", label=f"Total Score \n Gamma = {gamma}")
    ax2.scatter(costs_in_mil, arch_efficiency, color=colors[j],
             marker="x", label=f"Efficiency \n Gamma = {gamma}")
    score_est = np.polyfit(costs_in_mil, scores, 2)
    eff_est = np.polyfit(costs_in_mil, arch_efficiency, 2)
    costs_full = np.linspace(costs_in_mil[0], costs_in_mil[-1], 100)
    ax.plot(costs_full, np.polyval(score_est, costs_full),
            color=colors[j], label=f"Total Score Best Fit \n Gamma = {gamma}")
    ax2.plot(costs_full, np.polyval(eff_est, costs_full), "--",
             color=colors[j], label=f"Efficiency Best Fit \n Gamma = {gamma}")
#plt.title("Architecture Budget Pareto Frontier")
ax.set_xlabel(r"Lifecycle Budget [\$M]")
ax.set_ylabel("Cumulative CSI Score of Remediated Debris")
ax2.set_ylabel(r"Total CSI Score / Max ToF [years] / Cost [\$M]")
ax.legend(fontsize = 14, bbox_to_anchor=(1.15,1), loc="upper left")
ax2.legend(fontsize = 14, bbox_to_anchor=(1.15,0.5), loc="upper left")
plt.grid()
plt.show()

arch_cons = load_data("commercial_architecture_top_50_debris_2gamma")
arch_avg = load_data("commercial_architecture_top_50_debris_1gamma")
arch_aggro = load_data("commercial_architecture_top_50_debris_0gamma")

arch_cheap = arch_cons.arch_data["missions"][-2]
arch_mid1 = arch_avg.arch_data["missions"][3]
arch_mid2 = arch_avg.arch_data["missions"][2]
arch_expensive = arch_aggro.arch_data["missions"][0]

fig = plt.figure()
x = ["Robust + Low-Cost", "Balanced + Low-Cost", "Balanced + High-Cost", "Risky + High-Cost"]
ddte = np.array([arch_cons.arch_data["ddte cost"][-2],
                 arch_avg.arch_data["ddte cost"][3],
                 arch_avg.arch_data["ddte cost"][2],
                 arch_aggro.arch_data["ddte cost"][0]])
launch = np.array([arch_cons.arch_data["launch cost"][-2],
                   arch_avg.arch_data["launch cost"][3],
                   arch_avg.arch_data["launch cost"][2],
                   arch_aggro.arch_data["launch cost"][0]])
ops = np.array([arch_cons.arch_data["ops cost"][-2],
                arch_avg.arch_data["ops cost"][3],
                arch_avg.arch_data["ops cost"][2],
                arch_aggro.arch_data["ops cost"][0]])
refuel = np.array([arch_cons.arch_data["refueling cost"][-2],
                   arch_avg.arch_data["refueling cost"][3],
                   arch_avg.arch_data["refueling cost"][2],
                   arch_aggro.arch_data["refueling cost"][0]])
plt.grid(zorder=0)
plt.bar(x, ddte, color=colors[0], zorder=3)
plt.bar(x, launch, bottom=ddte, color=colors[1], zorder=4)
plt.bar(x, ops, bottom=ddte+launch, color=colors[2], zorder=5)
plt.bar(x, refuel, bottom=ddte+launch+ops, color=colors[3], zorder=6)
plt.ylabel(r"Lifecycle Cost [\$M 2023]")
plt.legend([r"DDT\&E", "Launch", "Operations", "On-Orbit Refueling"])
plt.show()


print("Cheap Fleet")
score = 0
serv_dict = {"MEV":0, "MRV":0, "OSAM-1":0, "ClearSpace":0, "ELSA":0}
for mission in arch_cheap.values():
    for name, data in mission.data_log.items():
        if len(data["times"]) > 1:
            for serv in serv_dict.keys():
                if serv in name:
                    serv_dict[serv] += 1
        for t_ind in data["captured"]:
            if t_ind is not None:
                target = mission.targets[t_ind]
                score += target.score
                print(f"{target.satno}, {target.satname}, {target.country}, {target.mass}, {target.score}")
print(score)
print(serv_dict)

print("Balanced Fleet 1")
score = 0
serv_dict = {"MEV":0, "MRV":0, "OSAM-1":0, "ClearSpace":0, "ELSA":0}
for mission in arch_mid1.values():
    for name, data in mission.data_log.items():
        if len(data["times"]) > 1:
            for serv in serv_dict.keys():
                if serv in name:
                    serv_dict[serv] += 1
        for t_ind in data["captured"]:
            if t_ind is not None:
                target = mission.targets[t_ind]
                score += target.score
                print(f"{target.satno}, {target.satname}, {target.country}, {target.mass}, {target.score}")
print(score)
print(serv_dict)

print("Balanced Fleet 2")
score = 0
serv_dict = {"MEV":0, "MRV":0, "OSAM-1":0, "ClearSpace":0, "ELSA":0}
for mission in arch_mid2.values():
    for name, data in mission.data_log.items():
        if len(data["times"]) > 1:
            for serv in serv_dict.keys():
                if serv in name:
                    serv_dict[serv] += 1
        for t_ind in data["captured"]:
            if t_ind is not None:
                target = mission.targets[t_ind]
                score += target.score
                print(f"{target.satno}, {target.satname}, {target.country}, {target.mass}, {target.score}")
print(score)
print(serv_dict)

print("Expensive Fleet")
score = 0
serv_dict = {"MEV":0, "MRV":0, "OSAM-1":0, "ClearSpace":0, "ELSA":0}
for mission in arch_expensive.values():
    for name, data in mission.data_log.items():
        if len(data["times"]) > 1:
            for serv in serv_dict.keys():
                if serv in name:
                    serv_dict[serv] += 1
    for data in mission.data_log.values():
        for t_ind in data["captured"]:
            if t_ind is not None:
                target = mission.targets[t_ind]
                score += target.score
                print(f"{target.satno}, {target.satname}, {target.country}, {target.mass}, {target.score}")
print(score)
print(serv_dict)
