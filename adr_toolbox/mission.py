"""Container for adr_toolbox Mission class definitions"""
###############################################################
##  Implemented by:
##     - Joshua Fitch
##     - Purdue University AAE
##     - January 2023
##     - jfitch007@outlook.com
###############################################################
import random
import numpy as np
from numba import jit
from astropy import units as u
from poliastro.bodies import Earth
from adr_toolbox.optimize import VehicleRouting
from adr_toolbox.spacecraft import Shuttle, Picker, Mothership

# Set up some useful astrodynamic constants
MU_E = Earth.k.to_value(u.km**3 / u.s**2)
R_E = Earth.R_mean.to_value(u.km)
J2 = 1.08262668e-3

class Mission():
    """
    Class to solve Vehicle Routing Problem for various Mission Threads

    Accepts:
        - targets (dict): dict of Sat objects to target for removal
        - depots (dict): dict of Spacecraft objects acting as depots (may be None)
        - servicers (dict): dict of Spacecraft objects acting as servicing tugs
        - max_range (float): Limit on realistic delta-V budget
        - conservatism (float): Value from 0 to 6 that defines the number of std. dev.
          in expected reduced performance or additional costs
        - monte_carlo_size (int): Number of iterations to run for random sampling of
          altitude and inclination values to sample range of transfer costs
        - sim_step_size (int): Number of seconds for step size for fine timeseries

    Returns:
        - N/A
    """
    def __init__(
            self, targets, servicers, weights, year_limit,
            conservatism, monte_carlo_size, sim_step_size,
            no_route=True
        ):
        # Define set of debris targets based on subset (or full set) from SpaceEnv
        self.targets = list(targets.values())
        self.target_raans = []
        self.max_score = 0
        countries = []
        self.max_countries = 0
        for target in self.targets:
            self.max_score += target.score
            if target.country not in countries:
                countries.append(target.country)
                self.max_countries += 1

        # Define servicers to complete mission
        self.servicers = servicers

        # Initialize weights on delta-V vs ToF cost
        self.weights = weights
        self.year_limit = year_limit

        self.data_log = {}
        self.raan_data = {}

        # Set mission parameters for monte carlo runs and conservatism
        self.monte_carlo_size = monte_carlo_size
        self.conservatism = conservatism
        self.sim_step_size = sim_step_size
        self.no_route = no_route
        self.vehicle_used = []
        self.vehicle_mass = 0
        self.max_veh_mass = 0
        for servicer in servicers:
            self.max_veh_mass += servicer.wet_mass
            if isinstance(servicer, Mothership):
                self.max_veh_mass += servicer.modules[0].wet_mass * len(servicer.modules)

        # Setup an attribute to score optimization behavior
        self.ga_evo = {}
        self.best_route = None
        self.raw_metrics = {}


    def solve_mission(self):
        """ Locate optimal routing solutions for each vehicle """
        # Instantiate the optimizer object
        routing = VehicleRouting(
            self.__traverse_routes, len(self.targets), len(self.servicers),
            num_gens=10, pop_size=100 + len(self.targets)**3,
            weights=(1,), bit_mutate_prob=0.8, ind_mutate_prob=0.05,
            cross_prob=0.8, tourney_size=20
        )
        # Solve the optimization problem
        routing.optimize()
        # Store results of GA evolution
        gen, avg, best = routing.logbook.select("gen", "avg", "max")
        best_ever = routing.hof.items[0]
        self.ga_evo = {
            "gens": gen,
            "avg": avg,
            "best": best
        }

        # Access best solution
        self.best_route = list(best_ever)
        # Run the best solution
        self.__traverse_routes(best_ever)
        # Create a finer RAAN data timeseries
        self.__create_raan_data()


    def __traverse_routes(self, ind):
        """
        Compute cumulative score of objects able to be removed and how
        long it takes (assuming simultaneous missions)

        Accepts:
            - ind (list of ints): individual data string from genetic algorithm

        Returns:
            - performance (float): utility score combining cumulative score of remediated
              debris and total required mission duration to complete. Both factors are
              scaled by user-defined weights
        """
        # Use routing decoder to break up string into routes if multiple vehicles
        routes = self.__decode_routing(ind, len(self.servicers))

        if self.no_route is False:
            for route in routes:
                if len(route) == 0:
                    return (0.00001,)
        self.vehicle_used = np.zeros(len(self.servicers))
        self.vehicle_mass = 0
        available_refuels = 0
        refuels_used = 0
        self.raw_metrics = {
            "risk remediated": 0,
            "total tof": 0,
            "max tof": 0,
            "refuel mass": 0
        }

        # Initiate/reset the data logging dictionary and target RAANs for each run
        self.__setup_log()

        score_list = []
        tof_list = []
        policy_list = []
        # Iterate over each servicers route and see how far it gets
        for serv_ind, servicer in enumerate(self.servicers):
            self.__setup_target_raans()
            # setup route, refuelings, and starting prop mass
            route = routes[serv_ind]
            if isinstance(servicer, Picker):
                refuels = 0
            else:
                refuels = servicer.num_refuels
                available_refuels += servicer.num_refuels
            usable_prop = servicer.prop_mass

            vehicle_risk_reduction = 0
            vehicle_tof = 0
            estimated_tof = 0
            countries = []
            country_count = 0
            if isinstance(servicer, Mothership):
                module_masses = [x.wet_mass for x in servicer.modules]
            else:
                module_masses = [0]

            # Initial orbit is deployment orbit
            serv_loc = [servicer.a_0, servicer.inc_0, servicer.raan_0]

            # Log data at deployment
            self.__logging_data(servicer.name, 0, None, None, 0,
                usable_prop, 0, refuels,
                serv_loc[0], serv_loc[1], serv_loc[2]
            )

            # Iterate through each sequence of "wait -> up -> capture -> down"
            for i, t_ind in enumerate(route):
                #####################################
                ##       TRANSFER TO TARGET        ##
                #####################################
                # Get vehicle orbit and target orbit
                target = self.targets[t_ind]
                orbit1 = serv_loc
                orbit1_unc = [0, 0, 0]
                orbit2 = target.orbit_mean[0:2] + [self.target_raans[t_ind]]
                orbit2_unc = target.orbit_unc[0:3]

                # Compute prop mass, and ToF to reach target
                delta_v_1, prop_mass, transfer_tof_1 = self.__calc_transfer_costs(
                    orbit1, orbit1_unc, orbit2, orbit2_unc,
                    servicer.dry_mass + usable_prop + sum(module_masses),
                    servicer.thrust, servicer.isp
                )

                # If insufficient prop mass (with margin), check if refuel is available
                if isinstance(servicer, Mothership):
                    insuff_prop = (3 * prop_mass) > usable_prop
                else:
                    insuff_prop = (3 + np.ceil(target.mass / servicer.wet_mass)) \
                        * prop_mass > usable_prop

                # Try to refuel if insufficient propellant mass
                if insuff_prop:
                    if prop_mass > servicer.prop_mass or isinstance(servicer, Picker):
                        # Next target too far away to reach with full tank
                        continue
                    elif refuels > 0:
                        # Reset usable prop mass to initial prop mass
                        # assuming full refueling
                        usable_prop = servicer.prop_mass
                        refuels -= 1
                        # Log refueling
                        self.__logging_data(
                            servicer.name, 0, None, None, 0,
                            servicer.prop_mass, 0, refuels,
                            serv_loc[0], serv_loc[1], serv_loc[2]
                        )
                    else:
                        # If no refuels left, end the route
                        break

                # Based on transfer ToF and orbits calc total time of flight with RAAN
                raan_tof = self.__calc_raan_wait(
                    orbit1, orbit1_unc, orbit2, orbit2_unc, transfer_tof_1
                )

                # Update servicer location RAAN
                serv_loc[2] = self.__propagate_servicer_raan(
                                serv_loc[0], serv_loc[1], serv_loc[2], raan_tof
                            )

                # Make sure max vehicle ToF is within mission duration limit
                estimated_tof += raan_tof + 2 * transfer_tof_1
                if estimated_tof / 3600 / 24 / 365 > self.year_limit:
                    break

                # Log data after RAAN sync wait
                self.__logging_data(servicer.name, raan_tof, None, None,
                    0, usable_prop, 0,
                    refuels, serv_loc[0], serv_loc[1], serv_loc[2]
                )

                # Update usable prop mass
                usable_prop -= prop_mass

                # Update servicer location RAAN
                serv_loc[2] = self.__propagate_servicer_raan(
                                serv_loc[0], serv_loc[1], serv_loc[2], transfer_tof_1
                            )
                serv_loc[0:2] = orbit2[0:2]
                # Log data after transfer is complete
                self.__logging_data(
                    servicer.name, transfer_tof_1, None, None, 0,
                    usable_prop, delta_v_1, refuels,
                    serv_loc[0], serv_loc[1], serv_loc[2]
                )

                #####################################
                ##          CAPTURE TARGET         ##
                #####################################
                # Update servicer location RAAN
                serv_loc[2] = self.__propagate_servicer_raan(
                                serv_loc[0], serv_loc[1], serv_loc[2], servicer.docking_time
                            )
                # Update servicer prop mass
                usable_prop -= (servicer.dry_mass + usable_prop) * \
                    (1 - np.exp(-servicer.docking_dv / servicer.isp / 9.81))
                # Log data after transfer is complete
                self.__logging_data(
                    servicer.name, servicer.docking_time, t_ind, None, 0,
                    usable_prop, servicer.docking_dv, refuels,
                    serv_loc[0], serv_loc[1], serv_loc[2]
                )

                #####################################
                ##          DEORBIT TARGET         ##
                #####################################
                # Update starting and ending orbits
                orbit1 = orbit2
                orbit1_unc = orbit2_unc
                # Mothership and Shuttle reusable, don't fully deorbit
                if isinstance(servicer, Shuttle):
                    orbit2 = [R_E + servicer.drop_off_alt] + orbit1[1:3]
                    extra_mass = target.mass
                elif isinstance(servicer, Mothership):
                    orbit2 = [R_E + servicer.raan_sync_alt] + orbit1[1:3]
                    extra_mass = 0
                orbit2_unc = [0, 0, 0]

                if isinstance(servicer, Mothership):
                    time = self.data_log[servicer.name]["times"][-1]
                    deorbiter = servicer.modules[i]
                    # Remove module mass from Mothership baggage
                    module_masses[i] = 0
                    self.__logging_data(
                        deorbiter.name, time, None, None, 0,
                        deorbiter.prop_mass, 0, 0,
                        serv_loc[0], serv_loc[1], serv_loc[2]
                    )

                    # Compute how much altitude the deorbiter can drop the object
                    alt_drop, tof, d_v = self.__calc_alt_drop(
                        orbit1, deorbiter.wet_mass + target.mass,
                        deorbiter.prop_mass, deorbiter.thrust, deorbiter.isp
                    )

                    # Log data after transfer is complete
                    self.__logging_data(
                        deorbiter.name, tof, None, t_ind, target.score,
                        0, d_v, 0, (serv_loc[0] - alt_drop), serv_loc[1], serv_loc[2]
                    )

                # Only deorbit the first target in a route for a Picker
                if isinstance(servicer, Picker):
                    deorbiter = servicer
                    # Compute how much altitude the Picker can drop the object
                    alt_drop, transfer_tof_2, d_v = self.__calc_alt_drop(
                        orbit1, deorbiter.wet_mass + target.mass,
                        deorbiter.prop_mass, deorbiter.thrust, deorbiter.isp
                    )

                    # Log data after transfer is complete
                    self.__logging_data(
                        deorbiter.name, transfer_tof_2, None, t_ind, target.score,
                        0, d_v, 0, (serv_loc[0] - alt_drop), serv_loc[1], serv_loc[2]
                    )
                else:
                    # Compute dV, prop mass, ToF to deorbit target
                    delta_v_2, prop_mass, transfer_tof_2 = self.__calc_transfer_costs(
                        orbit1, orbit1_unc, orbit2, orbit2_unc,
                        servicer.dry_mass + usable_prop + extra_mass + sum(module_masses),
                        servicer.thrust, servicer.isp
                    )

                    # Update usable prop mass
                    usable_prop -= prop_mass

                    # Update servicer location RAAN
                    serv_loc[2] = self.__propagate_servicer_raan(
                                    serv_loc[0], serv_loc[1], serv_loc[2], transfer_tof_2
                                )
                    serv_loc[0:2] = orbit2[0:2]

                    target_val = t_ind
                    if isinstance(servicer, Mothership):
                        target_val = None

                    # Log data after transfer is complete
                    self.__logging_data(
                        servicer.name, transfer_tof_2, None, target_val, target.score,
                        usable_prop, delta_v_2, refuels,
                        serv_loc[0], serv_loc[1], serv_loc[2]
                    )

                vehicle_tof += raan_tof + transfer_tof_1 + \
                            servicer.docking_time + transfer_tof_2

                # Update where the target RAANs have precessed to
                self.__propagate_target_raans(vehicle_tof)

                # Update risk reduction and political complexity scores
                vehicle_risk_reduction += target.score
                if target.country not in countries:
                    country_count += 1
                    countries.append(target.country)

                # If mothership has used all deorbit modules, loiter in RAAN sync
                if isinstance(servicer, Mothership):
                    if sum(module_masses) == 0:
                        break

                # If picker mission, done after first target deorbited
                if isinstance(servicer, Picker):
                    break

            # Switch time to years
            vehicle_tof_years = vehicle_tof / 3600 / 24 / 365

            # Capture all non-dimensionalized vehicle scores
            score_list.append(vehicle_risk_reduction)
            tof_list.append(1/(1+(vehicle_tof_years / self.year_limit)))
            if self.max_countries == 1:
                policy_list.append(1)
            else:
                policy_list.append(1/(1+(country_count/self.max_countries)))

            self.raw_metrics["risk remediated"] += vehicle_risk_reduction
            self.raw_metrics["total tof"] += vehicle_tof_years
            if vehicle_tof_years > self.raw_metrics["max tof"]:
                self.raw_metrics["max tof"] = vehicle_tof_years
            if not isinstance(servicer, Picker):
                self.raw_metrics["refuel mass"] += (servicer.num_refuels - refuels) \
                    * servicer.prop_mass
                refuels_used += servicer.num_refuels - refuels

            if len(route) > 0:
                self.vehicle_used[serv_ind] = 1
                self.vehicle_mass += servicer.wet_mass
                if isinstance(servicer, Mothership):
                    self.vehicle_mass += servicer.modules[0].wet_mass * len(servicer.modules)

        if self.raw_metrics["risk remediated"] == 0:
            return (0.00001,)

        # Get final score metrics
        risk_score = 0.5 + (sum(score_list) / self.max_score / 2)
        time_score = min(tof_list)
        veh_score = 1/(1 + (self.vehicle_mass / self.max_veh_mass))
        policy_score = np.average(policy_list)
        alpha, beta, gamma, delta = self.weights

        # Compute weighted composite performance
        performance = alpha * risk_score + beta * time_score \
                      + gamma * veh_score + delta * policy_score

        return (performance,)


    @staticmethod
    def __decode_routing(ind, num_vehicles):
        """
        Take a string of routing indexes and split indices and 
        break up into distinct routes for each vehicle

        Accepts:
            - ind (list of ints): individual from GA, list of integers
            - num_vehicles (int): number of vehicles and therefore routes

        Returns:
            - routes (list of lists of ints): breakdown of distinct routes
        """
        # Get integers representing start of each vehicles route
        start_ints = [x for x in range(num_vehicles)]

        # Shift list to start at 0
        ind_shift = ind[ind.index(0):] + ind[:ind.index(0)]

        # Get the indices of the starting integers
        start_inds = []
        for i, integer in enumerate(ind_shift):
            if integer in start_ints:
                start_inds.append(i)

        # Split into distinct routes
        routes = [ind_shift[i:j] for i,j in zip(start_inds, start_inds[1:]+[None])]

        # Sort lists by vehicle index
        routes_sorted = sorted(routes, key=lambda x: x[0])

        # Shift values in each route by number of vehicles
        routes_shift = []
        for route in routes_sorted:
            routes_shift.append([x-num_vehicles for x in route[1:]])

        return routes_shift


    def __calc_transfer_costs(
            self, orbit1_mean, orbit1_unc, orbit2_mean, orbit2_unc, mass, thrust, isp
        ):
        """
        Calculate delta-V cost between orbits accounting for uncertainty

        If isp > 500s, use low-thrust Edelbaum/Kéchichian theory
        If isp < 500s, use impulsive approximation for circular inclined orbits

        Accepts:
            - orbit1_mean [list]: list of mean orbital elements for initial orbit
            - orbit1_unc [list]: list of orbital element std. dev. for initial orbit
            - orbit2_mean [list]: list of mean orbital elements for final orbit
            - orbit2_unc [list]: list of orbital element std. dev. for final orbit
            - mass (float) [kg]: initial mass of vehicle starting transfer
            - thrust (float) [Newtons]: force generated by propulsion system
            - isp (float) [seconds]: specific impulse efficiency of propulsion system

        Returns:
            - transfer_dv (float) [km/s]: delta-V to transfer between 
            - transfer_tof (float) [seconds]: time to complete transfer
            - prop_mass (float) [kg]: prop mass required to complete transfer
        """
        # Iterate over orbital element distributions
        dv_monte = []
        tof_monte = []
        prop_monte = []
        for _ in range(self.monte_carlo_size):
            # Get mean and std dev for initial orbit
            a_0_mean = orbit1_mean[0]
            a_0_unc = orbit1_unc[0] * self.conservatism
            inc_0_mean = orbit1_mean[1]
            inc_0_unc = orbit1_unc[1] * self.conservatism

            # Get mean and std dev for final orbit
            a_f_mean = orbit2_mean[0]
            a_f_unc = orbit2_unc[0] * self.conservatism
            inc_f_mean = orbit2_mean[1]
            inc_f_unc = orbit2_unc[1] * self.conservatism

            # Generate random sample from mean and std dev values
            a_0 = random.uniform(a_0_mean - a_0_unc, a_0_mean + a_0_unc)
            a_f = random.uniform(a_f_mean - a_f_unc, a_f_mean + a_f_unc)
            inc_0 = random.uniform(inc_0_mean - inc_0_unc, inc_0_mean + inc_0_unc)
            inc_f = random.uniform(inc_f_mean - inc_f_unc, inc_f_mean + inc_f_unc)

            # Computation for low-thrust
            if isp > 500:
                delta_v, prop_mass, tof = self.__low_thrust_transfer(
                    a_0, a_f, inc_0, inc_f, mass, isp, thrust
                )
            # Computation for impulsive
            if isp < 500:
                delta_v, prop_mass, tof = self.__impulse_transfer(
                    a_0, a_f, inc_0, inc_f, mass, isp
                )

            # Store data in monte carlo list
            dv_monte.append(delta_v)
            tof_monte.append(tof)
            prop_monte.append(prop_mass)

        # Get final delta-V and time of flight with conservatism
        transfer_dv = np.mean(dv_monte) + np.std(dv_monte) * self.conservatism
        transfer_tof = np.mean(tof_monte) + np.std(tof_monte) * self.conservatism
        prop_mass = np.mean(prop_monte) + np.std(prop_monte) * self.conservatism

        # Return final costs
        return transfer_dv, prop_mass, transfer_tof


    def __calc_raan_wait(self, orbit1_mean, orbit1_unc, orbit2_mean, orbit2_unc, transfer_tof):
        """
        Compute time necessary to sync two orbits RAAN

        Accepts:
            - orbit1_mean [list]: list of mean orbital elements for initial orbit
            - orbit1_unc [list]: list of orbital element std. dev. for initial orbit
            - orbit2_mean [list]: list of mean orbital elements for final orbit
            - orbit2_unc [list]: list of orbital element std. dev. for final orbit
            - transfer_tof (float) [secs]: time for active transfer between orbits

        Returns:
            - tof (float) [secs]: time required to wait in initial orbit for RAAN sync
        """
        tof_monte = []
        for _ in range(self.monte_carlo_size):
            # Get mean and std dev for initial orbit
            a_0_mean = orbit1_mean[0]
            a_0_unc = orbit1_unc[0] * self.conservatism
            inc_0_mean = orbit1_mean[1]
            inc_0_unc = orbit1_unc[1] * self.conservatism
            raan_0_mean = orbit1_mean[2]
            raan_0_unc = orbit1_unc[2] * self.conservatism

            # Get mean and std dev for final orbit
            a_f_mean = orbit2_mean[0]
            a_f_unc = orbit2_unc[0] * self.conservatism
            inc_f_mean = orbit2_mean[1]
            inc_f_unc = orbit2_unc[1] * self.conservatism
            raan_f_mean = orbit2_mean[2]
            raan_f_unc = orbit2_unc[2] * self.conservatism

            # Generate random sample from mean and std dev values
            a_0 = random.uniform(a_0_mean - a_0_unc, a_0_mean + a_0_unc)
            a_f = random.uniform(a_f_mean - a_f_unc, a_f_mean + a_f_unc)
            inc_0 = random.uniform(inc_0_mean - inc_0_unc, inc_0_mean + inc_0_unc)
            inc_f = random.uniform(inc_f_mean - inc_f_unc, inc_f_mean + inc_f_unc)
            raan_0 = random.uniform(raan_0_mean - raan_0_unc, raan_0_mean + raan_0_unc)
            raan_f = random.uniform(raan_f_mean - raan_f_unc, raan_f_mean + raan_f_unc)

            # Get raan precession rates for initial, transfer, and final orbit
            raan_dot_0 = self.calc_raan_dot(a_0, inc_0)
            raan_dot_tr = self.calc_raan_dot((a_0 + a_f)/2, (inc_0 + inc_f)/2)
            raan_dot_f = self.calc_raan_dot(a_f, inc_f)

            # Calculate RAAN offset for transfer time precession
            raan_offset = np.abs(raan_dot_tr - raan_dot_f) * transfer_tof

            # If initial orbit is ahead of and faster than, or behind and slower than,
            # the final orbit then we need to adjust the delta by a factor of 360 as
            # the initial orbit will "lap" the final orbit in raan precession
            if raan_0 > raan_f == raan_dot_0 > raan_dot_f:
                raan_delta = abs(360 - abs(raan_0 - raan_f) - raan_offset)
            else:
                raan_delta = abs(abs(raan_0 - raan_f) - raan_offset)

            # Compute delta in raan_dots for initial and final orbits
            raan_dot_delta = np.abs(raan_dot_0 - raan_dot_f)

            # Calculate time necessary to be cover remaining
            tof = raan_delta / raan_dot_delta

            tof_monte.append(tof)

        final_tof = np.mean(tof_monte) + np.std(tof_monte) * self.conservatism

        return final_tof


    def __calc_alt_drop(self, orbit1, mass, prop_mass, thrust, isp):
        """ Compute possible altitude decrease with available prop mass"""
        # Get initial semi-major axis
        a_0 = orbit1[0]

        for alt in [0, 100, 200, 300, 400, 500]:
            a_f = R_E + alt
            if isp < 500:
                d_v, req_prop_mass, tof = self.__impulse_transfer(
                    a_0, a_f, 0, 0, mass, isp
                )
            else:
                d_v, req_prop_mass, tof = self.__low_thrust_transfer(
                    a_0, a_f, 0, 0, mass, isp, thrust
                )
            if req_prop_mass < prop_mass:
                break

        alt_drop = a_0 - a_f

        return alt_drop, tof, d_v


    def __setup_target_raans(self):
        """ Initialize target raan tracking list """
        for target in self.targets:
            self.target_raans.append(target.orbit_mean[2])


    def __propagate_target_raans(self, tof):
        """
        Propagate forward all targets raan values

        Accepts:
            - tof [seconds]: time passage        
        """
        for i, target in enumerate(self.targets):
            # Get targets semi-major axis and inclination
            a_km = target.orbit_mean[0]
            inc_deg = target.orbit_mean[1]
            # Calculate RAAN precession rate
            raan_dot = self.calc_raan_dot(a_km, inc_deg)
            # Get last RAAN value
            last_raan = self.target_raans[i]
            # Take the 360 deg modulus
            new_raan = np.mod(last_raan + raan_dot * tof, 360)
            # Store new raan
            self.target_raans[i] = new_raan


    def __propagate_servicer_raan(self, a_km, inc_deg, raan_deg, tof):
        """
        Get Servicers new RAAN after some time

        Accepts:
            - a_km (float) [km]: current semi-major axis
            - inc_deg (float) [degs]: current inclination
            - raan_deg (float) [degs]: current RAAN location
            - tof (float) [seconds]: how long to propagate RAAN

        Returns:
            - new_raan (float) [degs]: new RAAN location of servicer        
        """
        # Calculate RAAN precession rate
        raan_dot = self.calc_raan_dot(a_km, inc_deg)
        # Take the 360 deg modulus
        new_raan = np.mod(raan_deg + raan_dot * tof, 360)

        return new_raan


    def __setup_log(self):
        """ Set up or refresh data log """
        for servicer in self.servicers:
            self.data_log[servicer.name] = {
                "times": [],
                "captured": [],
                "released": [],
                "scores": [],
                "prop_mass": [],
                "delta_vs": [],
                "refuels": [],
                "a_profile": [],
                "inc_profile": [],
                "raan_profile": []
            }
            if isinstance(servicer, Mothership):
                for module in servicer.modules:
                    self.data_log[module.name] = {
                        "times": [],
                        "captured": [],
                        "released": [],
                        "scores": [],
                        "prop_mass": [],
                        "delta_vs": [],
                        "refuels": [],
                        "a_profile": [],
                        "inc_profile": [],
                        "raan_profile": []
                    }


    def __logging_data(
            self, servicer_name, tof, capture, release, score,
            mass, delta_v, num_refuels, a_km, inc_deg, raan_deg
        ):
        """ Log all relevant data points as mission progresses """
        # Get the most recent time stamp
        if len(self.data_log[servicer_name]["times"]) == 0:
            previous_time = 0
        else:
            previous_time = self.data_log[servicer_name]["times"][-1]
        self.data_log[servicer_name]["times"].append(previous_time + tof)
        self.data_log[servicer_name]["captured"].append(capture)
        self.data_log[servicer_name]["released"].append(release)
        self.data_log[servicer_name]["scores"].append(score)
        self.data_log[servicer_name]["prop_mass"].append(mass)
        self.data_log[servicer_name]["delta_vs"].append(delta_v)
        self.data_log[servicer_name]["refuels"].append(num_refuels)
        self.data_log[servicer_name]["a_profile"].append(a_km)
        self.data_log[servicer_name]["inc_profile"].append(inc_deg)
        self.data_log[servicer_name]["raan_profile"].append(raan_deg)


    def __create_raan_data(self):
        """ Creates a finer time series dataset based on data log """
        # Store step size in convenient variable
        step = self.sim_step_size
        servicer_list = []
        for servicer in self.servicers:
            servicer_list.append(servicer)
            if isinstance(servicer, Mothership):
                servicer_list.extend(servicer.modules)
        # Initialize the time-series object
        for servicer in servicer_list:
            # Initialize the dictionary for this servicer
            raan_data = {
                "times": [],
                "raan_profile": []
            }

            # Get the data log for this servicer
            log = self.data_log[servicer.name]

            # Iterate through data log times and fill in the gaps
            # for the orbital motion variables (a, inc, raan)
            for i, time in enumerate(log["times"][:-1]):
                time_1 = self.__rounding(time, step)
                time_2 = self.__rounding(log["times"][i+1], step)
                if (time_2 - time_1) < 1:
                    continue
                times = range(time_1, time_2, step)
                raan_data["times"].extend(times)
                a_1 = log["a_profile"][i]
                a_2 = log["a_profile"][i+1]
                inc_1 = log["inc_profile"][i]
                inc_2 = log["inc_profile"][i+1]
                raan_0 = log["raan_profile"][i]
                raan_f = log["raan_profile"][i+1]
                a_t = np.average([a_2, a_1])
                inc_t = np.average([inc_2, inc_1])
                avg_raan_dot = self.calc_raan_dot(a_t, inc_t)
                for time in times:
                    raan_0 = np.mod(raan_0 + avg_raan_dot * step, 360)
                del_raan_1 = raan_f - raan_0
                del_raan_2 = 360 - abs(raan_f - raan_0)
                if raan_f > raan_0:
                    del_raan_2 = -del_raan_2
                if abs(del_raan_2) < del_raan_1:
                    raan_error = del_raan_2
                else:
                    raan_error = del_raan_1
                avg_raan_dot += raan_error / (time_2 - time_1)
                raan_0 = log["raan_profile"][i]
                for time in times:
                    raan_0 = np.mod(raan_0 + avg_raan_dot * step, 360)
                    raan_data["raan_profile"].append(raan_0)

            self.raan_data[servicer.name] = raan_data


    @staticmethod
    @jit(nopython=True)
    def __impulse_transfer(a_0, a_f, inc_0, inc_f, mass, isp):
        """
        Calculate delta-V, prop mass, and time of flight for impulsive transfer
        lower-velocity burn includes inc change
        """
        # Orbital velocities
        v_a_1 = np.sqrt(MU_E / a_0)
        v_a_2 = np.sqrt(2 * MU_E / a_0 - 2 * MU_E / (a_0 + a_f))
        v_b_1 = np.sqrt(2 * MU_E / a_f - 2 * MU_E / (a_0 + a_f))
        v_b_2 = np.sqrt(MU_E / a_f)
        # Check if transfer is increasing or decreasing altitude
        if a_f > a_0:
            # If altitude increasing, do inc change in second burn
            dv_1 = np.abs(v_a_1 - v_a_2)
            # Law of cosines for minimum possible delta-V
            dv_2 = np.sqrt(v_b_1**2 + v_b_2**2 - \
                2*v_b_1*v_b_2*np.cos(np.deg2rad(np.abs(inc_0-inc_f))))
        else:
            dv_1 = np.sqrt(v_a_1**2 + v_a_2**2 - \
                2*v_a_1*v_a_2*np.cos(np.deg2rad(np.abs(inc_0-inc_f))))
            dv_2 = np.abs(v_b_1 - v_b_2)
        delta_v = dv_1 + dv_2
        # Compute prop mass from ideal rocket equation
        prop_mass = mass * (1 - np.exp(-delta_v * 1000 / isp / 9.81))
        # Assume Hohmann, or half of transfer orbit period
        tof = np.pi * np.sqrt(((a_0 + a_f) / 2)**3 / MU_E)

        return delta_v, prop_mass, tof


    @staticmethod
    @jit(nopython=True)
    def __low_thrust_transfer(a_0, a_f, inc_0, inc_f, mass, isp, thrust):
        """
        Calculate delta-V, prop mass, and time of flight for low-thrust transfer
        
        Ref 1: Edelbaum, T. N. “Propulsion Requirements for Controllable Satellites”, 1961
        Ref 2: Kéchichian, J. A. “Reformulation of Edelbaum's Low-Thrust Transfer Problem
               Using Optimal Control Theory”, 1997
        """
        # Orbital velocities
        v_1 = np.sqrt(MU_E / a_0)
        v_2 = np.sqrt(MU_E / a_f)
        # Edelbaum equation
        delta_v = np.sqrt(v_1**2 + v_2**2 - \
            2*v_1*v_2*np.cos(np.deg2rad(np.abs(inc_0 - inc_f))*np.pi/2))
        # Compute prop mass from ideal rocket equation
        prop_mass = mass * (1 - np.exp(-delta_v * 1000 / isp / 9.81))
        # Calculate time of flight based on thrust and average mass
        tof = delta_v * 1000 / thrust * (mass - 0.5 * prop_mass)

        return delta_v, prop_mass, tof


    @staticmethod
    @jit(nopython=True)
    def calc_raan_dot(smj_ax, inc):
        """
        Compute RAAN precession rate

        Accepts:
            - smj_ax (float) [km]: semi-major axis in km
            - inc (float) [degs]: inclination in degrees

        Returns:
            - raan_dot (float) [degs/s]: raan precession in degrees per second
        """
        return np.rad2deg(-3/2 * J2 * R_E**2 / smj_ax**2 * \
            np.sqrt(MU_E / smj_ax**3) * np.cos(np.deg2rad(inc)))


    @staticmethod
    @jit(nopython=True)
    def __rounding(value, base):
        """
        Round a value to the nearest multiple of a base
        
        Accepts:
            - value (float): some number
            - base (float): some reference multiple
        
        Returns:
            - rounded_val (float): value rounded to nearest base
        """
        rounded_val = base * round(value/base)
        return rounded_val
