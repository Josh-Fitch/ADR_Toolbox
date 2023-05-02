"""Container for adr_toolbox Architecture class definitions"""
###############################################################
##  Implemented by:
##     - Joshua Fitch
##     - Purdue University AAE
##     - January 2023
##     - jfitch007@outlook.com
###############################################################
import numpy as np
from adr_toolbox.mission import Mission
from adr_toolbox.spacecraft import Mothership

class Architecture():
    """ Design and optimize various missions for various budget levels """
    def __init__(
            self, year, num_budgets, space_env, servicers,
            launch_cost_per_kg, refuel_cost_per_kg, weights,
            year_limit, conservatism, monte_carlo_size
        ):
        self.year = year
        self.num_budgets = num_budgets
        self.clusters = space_env.cluster_dict
        self.servicers = servicers
        self.servicer_usage = np.zeros(len(servicers))
        self.launch_cost_per_kg = launch_cost_per_kg
        self.refuel_cost_per_kg = refuel_cost_per_kg
        self.weights = weights
        self.year_limit = year_limit
        self.conservatism = conservatism
        self.monte_carlo_size = monte_carlo_size
        self.arch_data = {
            "missions": [],
            "total tof": [],
            "max tof": [],
            "total score": [],
            "total cost": [],
            "ddte cost": [],
            "launch cost": [],
            "ops cost": [],
            "refueling cost": [],
            "max score": []
        }


    def solve_architecture(self):
        """ Iterate through clusters and apply optimization """
        scale_range = np.linspace(0, 0.5, self.num_budgets)
        for weight in scale_range:
            missions = {}
            weights = [x * (1 - weight) for x in self.weights]
            weights.insert(2, weight)
            self.servicer_usage = np.zeros(len(self.servicers))
            max_score = 0
            for cluster_name, targets in self.clusters.items():
                target_incs = [target.orbit_mean[1] for target in targets.values()]
                avg_inc = np.average(target_incs)
                for servicer in self.servicers:
                    servicer.inc_0 = avg_inc
                mission = Mission(targets, self.servicers, weights,
                    self.year_limit, self.conservatism,
                    self.monte_carlo_size, 600
                )
                mission.solve_mission()
                missions[cluster_name] = mission
                for target in targets.values():
                    max_score += target.score
            self.arch_data["max score"].append(max_score)

            total_score = 0
            total_tof = 0
            max_tof = 0
            refuel_mass = 0
            for mission in missions.values():
                for i, used in enumerate(mission.vehicle_used):
                    if used:
                        self.servicer_usage[i] += 1
                total_score += mission.raw_metrics["risk remediated"]
                total_tof += mission.raw_metrics["total tof"]
                if mission.raw_metrics["max tof"] > max_tof:
                    max_tof = mission.raw_metrics["max tof"]
                refuel_mass += mission.raw_metrics["refuel mass"]

            ddte_cost = 0
            launch_mass = 0
            for i, num in enumerate(self.servicer_usage):
                veh = self.servicers[i]
                ddte_cost += self.__calc_ddte_costs(
                    veh.dry_mass, num, self.year, veh.difficulty, veh.block
                )
                launch_mass += veh.wet_mass * num
                if isinstance(self.servicers[i], Mothership):
                    num_modules = len(self.servicers[i].modules)
                    module = self.servicers[i].modules[0]
                    ddte_cost += self.__calc_ddte_costs(
                        module.dry_mass, num_modules, self.year, module.difficulty, module.block
                    )
                    launch_mass += module.wet_mass * num_modules

            launch_cost = (launch_mass * self.launch_cost_per_kg) / 1000000
            ops_cost = 0.1 * ddte_cost
            refueling_cost = (refuel_mass * self.refuel_cost_per_kg) / 1000000
            total_cost = ddte_cost + launch_cost + ops_cost + refueling_cost

            self.arch_data["missions"].append(missions)
            self.arch_data["total tof"].append(total_tof)
            self.arch_data["max tof"].append(max_tof)
            self.arch_data["total score"].append(total_score)
            self.arch_data["total cost"].append(total_cost)
            self.arch_data["ddte cost"].append(ddte_cost)
            self.arch_data["launch cost"].append(launch_cost)
            self.arch_data["ops cost"].append(ops_cost)
            self.arch_data["refueling cost"].append(refueling_cost)


    @staticmethod
    def __calc_ddte_costs(mass, quantity, year, difficulty, block):
        """ Compute results from Advanced Mission Cost Model """
        alpha = 5.65e-4
        beta = 0.5941
        theta = 0.6604
        delta = 80.599
        epsilon = 3.8085e-55
        phi = -0.3553
        gamma = 1.5691
        spec = 2.00

        cost = alpha * quantity ** beta * (2.2 * mass) ** theta * \
               delta ** spec * epsilon ** (1/(year-1900)) * \
               block ** phi * gamma ** difficulty

        # approximate 80% increase from 1999 to 2023 from inflation
        cost_adjusted = 1.8 * cost

        return cost_adjusted
