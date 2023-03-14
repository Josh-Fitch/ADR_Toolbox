"""Testing debris data fetching api"""
from adr_toolbox.api import API

test = API("auth.ini")
test.from_list_hist([22566, 22220, 31793], 5)
test.json_dump("top_three_debris_data_list")

test2 = API("auth.ini")
test2.from_list_now([22566, 22220, 31793])
test2.json_dump("top_three_debris_data")
