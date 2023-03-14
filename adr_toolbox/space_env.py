"""Container for adr_toolbox SpaceEnv class definitions"""
###############################################################
##  Implemented by:
##     - Joshua Fitch
##     - Purdue University AAE
##     - January 2023
##     - jfitch007@outlook.com
###############################################################
import json
from datetime import datetime
import numpy as np
from numba import jit
from astropy import units as u
import poliastro.twobody.thrust as model
from poliastro.bodies import Earth
from sklearn.cluster import DBSCAN
from alive_progress import alive_bar
from adr_toolbox.satellite import Sat

class SpaceEnv():
    """
    Class contains space environment of objects to be analyzed
    
    Attributes:
        - sat_dict (dict): keys = NORAD ID, values = corresponding Sat object
        - api_data (dict): ingests raw data from api call
        - spatial_density (dict): keys = altitude bins [km], values = density [objects / km^3]

    Methods:
        - from_api_data: initialize space environment from api data
        - propagate_env: propagate all satellites in environment to future date
        - score_env: calculate CSI score for each object in environment
        - calc_spatial_density: populate spatial density dict based on objects in env
        - rounding [static]: round altitude to nearest bucket
    
    """
    def __init__(self):
        """Initialize by creating default empty attributes"""
        # Initialize empty dict to hold eventual Debris instances
        self.sat_dict = {}
        # Initialize empty dicts to process raw API data
        self.api_data = {}
        # Initialize empty spatial density dict
        self.spatial_density = {}
        # Initialize dict to track propagation status error codes
        self.prop_status_dict = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0}
        # Initialize transfer_dv matrix
        self.transfer_dvs = None
        # Initialize list of distinct labels from DBScan clustering
        self.core_labels = None
        # Initialize a dict to cluster sat dict
        self.cluster_dict = {}


    def from_api_data(self, file_name):
        """
        Method to instantiate space environment by ingesting api data json, 
        instantiating Debris objects and saving to obj_dict

        Accepts:
            - file_name (str): name of json file containing api data
        
        Returns:
            - N/A
        """

        with open(f'{file_name}.json', 'r', encoding='utf-8') as json_file:
            api_data = json.load(json_file)

        print("Initializing Environment by propagating to current datetime:")
        with alive_bar(int(len(api_data.values())-1)) as prog_bar:
            for key, data in api_data.items():
                if key == "__header":
                    continue
                sat = Sat()
                norad_id = key
                sat.from_api_dict(norad_id, data)
                self.sat_dict[norad_id] = sat
                prog_bar() # pylint: disable=not-callable

        self.__compute_and_report_prop_status()


    def propagate_env(self, year, month=1, day=1, hour=0, minute=0, sec=0):
        """
        Propagate entire environment of objects to some future date

        Accepts:
            - year    (float) [required]: future year to propagate to
            - month   (float) [optional, default = Jan]
            - day     (float) [optional, default = 1st]
            - hour    (float) [optional, default = midnight]
            - minute  (float) [optional, default = top of hour]
            - sec     (float) [optional, default = top of minute]

        Returns:
            - N/A
        """
        print(f"Propagating Env to year {year}:")
        with alive_bar(int(len(self.sat_dict.values()))) as prog_bar:
            for sat in self.sat_dict.values():
                sat.propagate_to(year, month, day, hour, minute, sec)
                prog_bar() # pylint: disable=not-callable

        # Reset prop status dict
        self.prop_status_dict = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0}
        self.__compute_and_report_prop_status()


    def score_env(self, spatial_density):
        """
        Scores each object in environment at the time that env has been propagated to
        does not use it's own spatial density, as you typically do not want to score
        the entire LEO environment, just a smaller portion (i.e. just RCS > 1m^2)

        Accepts:
            - spatial_density (dict): spatial density of LEO from another space_env instance
        
        Returns:
            - N/A
        """
        bucket_size = list(spatial_density.keys())[1] - list(spatial_density.keys())[0]
        for sat in self.sat_dict.values():
            # For each successfully propagated satellite, calc CSI score
            if sat.prop_status == 0:
                rounded_alt = self.rounding(
                    (sat.orbit_mean[0] - Earth.R_mean.to_value(u.km)), bucket_size
                )
                # Make sure orbit is realistic, sometimes SGP4 is weird
                if rounded_alt in range(400, 2000):
                    # Normalize spatial density flux around maximum
                    flux = spatial_density[rounded_alt] / max(spatial_density.values())
                    sat.calc_score(flux)


    def calc_spatial_density(self, bucket_size, exclude_starlink=False):
        """
        Populate spatial density dict [objects/km^3] as a function of altitude [km]
        
        Accepts:
            - bucket_size (float): size of each altitude bin [km]
            - exclude_starlink (bool) [optional, default = False]: should Starlinks be excluded

        Returns:
            - N/A
        """
        # Effective bounds on LEO
        lower_limit = 400
        upper_limit = 2000

        # Create altitude bucket increments
        alt_range = range(lower_limit, upper_limit, bucket_size)

        # Initialize dict with alt bucket centers as dict keys
        for alt in alt_range:
            self.spatial_density[alt] = 0

        # Iterate through all satellites in environment
        for sat in self.sat_dict.values():
            # See how spatial density is impacted if we don't consider Starlinks
            if (exclude_starlink is True) and (sat.satname is not None):
                if "STARLINK" in sat.satname:
                    continue
            if sat.prop_status == 0:
                # For each successfully propagated satellite, find the mean altitude nearest bucket
                rounded_alt = self.rounding(
                    (sat.orbit_mean[0] - Earth.R_mean.to_value(u.km)), bucket_size
                )
                # Some objects have funky orbits with incorrect smj_ax values after SGP4 prop
                if rounded_alt in range(lower_limit, upper_limit):
                    self.spatial_density[rounded_alt] += 1


    def cluster_by_dv(self, dv_dist, min_objects):
        """
        Utilize DBSCAN for network spatial clustering of objects based on transfer delta-V
        
        Accepts:
            - dv_dist (float): max distance between objects to be considered in the same cluster
            - min_objects (int): minimum number of proximal objects to create a cluster

        Returns:
            - N/A
        """
        # Call method to populate transfer delta-V matrix
        self.calc_transfer_dvs()

        # Initialize the DBSCAN object
        clustering = DBSCAN(eps=dv_dist, min_samples=min_objects, metric="precomputed")
        # Fit the clustering to the delta-V matrix
        out = clustering.fit(self.transfer_dvs)

        # Capture distinct labels
        core_labels = []
        for i, label in enumerate(out.labels_):
            # Create list of distinct labels
            if len(core_labels) == 0:
                core_labels.append(label)
            elif label not in core_labels:
                core_labels.append(label)

            # Assign label to sat object
            sat = list(self.sat_dict.values())[i]
            sat.label = label

        # Assign list of distinct labels as attribute
        self.core_labels = core_labels

        # Create dict to break out clusters of sats
        self.__create_cluster_dicts()


    def calc_transfer_dvs(self):
        """
        Calculate full matrix of low-thrust transfers between pairs of objects
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
        # Initialize transfer_dv matrix to size for number of objects
        self.transfer_dvs = np.zeros((len(self.sat_dict.values()), len(self.sat_dict.values())))
        print("Computing Transfer Costs:")
        # Iterate through each pair of objects
        with alive_bar(int(len(self.sat_dict.values()))) as prog_bar:
            for i, sat_0 in enumerate(self.sat_dict.values()):
                for j, sat_f in enumerate(self.sat_dict.values()):
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
                    self.transfer_dvs[i][j] = out[1]
                prog_bar() # pylint: disable=not-callable


    def filter_top_scores(self, num_objects):
        """
        Filters objects sat_dict to only the top-scored objects and sort

        Accepts:
            - num_objects (int): The number of top-scored objects to be filtered

        Returns:
            - N/A
        """
        # Create empty dict to hold new filtered, ordered sat objects
        new_sat_dict = {}

        # Create dict of NORAD ID as keys and scores as values
        score_dict = {}
        for sat in self.sat_dict.values():
            # Some objects may not be scored due to a lack of mass information
            if sat.score is not None:
                score_dict[sat.satno] = sat.score

        # Sort the ordering of the dictionary by score from largest to smallest
        sorted_score_dict = dict(sorted(score_dict.items(), key=lambda item: item[1], reverse=True))

        # Populate the new sat dict in order from largest scores to smallest, up to number specified
        for norad_id in list(sorted_score_dict)[:num_objects]:
            new_sat_dict[norad_id] = self.sat_dict[norad_id]

        # Re-assign attribute sat_dict to newly sorted and filtered list
        self.sat_dict = new_sat_dict


    def __create_cluster_dicts(self):
        """
        Saves a dict of dicts. Each dict represents a distinct DBScan cluster
        of Sat objects. Sub dicts are dictionaries of each sat in the cluster
        based on DBScan.

        Accepts:
            - N/A

        Returns:
            - N/A
        """
        for i, label in enumerate(sorted(self.core_labels, reverse=True)):
            # Define names for cluster labels
            if label == -1:
                dict_key = "Isolated"
            else:
                dict_key = f"Cluster {i + 1}"

            # Assign Sats to cluster dict
            self.cluster_dict[dict_key] = {}
            for norad_id, sat in self.sat_dict.items():
                if sat.label == label:
                    self.cluster_dict[dict_key][norad_id] = sat


    def export_scorecard_json(self, file_name, num_objects):
        """"
        Exports top X objects NORAD Catalog ID's and CSI scores (with std. dev.)

        Accepts:
            - file_name (str): Name of json file to create/export to
            - num_objects (int): The number of top-scored objects to be exported

        Returns:
            - Exports json file with NORAD ID's, scores, and score std. dev.
        """
        data = {"__header":{}, "data":[]}
        data["__header"]["description"] = \
            f"{num_objects} top scored objects based on Criticality of Spacecraft Index"
        data["__header"]["source"] = \
            "CSI Paper: https://www.sciencedirect.com/science/article/pii/S0273117715001556"
        data["__header"]["creation_timestamp"] = datetime.now()
        data["__header"]["prop_epoch"] = list(self.sat_dict)[0].prop_epoch

        # Create dict of NORAD ID as keys and scores as values
        score_dict = {}
        for sat in self.sat_dict:
            score_dict[sat.satno] = sat.score

        # Sort the ordering of the dictionary by score from largest to smallest
        sorted_score_dict = dict(sorted(score_dict.items(), key=lambda item: item[1], reverse=True))

        # For the first X objects, append relevant data to dictionary for export
        for norad_id in list(sorted_score_dict)[:num_objects]:
            data["data"].append({
                "satno": norad_id,
                "score": self.sat_dict[norad_id].score,
                "score std dev": self.sat_dict[norad_id].score_std_dev
            })

        # Dump data dictionary to json file for later access
        with open(f'{file_name}.json', 'w+', encoding="utf-8") as outfile:
            print(json.dumps(data, indent=4), file=outfile)


    def __compute_and_report_prop_status(self):
        """
        Sum up and print report on overall success of environment propagation

        Accepts:
            - N/A

        Returns:
            - N/A
        """
        ecc_error_alts = []
        for sat in self.sat_dict.values():
            if sat.prop_status == 1:
                ecc_error_alts.append(sat.orbit_mean[0] - Earth.R_mean.to_value(u.km))
            self.prop_status_dict[sat.prop_status] += 1
        if len(ecc_error_alts) > 0:
            ecc_error_avg_alt = np.median(ecc_error_alts)
        else:
            ecc_error_avg_alt = None

        print("\n===========================")
        print("Environment Prop Status:")
        print("===========================")
        print(f"Successful Propagations: {self.prop_status_dict[0]}")
        print(f"Eccentricity Errors: {self.prop_status_dict[1]}")
        print(f"    (Ecc Error Median Alt = {ecc_error_avg_alt})")
        print(f"Mean Motion Errors: {self.prop_status_dict[2]}")
        print(f"Perturbed Ecc. Errors: {self.prop_status_dict[3]}")
        print(f"Semilatus Rectum Errors: {self.prop_status_dict[4]}")
        print(f"[deprecated error type]: {self.prop_status_dict[5]}")
        print(f"Orbit has Decayed: {self.prop_status_dict[6]}\n")


    @staticmethod
    @jit(nopython=True)
    def rounding(value, base):
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
