"""Fetch orbital history data for top X CSI objects"""
from adr_toolbox.api import API
from adr_toolbox.util import load_data

top_objs = load_data("top_200_CSI_scored_debris")

# Create list of the NORAD Catalog ID's for top objects
satnos = []
for satno, sat in top_objs.sat_dict.items():
    satnos.append(satno)

# Get and save hist data for top X scored LEO objects
top_objs_data = API("auth.ini")
top_objs_data.from_list_hist(satnos[:50], 500)
top_objs_data.json_dump("top_50_hist")
