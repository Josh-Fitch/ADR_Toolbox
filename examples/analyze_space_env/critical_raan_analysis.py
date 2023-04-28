"""Analyze the uncertainties for the top 100 CSI scored objects"""
import json
import matplotlib.pyplot as plt
import scienceplots # pylint: disable=unused-import
plt.style.use('science')
plt.rcParams.update({'font.size': 22})

with open("top_100_hist.json", 'r', encoding='utf-8') as json_file:
    api_data = json.load(json_file)

fig = plt.figure()
ax = plt.axes()
i = 1
for satno, dict_data in api_data.items():
    if satno == "__header":
        continue
    if i > 10:
        break
    raans = []
    time_index = []
    j = 1
    for orbits in dict_data["gp_hist"]:
        raan = float(orbits["RA_OF_ASC_NODE"])
        if raan > 0 and raan < 360:
            time_index.append(j)
            raans.append(raan)
            j += 1
    plt.plot(time_index, raans)
    i += 1
plt.title("RAAN History of Top 10 Objects")
plt.xlabel("Time Index")
plt.ylabel("RAAN [degs]")
plt.grid()
plt.show()
