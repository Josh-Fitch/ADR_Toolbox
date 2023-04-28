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

class Architecture():
    """
    """
    def __init__(self, year, space_env, servicers, max_vehicles,
                 max_refuels, launch_cost_per_kg,
                 weights, year_limit, conservatism, monte_carlo_size):
        """
        """
        self.year = year
        self.clusters = space_env.cluster_dict
        self.num_clusters = len(self.clusters)
        self.servicers = servicers
        self.num_servicers = len(servicers)
        self.servicer_usage = np.zeros(len(servicers))
        self.total_tof = 0
        self.total_score = 0
        self.total_cost = 0
        self.max_tof = 0
        self.max_vehicles = max_vehicles
        self.max_refuels = max_refuels
        self.launch_cost_per_kg = launch_cost_per_kg
        self.weights = weights
        self.year_limit = year_limit
        self.conservatism = conservatism
        self.monte_carlo_size = monte_carlo_size
        self.missions = {}


    def solve_architecture(self):
        """
        Iterate through clusters and apply optimization
        """
        for cluster_name, targets in self.clusters.items():
            print(f"Solving Mission for {cluster_name}")
            mission = Mission(targets, self.servicers, self.weights,
                              self.year_limit, self.conservatism,
                              self.monte_carlo_size, 600)
            mission.solve_mission()
            self.missions[cluster_name] = mission

        for mission in self.missions.items():
            for i, used in enumerate(mission.vehicle_used):
                if used == 1:
                    self.servicer_usage[i] += 1
            self.total_score += mission.raw_metrics["risk remediated"]
            self.total_tof += mission.raw_metrics["total tof"]
            if mission.raw_metrics["max tof"] > self.max_tof:
                self.max_tof = mission.raw_metrics["max tof"]

        ddte_cost = 0
        launch_mass = 0
        for i, num in enumerate(self.servicer_usage):
            veh = self.servicers[i]
            ddte_cost += self.__calc_ddte_costs(
                veh.dry_mass, num, self.year, veh.difficulty, veh.block
            )
            launch_mass += veh.wet_mass * num

        total_cost = 1.1 * ddte_cost + launch_mass * self.launch_cost_per_kg

        print("Architecture:")
        print(f"    Debris Risk Remediated [CSI] = {self.total_score}")
        print(f"    Total Cost [2023$] = {total_cost}")
        print(f"    Mission Duration [Years] = {self.max_tof}")
        for i, servicer in enumerate(self.servicers):
            print(f"    {self.servicer_usage[i]} {servicer.name}")


    @staticmethod
    def __calc_ddte_costs(mass, quantity, year, difficulty, block):
        """
        """
        alpha = 5.65e-4
        beta = 0.5941
        theta = 0.6604
        delta = 80.599
        epsilon = 3.8085e-55
        phi = -0.3553
        gamma = 1.5691

        spec = 2.00

        cost = alpha * quantity ** beta * 2.2 * mass ** theta * \
               delta ** spec * epsilon ** (1/(year-1900)) * \
               block ** phi * gamma ** difficulty

        # approximate 80% increase from 1999 to 2023 from inflation
        cost_adjusted = 1.8 * cost

        return cost_adjusted
