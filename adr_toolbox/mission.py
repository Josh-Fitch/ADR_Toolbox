"""Container for adr_toolbox Mission class definitions"""
###############################################################
##  Implemented by:
##     - Joshua Fitch
##     - Purdue University AAE
##     - January 2023
##     - jfitch007@outlook.com
###############################################################
import numpy as np
import json
from numba import jit
from alive_progress import alive_bar
from astropy import units as u
import poliastro.twobody.thrust as model
from poliastro.bodies import Earth

class Mission():
    """
    """
    def __init__(self, sat_dict):
        """
        """
        # Define set of debris targets based on subset (or full set) from SpaceEnv
        self.targets = sat_dict
        # Initialize transfer_dv matrix by number of targets
        self.transfer_dvs = np.zeros((len(self.targets.values()), len(self.targets.values())))
        # Initialize servicing vehicles
        self.servicers = None
        # Initialize depots
        self.depots = None


    def calc_transfer_dvs(self):
        """
        Calculate full matrix of low-thrust transfers between pairs of targets
        using the Edelbaum/Kéchichian theory, optimal transfer between
        circular inclined orbits (a_0, i_0) -> (a_f, i_f), ecc = 0

        Ref 1: Edelbaum, T. N. “Propulsion Requirements for Controllable Satellites”, 1961
        Ref 2: Kéchichian, J. A. “Reformulation of Edelbaum's Low-Thrust Transfer Problem
               Using Optimal Control Theory”, 1997

        Accepts:
            - N/A

        Returns:
            - N/A
        """
        print("Computing Transfer Costs:")
        # Iterate through each pair of objects
        with alive_bar(int(len(self.targets.values()))) as prog_bar:
            for i, sat_0 in enumerate(self.targets.values()):
                for j, sat_f in enumerate(self.targets.values()):
                    # Object has zero cost to itself
                    if i == j:
                        continue
                    # Acceleration does not impact delta-V, only ToF
                    accel = 1 << u.km / u.s**2
                    a_0 = sat_0.orbit_mean[0] << u.km
                    inc_0 = sat_0.orbit_mean[1] << u.deg
                    a_f = sat_f.orbit_mean[0] << u.km
                    inc_f = sat_f.orbit_mean[1] << u.deg
                    out = model.change_a_inc(Earth.k, a_0, a_f, inc_0, inc_f, accel)
                    # Google OR-Tools need integer distances, convert to m/s and round to int
                    self.transfer_dvs[i][j] = round(out[1].to_value(u.m / u.s))
                prog_bar() # pylint: disable=not-callable


    def picker(self):
        """
        """
        pass

    def shuttle(self):
        """
        """
        pass

    def mothership(self):
        """
        """
        pass

    def recycler(self):
        """
        """
        pass
