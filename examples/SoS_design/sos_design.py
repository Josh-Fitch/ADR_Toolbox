"""Case Study 1 -- Optimize ADR SoS from Scratch"""
from adr_toolbox.api import API

full_leo_pop = API("auth.ini")
full_leo_pop.from_leo()


"""
1. create api obj for scoring debris
2. call api method for getting all leo objects current data
3. create space_env obj from leo objects
4. call space_env method for scoring leo objects using CSI index
5. Take the x top scored debris
6. Create new api obj to get full data for each of the top x debris
7. call api method to get history data for the top x debris
8. create space_env obj from the top x debris

"""
