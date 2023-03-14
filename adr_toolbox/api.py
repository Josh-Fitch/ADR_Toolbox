"""Container for adr_toolbox SpaceEnv class definition"""
###############################################################
##  DISCOSweb docs: https://discosweb.esoc.esa.int/apidocs/v2
##  Space-Track docs: https://www.space-track.org/documentation
##
##  Implemented by:
##     - Joshua Fitch
##     - Purdue University AAE
##     - January 2023
##     - jfitch007@outlook.com
###############################################################
##  !! INCLUDE A 30 SECOND SLEEP BETWEEN API CALLS TO STAY BELOW THROTTLE LIMITS !!
import json
import time
import configparser
from datetime import datetime
from alive_progress import alive_bar
import requests
import urllib3
# DISCOweb will sometimes not successfully verify, but we trust it anyways
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


#############################################
#####            API LINKS              #####
#############################################
URLBASE_DW         = "https://discosweb.esoc.esa.int/api/objects"
URLBASE_ST         = "https://www.space-track.org"
REQ_LOGIN          = "/ajaxauth/login"
REQ_QUERY          = "/basicspacedata/query"
REQ_GP1            = "/class/gp/NORAD_CAT_ID/"
REQ_GP2            = "/format/json"
REQ_GP_HIST1       = "/class/gp_history/NORAD_CAT_ID/"
REQ_GP_HIST2       = "/orderby/EPOCH desc/limit/"
REQ_GP_HIST3       = "/format/json"
REQ_GP_LEO         = "/class/gp/EPOCH/>now-30/MEAN_MOTION/>11.25/ECCENTRICITY/<0.25"
REQ_GP_LEO_LARGE   = "/class/gp/RCS_SIZE/large/EPOCH/>now-30/MEAN_MOTION/>11.25/ECCENTRICITY/<0.25"


class MyError(Exception):
    """Class to capture and report errors with api requests"""
    def __init___(self,args):
        Exception.__init__(self,f"Exception was raised with arguments {args}")
        self.args = args


