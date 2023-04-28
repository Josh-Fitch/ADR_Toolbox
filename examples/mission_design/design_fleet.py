""" Case Study 2 -- Design a Notional Shuttle Mission """
from adr_toolbox.spacecraft import Shuttle, Picker, Mothership, Spacecraft
from adr_toolbox.mission import Mission
from adr_toolbox.util import load_data, save_data

# Load in the top 200 scored debris with clustering
top_200_data = load_data("top_200_w_unc_clustered")
# Get specifically the dictionary of debris objects in cluster 3
targets = top_200_data.cluster_dict["Cluster 3"]

# Create a fleet of diverse notional servicing spacecraft
deorbit_mod1 = Spacecraft("DeorbitMod1", 200, 0.6, 100e-3, 1400, 1, -1)
deorbit_mod2 = Spacecraft("DeorbitMod2", 200, 0.6, 100e-3, 1400, 1, -1)
deorbit_mod3 = Spacecraft("DeorbitMod3", 200, 0.6, 100e-3, 1400, 1, -1)
modules = [deorbit_mod1, deorbit_mod2, deorbit_mod3]
servicer_1 = Mothership("Mothership", 2000, 0.5, 250, 330, 1, 1,
                        6378+550, 65, 150, 550, 10*24*60*60, 75, 1, modules)
servicer_2 = Shuttle("Shuttle", 500, 0.4, 100e-3, 1400, 1, 1,
                     6378+550, 65, 320, 300, 10*24*60*60, 75, 2)
servicer_3 = Picker("Picker", 500, 0.4, 100e-3, 1400, 1, 0,
                    6378+550, 65, 320, 10*24*60*60, 75)

# Create a homogeneous fleet of 3 servicing vehicles
servicers = [servicer_1, servicer_2, servicer_3]
mission = Mission(targets, servicers, (0.5, 0, 0.5, 0), 4, 1, 10, 600, no_route=True)

# Solve the routing and save to a .dat file
mission.solve_mission()
save_data(mission, "cluster3_fleet3_combo_05score_05num")
