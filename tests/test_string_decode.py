"""Testing string decoding for genetic algorithm"""

num_vehicles = 9
ind = [1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8]

# Define list of indices where to break up string
breaks = [0] + ind[-(num_vehicles-1):] + [-(num_vehicles-1)]
print(breaks)

# Divide up string into sub-routes for each vehicle
routes = [ind[breaks[i]:breaks[i+1]] for i in range(len(breaks)-1)]
print(routes)
