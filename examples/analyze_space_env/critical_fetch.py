"""Fetch orbital history data for top 100 CSI objects"""
from adr_toolbox.api import API
from adr_toolbox.util import load_data


top_100 = load_data("top_100_CSI_scored_debris")

# Create list of the NORAD Catalog ID's for top 100 objects
satnos = []
for satno in top_100.sat_dict.keys():
    satnos.append(satno)

# Get and save hist data for top 100 scored LEO objects
top_100_data = API("auth.ini")
top_100_data.from_list_hist(satnos, 500)
top_100_data.json_dump("top_100_hist")
