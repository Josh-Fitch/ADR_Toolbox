"""Container for adr_toolbox Architecture class definitions"""
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

class Architecture():
    """
    """
    def __init__(self, missions):
        """
        """
        self.missions = missions
        


    def calc_ddte_costs(self, quantity, year, difficulty, block):
        """
        """
        alpha = 5.65e-4
        beta = 0.5941
        theta = 0.6604
        delta = 80.599
        epsilon = 3.8085e-55
        phi = -0.3553
        gamma = 1.5691

        mass = self.wet_mass
        spec = 2.00

        cost = alpha * quantity ** beta * mass ** theta * \
               delta ** spec * epsilon ** (1/(year-1900)) * \
               block ** phi * gamma ** difficulty
        
        # approximate 80% increase from 1999 to 2023 from inflation
        cost_adjusted = 1.8 * cost

        self.ddte_cost = cost_adjusted

    def calc_launch_costs(self):
        """
        """
    
    def calc_ops_costs(self):
        """
        """
    
    def calc_total_costs(self):
        """
        """
        self.cost = self.ddte_cost + self.launch_cost + self.ops_cost