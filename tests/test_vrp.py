"""Test of VRP with arbitary start and end locations"""
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def create_data_model():
    """Stores the data for the problem."""
    data = {}
    data['distance_matrix'] = [
        [0, 0, 0, 0, 0],
        [0, 0, 3, 7, 5],
        [0, 3, 0, 2, 4],
        [0, 7, 2, 0, 1],
        [0, 5, 4, 1, 0],
    ]
    data['num_vehicles'] = 1
    data['depot'] = 0
    return data


def export_routes(data, manager, routing, solution):
    """Exports routes and total costs to dicts"""
    routes = {}
    costs = {}
    for vehicle_id in range(data['num_vehicles']):
        routes[vehicle_id] = []
        index = routing.Start(vehicle_id)
        route_distance = 0
        while True:
            # For arbitrary start/end, ignore depot location
            if index == data['depot']:
                index = solution.Value(routing.NextVar(index))
                continue
            routes[vehicle_id].append(manager.IndexToNode(index))
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
            # Break out of loop once end of route is reached
            if routing.IsEnd(index):
                break
        # Store total route cost
        costs[vehicle_id] = route_distance
    return routes, costs


def main():
    """Entry point of the program."""
    # Instantiate the data problem.
    data = create_data_model()

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint.
    dimension_name = 'Distance'
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        20,  # vehicle maximum travel distance
        True,  # start cumul to zero
        dimension_name)
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC) # pylint: disable=no-member

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        routes, costs = export_routes(data, manager, routing, solution)
        print(routes)
        print(costs)
    else:
        print("No Solution!")


if __name__ == '__main__':
    main()