class API():
    """
    Contains functionalities for fetching and saving Space-Track and DISCOSweb data

    Attributes:
        - data_dict (dict of dicts): NORAD catalog ID are keys
    
    Methods:
        - from_list_now: fetch and save only most recent data for a list of id's
        - from_list_hist: fetch and save history of orbit data for a list of id's
        - from_leo_all: fetch and save only most recent data for all leo objects
        - from_leo_large: fetch most recent data for all leo objects >1m^2 radar cross section
        - json_dump: save data dictionary attribute to .json file for future access
        - __spacetrack_api: pseudo-private method to execute space-track api call
        - __discosweb_api: pseudo-private method to execute discosweb api call
    """

    def __init__(self, auth_file) -> None:
        """
        Initialize by setting up attributes and getting authentication data

        Accepts:
            - auth_file (str): file name of .ini file containing auth data

        Returns:
            - N/A
        """
        # Initialize empty dict to eventually store fetched data
        self.data_dict = {}
        # Create some useful header comment data
        self.data_dict["__header"] = {}
        self.data_dict["__header"]["description"] = \
            "Orbit and Object Data from Space-Track and DISCOSweb"
        self.data_dict["__header"]["source"] = {
            "Space-Track": "https://www.space-track.org/auth/login",
            "DISCOSweb": "https://discosweb.esoc.esa.int/apidocs/v2"
        }
        self.data_dict["__header"]["timestamp"] = f"{datetime.now()}"

        # Read and save DISCOweb auth token and Space-Track Username/Password
        config = configparser.ConfigParser()
        config.read(auth_file)
        self.dw_auth = config.get("configuration","discoweb_auth_token")
        config_usr = config.get("configuration","spacetrack_username")
        config_pwd = config.get("configuration","spacetrack_password")
        self.st_auth = {'identity': config_usr, 'password': config_pwd}


    def from_list_now(self, satno_list):
        """
        Fetches spacetrack gp history and discoweb data for a list of sat numbers
        and saves the data to dict attribute

        Accepts:
            - satno_list (list of ints): list of NORAD Catalog ID numbers

        Returns:
            - N/A
        """
        ###############################
        ##  Space-Track API Session  ##
        ###############################
        link_str = ','.join(map(str,satno_list))
        query_str = REQ_GP1 + link_str + REQ_GP2
        st_data = self.__spacetrack_api(query_str)
        # Iterate through space-track data and convert to dictionary
        for obj_dict in st_data:
            norad_id = int(obj_dict["NORAD_CAT_ID"])
            self.data_dict[norad_id] = {}
            self.data_dict[norad_id]["gp_hist"] = [obj_dict]

        #############################
        ##  DISCOSweb API Session  ##
        #############################
        # Break down satno_list into 100-length chunks
        split_satnos = [satno_list[i:i + 100] for i in range(0, len(satno_list), 100)]
        print("Fetching DISCOSweb data for list:")
        with alive_bar(int(len(split_satnos))) as prog_bar:
            for i, satnos in enumerate(split_satnos):
                dw_data = self.__discosweb_api(satnos)
                # Iterate through discoweb data and add to dictionary
                for obj_dict in dw_data:
                    norad_id = obj_dict["attributes"]["satno"]
                    self.data_dict[norad_id].update(obj_dict["attributes"])
                # If we are on our second API call, start throttling call rate
                if i > 0:
                    time.sleep(30)
                prog_bar() # pylint: disable=not-callable


    def from_list_hist(self, satno_list, gp_hist):
        """
        Fetches spacetrack gp history and discoweb data for a list of sat numbers
        and saves the data to dict attribute

        Accepts:
            - satno_list (list of ints): list of NORAD Catalog ID numbers
            - tle_hist (int): number of tle entries to go back

        Returns:
            - N/A
        """
        ###############################
        ##  Space-Track API Session  ##
        ###############################
        print("Fetching Space-Track gp history data for list:")
        with alive_bar(int(len(satno_list))) as prog_bar:
            for i, satno in enumerate(satno_list):
                query_str = REQ_GP_HIST1 + str(satno) + REQ_GP_HIST2 + str(gp_hist) + REQ_GP_HIST3
                obj_dict = self.__spacetrack_api(query_str)
                norad_id = int(obj_dict[0]["NORAD_CAT_ID"])
                self.data_dict[norad_id] = {}
                self.data_dict[norad_id]["gp_hist"] = obj_dict
                # If we are on our second API call, start throttling call rate
                if i > 0:
                    time.sleep(30)
                prog_bar() # pylint: disable=not-callable

        #############################
        ##  DISCOSweb API Session  ##
        #############################
        # Break down satno_list into 100-length chunks
        split_satnos = [satno_list[i:i + 100] for i in range(0, len(satno_list), 100)]
        print("Fetching DISCOSweb data for list:")
        with alive_bar(int(len(split_satnos))) as prog_bar:
            for i, satnos in enumerate(split_satnos):
                dw_data = self.__discosweb_api(satnos)
                # Iterate through discoweb data and add to dictionary
                for obj_dict in dw_data:
                    norad_id = obj_dict["attributes"]["satno"]
                    self.data_dict[norad_id].update(obj_dict["attributes"])
                # If we are on our second API call, start throttling call rate
                if i > 0:
                    time.sleep(30)
                prog_bar() # pylint: disable=not-callable


    def from_leo_all(self):
        """
        Fetches the most recent spacetrack data and discoweb data
        for all objects in LEO and saves data to attribute

        Accepts:
            - N/A

        Returns:
            - N/A
        """
        ###############################
        ##  Space-Track API Session  ##
        ###############################
        st_data = self.__spacetrack_api(REQ_GP_LEO)
        satno_list = []
        # Iterate through space-track data and convert to dictionary
        for obj_dict in st_data:
            norad_id = int(obj_dict["NORAD_CAT_ID"])
            self.data_dict[norad_id] = {}
            self.data_dict[norad_id]["gp_hist"] = [obj_dict]
            satno_list.append(norad_id)

        #############################
        ##  DISCOSweb API Session  ##
        #############################
        # Break down satno_list into 100-length chunks
        split_satnos = [satno_list[i:i + 100] for i in range(0, len(satno_list), 100)]
        print("Fetching DISCOSweb data for full leo environment:")
        with alive_bar(int(len(split_satnos))) as prog_bar:
            for i, satnos in enumerate(split_satnos):
                dw_data = self.__discosweb_api(satnos)
                # Iterate through discoweb data and add to dictionary
                for obj_dict in dw_data:
                    norad_id = obj_dict["attributes"]["satno"]
                    self.data_dict[norad_id].update(obj_dict["attributes"])
                # If we are on our second API call, start throttling call rate
                if i > 0:
                    time.sleep(30)
                prog_bar() # pylint: disable=not-callable


    def from_leo_large(self):
        """
        Fetches the most recent spacetrack data and discoweb data
        for objects in LEO with radar cross section >1m^2 and saves data

        Accepts:
            - N/A

        Returns:
            - N/A
        """
        ###############################
        ##  Space-Track API Session  ##
        ###############################
        st_data = self.__spacetrack_api(REQ_GP_LEO_LARGE)
        satno_list = []
        # Iterate through space-track data and convert to dictionary
        for obj_dict in st_data:
            norad_id = int(obj_dict["NORAD_CAT_ID"])
            self.data_dict[norad_id] = {}
            self.data_dict[norad_id]["gp_hist"] = [obj_dict]
            satno_list.append(norad_id)

        #############################
        ##  DISCOSweb API Session  ##
        #############################
        # Break down satno_list into 100-length chunks
        split_satnos = [satno_list[i:i + 100] for i in range(0, len(satno_list), 100)]
        print("Fetching DISCOSweb data for leo objects with RCS >1m^2:")
        with alive_bar(int(len(split_satnos))) as prog_bar:
            for i, satnos in enumerate(split_satnos):
                dw_data = self.__discosweb_api(satnos)
                # Iterate through discoweb data and add to dictionary
                for obj_dict in dw_data:
                    norad_id = obj_dict["attributes"]["satno"]
                    self.data_dict[norad_id].update(obj_dict["attributes"])
                # If we are on our second API call, start throttling call rate
                if i > 0:
                    time.sleep(30)
                prog_bar() # pylint: disable=not-callable


    def json_dump(self, file_name):
        """
        Dump data attribute to json file

        Accepts:
            - file_name (str): string of name of file to dump to

        Returns:
            - N/A
        """
        with open(f'{file_name}.json', 'w+', encoding="utf-8") as outfile:
            print(json.dumps(self.data_dict, indent=4), file=outfile)


    def __spacetrack_api(self, query_str):
        """Private method for spacetrack API"""
        with requests.Session() as session:
            # need to log in first (200 resp code only means the website got the auth data)
            resp = session.post(URLBASE_ST + REQ_LOGIN, data = self.st_auth)
            if resp.status_code != 200:
                raise MyError(resp, "POST fail on Space-Track login")

            # Make the actual gp data request based on LEO definition
            resp = session.get(URLBASE_ST + REQ_QUERY + query_str)
            if resp.status_code != 200:
                print(resp)
                raise MyError(resp, "GET fail on Space-Track request for gp")

            # Load response as json (dict)
            data = json.loads(resp.text)

        return data


    def __discosweb_api(self, satno_list):
        """Private method for DISCOweb API"""
        # Convert list of sat nums to string
        link_str = ','.join(map(str,satno_list))
        with requests.Session() as session:
            resp = session.get(
                URLBASE_DW,
                headers={
                    'Authorization': f'Bearer {self.dw_auth}',
                    'DiscosWeb-Api-Version': '2',
                },
                params={
                    'filter': f'in(satno,({link_str}))',
                    'page[size]': len(satno_list)
                },
                timeout=60,
                verify=False
            )

            if resp.status_code != 200:
                print(resp)
                raise MyError(resp, "GET fail on DISCOweb request for objects")

            # Load response as json (dict)
            data = resp.json()

        return data["data"]
