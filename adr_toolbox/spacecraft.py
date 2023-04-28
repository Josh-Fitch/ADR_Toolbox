"""Container for adr_toolbox SpaceEnv class definition"""
###############################################################
##  Implemented by:
##     - Joshua Fitch
##     - Purdue University AAE
##     - January 2023
##     - jfitch007@outlook.com
###############################################################

class Spacecraft():
    """
    Class for generic spacecraft platform or module

    Attributes:
        - wet_mass (float) [kg]: total launch mass of vehicle including payload
        - pmf (float) [n.d.]: fraction in range(0,1) capturing what fraction of vehicle
          mass is propellant
        - dry_mass (float) [kg]: mass of vehicle that is NOT propellant
        - prop_mass (float) [kg]: mass of vehicle that is propellant
        - thrust (float) [Newtons]: engine force generated (assumed constant)
        - isp (float) [seconds]: specific Impulse describing efficiency of engine

    Methods:
        - N/A
    """
    def __init__(
            self, name, wet_mass, pmf, thrust, isp,
            block, difficulty
        ) -> None:
        # Initialize spacecraft mass breakdown based on propellant mass fraction
        self.name = name
        self.wet_mass = wet_mass
        self.dry_mass = wet_mass * (1 - pmf)
        self.prop_mass = wet_mass * pmf
        self.thrust = thrust
        self.isp = isp
        self.block = block
        self.difficulty = difficulty


class Shuttle(Spacecraft):
    """
    Subclass of Spacecraft for shuttles

    Accepts:
        - a_0 (float) [km]: Semi-Major Axis of initial deployment orbit
        - inc_0 (float) [degs]: Inclination of initial deployment orbit
        - raan_0 (float) [degs]: Right Ascension of Ascending Node of initial deployment orbit
        - num_refuels (int): Number of full refuelings available

    Returns:
        - N/A
    """
    def __init__(
            self, name, wet_mass, pmf, thrust, isp,
            block, difficulty,
            a_0, inc_0, raan_0, drop_off_alt,
            docking_time, docking_dv, num_refuels
        ) -> None:
        super().__init__(name, wet_mass, pmf, thrust, isp, block, difficulty)
        self.a_0 = a_0
        self.inc_0 = inc_0
        self.raan_0 = raan_0
        self.drop_off_alt = drop_off_alt
        self.docking_time = docking_time
        self.docking_dv = docking_dv
        self.num_refuels = num_refuels


class Picker(Spacecraft):
    """
    Subclass of Spacecraft for pickers

    Accepts:
        - a_0 (float) [km]: Semi-Major Axis of initial deployment orbit
        - inc_0 (float) [degs]: Inclination of initial deployment orbit
        - raan_0 (float) [degs]: Right Ascension of Ascending Node of initial deployment orbit

    Returns:
        - N/A
    """
    def __init__(
            self, name, wet_mass, pmf, thrust, isp,
            block, difficulty, a_0, inc_0, raan_0,
            docking_time, docking_dv
        ) -> None:
        super().__init__(name, wet_mass, pmf, thrust, isp, block, difficulty)
        self.a_0 = a_0
        self.inc_0 = inc_0
        self.raan_0 = raan_0
        self.docking_time = docking_time
        self.docking_dv = docking_dv

class Mothership(Spacecraft):
    """
    Subclass of Spacecraft for motherships

    Accepts:
        - a_0 (float) [km]: Semi-Major Axis of initial deployment orbit
        - inc_0 (float) [degs]: Inclination of initial deployment orbit
        - raan_0 (float) [degs]: Right Ascension of Ascending Node of initial deployment orbit
        - num_refuels (int): Number of full refuelings available
        - modules (list of objs): List of Deorbit Modules (instances of Spacecraft)

    Returns:
        - N/A
    """
    def __init__(
            self, name, wet_mass, pmf, thrust,
            isp, block, difficulty,
            a_0, inc_0, raan_0,
            raan_sync_alt, docking_time, docking_dv,
            num_refuels, modules
        ) -> None:
        super().__init__(name, wet_mass, pmf, thrust, isp, block, difficulty)
        self.a_0 = a_0
        self.inc_0 = inc_0
        self.raan_0 = raan_0
        self.raan_sync_alt = raan_sync_alt
        self.docking_time = docking_time
        self.docking_dv = docking_dv
        self.num_refuels = num_refuels
        self.modules = modules
