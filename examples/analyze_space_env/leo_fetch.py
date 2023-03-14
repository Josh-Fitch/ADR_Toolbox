"""Get all relevant datasets"""
import time
from adr_toolbox.api import API

# Get and save data for entire catalog of LEO objects
leo_data = API("auth.ini")
leo_data.from_leo_all()
leo_data.json_dump("all_leo_data")

# Take a quick break to not overload api rate limits
time.sleep(300)

# Get and save data for LEO objects with Radar Cross Section >1m^2
leo_large = API("auth.ini")
leo_large.from_leo_large()
leo_large.json_dump("large_leo_data")
