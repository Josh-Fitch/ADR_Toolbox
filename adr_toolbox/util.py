"""Container for adr_toolbox utility class definitions"""
###############################################################
##  Implemented by:
##     - Joshua Fitch
##     - Purdue University AAE
##     - January 2023
##     - jfitch007@outlook.com
###############################################################
import pickle
import traceback

def load_data(file_name):
    """Load in a data file via pickle"""
    try:
        with open(f"{file_name}.dat", 'rb') as file: # pylint: disable=unspecified-encoding
            data = pickle.load(file)
    except Exception as error:  # pylint: disable=broad-except
        # Catch errors and report failure
        print("\nPickle Load Failed\n")
        print(traceback.format_exc(error))
        data = []
    return data

def save_data(data, file_name):
    """Write data to a file via pickle"""
    try:
        with open(f"{file_name}.dat", "wb") as file:
            pickle.dump(data, file)
    except Exception as error:  # pylint: disable=broad-except
        # Catch errors and report failure
        print("\nPickle Save Failed\n")
        print(traceback.format_exc(error))
