"""Container for adr_toolbox Satellite class definitions"""
###############################################################
##  Implemented by:
##     - Joshua Fitch
##     - Purdue University AAE
##     - January 2023
##     - jfitch007@outlook.com
###############################################################
from datetime import datetime
import numpy as np
from numba import jit
from astropy import units as u
from astropy.time import Time
from poliastro.bodies import Earth
from poliastro.twobody import Orbit
from sgp4.api import Satrec, jday

class Sat():
    """
    Stores, propagates, and scores an orbital satellite
    
    Attributes:
        - satno (int): NORAD Catalog ID
        - orbits (list of objects): list of Poliastro orbit objects
        - orbit_mean (list): list of 6 orbital elements average values
        - orbit_unc (list): list of 6 orbital element std dev
        - orbit_elems (list of lists): list of 6 lists of orbital elements
        - tle_list (list): list of TLE strings used to create Sat objects
        - prop_status (int): Code of most recent propagation (https://pypi.org/project/sgp4/)
        - prop_epoch (datetime): Epoch of propagation of environment
        - satname (str): name of satellite
        - country (str): country code of satellite owner/launcher
        - obj_type (str): classification of object
        - mass (float): mass of object
        - xsec_avg (float): average cross-sectional area of object
        - score (float): CSI score for object
        - score_std_dev (float): CSI standard deviation based on orbital element std dev
        - label (float): label assigned from DBScan clustering

    Methods:
        - from_api_dict: initialize object attributes from api dictionary data
        - propagate_to: propagate orbit(s) to future date
        - calc_score: manage calculation of CSI score and std dev
        - __csi_calc [private]: calculate csi score
        - __calc_orbit_unc [private]: calculate std dev of orbital elements
            
    """
    def __init__(self):
        """Initialize all attributes"""
        self.satno = None
        self.orbits = []
        self.orbit_mean = []
        self.orbit_unc = []
        self.orbit_elems = []
        self.tle_list = []
        self.prop_status = None
        self.prop_epoch = None
        self.satname = None
        self.country = None
        self.obj_type = None
        self.mass = None
        self.xsec_avg = None
        self.score = None
        self.score_std_dev = None
        self.label = None


    def from_api_dict(self, satno, sat_dict):
        """
        Assigns all satellite object attributes based on dict of DISCOSweb
        and Space-Track data from api class output

        Accepts:
            - satno (int): NORAD Catalog ID as an integer

        Returns:
            - N/A
        """
        # Assign basic Space-Track elements
        self.satno = satno
        self.country = sat_dict["gp_hist"][0]["COUNTRY_CODE"]
        self.satname = sat_dict["gp_hist"][0]["OBJECT_NAME"]

        # Check if DISCOSweb data was available for object
        if len(sat_dict.items()) > 1:
            # If Space-Track doesn't give a name, see if DISCOSweb does
            if self.satname is None:
                self.satname = sat_dict["name"]
            # Assign other useful quantities
            self.obj_type = sat_dict["objectClass"]
            self.mass = sat_dict["mass"]
            self.xsec_avg = sat_dict["xSectAvg"]

        # Propagate all spacetrack gp data to current time
        now = Time.now()
        self.prop_epoch = datetime.now()
        for gp_data in sat_dict["gp_hist"]:
            # Store TLE strings as attributes for future usage
            self.tle_list.append([gp_data["TLE_LINE1"], gp_data["TLE_LINE2"]])
            # Create SGP4 satellite object from most recently saved TLE's
            sat = Satrec.twoline2rv(self.tle_list[-1][0], self.tle_list[-1][1])
            # Propagate satellite to current time using SGP4
            self.prop_status, pos, vel = sat.sgp4(now.jd1, now.jd2)
            # Confirm propagation successful
            if self.prop_status == 0:
                # Add poliastro orbit object to list
                self.orbits.append(Orbit.from_vectors(Earth, pos << u.km, vel << u.km / u.s))
            else:
                # Often, propagation errors are due to low-altitude
                if (sat.am - 1) * sat.radiusearthkm < 400: # pylint: disable=E1101:no-member
                    # If altitude <400 km, will deorbit in ~1 year, not a concern
                    self.prop_status = 6
                else:
                    # If propagation failed, take last set of valid mean orbital elements
                    self.orbit_mean.append(sat.am * sat.radiusearthkm) # pylint: disable=E1101:no-member
                    self.orbit_mean.append(np.rad2deg(sat.im)) # pylint: disable=E1101:no-member
                    self.orbit_mean.append(np.rad2deg(sat.Om)) # pylint: disable=E1101:no-member
                    self.orbit_mean.append(sat.em) # pylint: disable=E1101:no-member
                    self.orbit_mean.append(np.rad2deg(sat.om)) # pylint: disable=E1101:no-member
                    self.orbit_mean.append(np.rad2deg(sat.nm)) # pylint: disable=E1101:no-member

        # Calculate orbital element mean and std. dev.
        if self.prop_status == 0:
            self.__calc_orbit_unc()


    def propagate_to(self, year, month=1, day=1, hour=0, minute=0, sec=0):
        """
        Propgate orbit object(s) to a future date using SGP4
        """
        # Calculate corresponding Julian Date elements
        jd_time, fr_time = jday(year, month, day, hour, minute, sec)
        self.prop_epoch = datetime(year=year,month=month,day=day,hour=hour,minute=minute,second=sec)
        self.orbits = []
        for tle in self.tle_list:
            # Create SGP4 satellite object from most recently saved TLE's
            sat = Satrec.twoline2rv(tle[0], tle[1])
            # Propagate satellite to current time using SGP4
            self.prop_status, pos, vel = sat.sgp4(jd_time, fr_time)
            # Confirm propagation successful
            if self.prop_status == 0:
                # Add poliastro orbit object to list
                self.orbits.append(Orbit.from_vectors(Earth, pos << u.km, vel << u.km / u.s))
            elif self.prop_status == 1:
                # Often, eccentricity errors are due to low-altitude
                if (sat.am - 1) * sat.radiusearthkm < 400: # pylint: disable=E1101:no-member
                    # If altitude <400 km, will deorbit in ~1 year, not a concern
                    self.prop_status = 6
                else:
                    # If propagation failed, take last set of valid mean orbital elements
                    self.orbit_mean.append(sat.am * sat.radiusearthkm) # pylint: disable=E1101:no-member
                    self.orbit_mean.append(np.rad2deg(sat.im)) # pylint: disable=E1101:no-member
                    self.orbit_mean.append(np.rad2deg(sat.Om)) # pylint: disable=E1101:no-member
                    self.orbit_mean.append(sat.em) # pylint: disable=E1101:no-member
                    self.orbit_mean.append(np.rad2deg(sat.om)) # pylint: disable=E1101:no-member
                    self.orbit_mean.append(np.rad2deg(sat.nm)) # pylint: disable=E1101:no-member

        # Calculate orbital element mean and std. dev.
        if self.prop_status == 0:
            self.__calc_orbit_unc()


    def calc_score(self, flux_norm):
        """
        Calculate the "Criticality of Spacecraft Index" value of object
        Source: https://www.sciencedirect.com/science/article/pii/S0273117715001556

        Accepts:
            - flux_norm (float): normalized spatial density at altitude [objects / km^3]

        Returns:
            - N/A
        """
        # If mass of object is not known, assign score of 0
        if self.mass is None:
            self.score = 0
        else:
            # Convert semi-major axis to mean altitude
            alt_mean = self.orbit_mean[0]  - Earth.R_mean.to_value(u.km)
            inc_mean = self.orbit_mean[1]
            # Start by calculating score for mean orbital elements
            self.score = self.__csi_calc(flux_norm, self.mass, alt_mean, inc_mean)

            # If we have multiple orbit data points to work with, calculate score uncertainty
            if len(self.orbits) > 1:
                score_list = []
                alt_stddev = self.orbit_unc[0]
                inc_stddev = self.orbit_unc[1]
                for alt in np.linspace(alt_mean-alt_stddev, alt_mean+alt_stddev, 5):
                    for inc in np.linspace(inc_mean-inc_stddev, inc_mean+inc_stddev, 5):
                        score_list.append(self.__csi_calc(flux_norm, self.mass, alt, inc))

                # Calculate std dev of score
                self.score_std_dev = np.std(score_list)


    @staticmethod
    @jit(nopython=True)
    def __csi_calc(flux_norm, mass, alt, inc):
        """
        Calculate the "Criticality of Spacecraft Index" value of object
        Source: https://www.sciencedirect.com/science/article/pii/S0273117715001556

        Accepts:
            - flux_norm (float): normalized spatial density at altitude [objects / km^3]
            - mass (float): mass of object [kg]
            - alt (float): altitude of objects orbit [km]
            - inc (float): inclination of objects orbit [degs]

        Returns:
            - score (float): CSI score of object
        """
        # ============== LIFETIME SCORE ===================
        # Normalize lifetime score by altitude of 1000 km
        ref_life = 14.18 * 1000 ** 0.1831 - 42.94
        # Calculate actual lifetime for object
        lifetime = 14.18 * alt ** 0.1831 - 42.94
        # Calculate normalized lifetime score
        life_norm = lifetime / ref_life

        # ================ MASS SCORE =====================
        # Calculate normalized mass score for reference object of 10,000 kg
        mass_norm = mass / 10000

        # ============ INCLINATION SCORE ==================
        k = 0.6
        gamma = (1 - np.cos(inc)) / 2
        inc_norm = (1 + k * gamma) / (1 + k)

        # ============= TOTAL CSI SCORE ===================
        return flux_norm * mass_norm * life_norm * inc_norm


    def __calc_orbit_unc(self):
        """Private method to calculate orbital element mean and std dev"""
        # List of a, inc, raan, ecc, argp, ta
        orb_elems = [[], [], [], [], [], []]
        for orbit in self.orbits:
            orb_elems[0].append(float(orbit.a.to_value(u.km)))
            orb_elems[1].append(float(orbit.inc.to_value(u.deg)))
            orb_elems[2].append(float(orbit.raan.to_value(u.deg)))
            orb_elems[3].append(float(orbit.ecc.to_value()))
            orb_elems[4].append(float(orbit.argp.to_value(u.deg)))
            orb_elems[5].append(float(orbit.nu.to_value(u.deg)))

        # Save all orbital elements for future access
        self.orbit_elems = orb_elems

        # Get mean and std dev for each orbital element list
        for elem in orb_elems:
            self.orbit_mean.append(np.mean(elem))
            self.orbit_unc.append(np.std(elem))
