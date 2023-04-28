"""Test of Genetic Algorithm Optimize Class"""
import numpy as np
import matplotlib.pyplot as plt
import scienceplots # pylint: disable=unused-import
from alive_progress import alive_bar
from adr_toolbox.optimize import VehicleRouting
plt.style.use('science')
plt.rcParams.update({'font.size': 14})

class Data:
    """Test data object"""
    def __init__(self) -> None:
        self.func_eval_tally = 0

    def fitness_func(self, individual):
        """Calculate fitness"""
        self.func_eval_tally += 1

        # If route without zeroes not unique, return zero fitness score
        if len(set(individual)) != len(individual):
            return (100,)

        fitness = 0
        for index in range(len(individual) - 1):
            fitness += np.abs(individual[index] - individual[index+1])

        # Must return a tuple form
        return (fitness,)


def optimize_params():
    """ Find optimal GA parameters """
    # Initialize data storage object
    data_obj = Data()

    optimizer = VehicleRouting(
        data_obj.fitness_func, 10, 3, num_gens=20, pop_size=500, weights=(-1,),
        bit_mutate_prob=0, ind_mutate_prob=0, cross_prob=0
    )

    bit_mutate = np.linspace(0, 0.8, 11)
    ind_mutate = np.linspace(0, 0.8, 11)
    cross_prob = np.linspace(0, 0.8, 11)
    size = len(bit_mutate) * len(ind_mutate) * len(cross_prob)
    best_func_tally = 1e10
    with alive_bar(size) as prog_bar:
        for i in bit_mutate:
            for j in ind_mutate:
                for k in cross_prob:
                    optimizer.bit_mutate_prob = i
                    optimizer.ind_mutate_prob = j
                    optimizer.cross_prob = k
                    perfs = []
                    func_tallys = []
                    for _ in range(50):
                        optimizer.optimize()
                        perfs.append(optimizer.best_performance)
                        func_tallys.append(data_obj.func_eval_tally)
                    print(np.mean(perfs))
                    print(np.mean(func_tallys))
                    if np.mean(perfs) == 12 and np.mean(func_tallys) < best_func_tally:
                        best_func_tally = np.mean(func_tallys)
                        best_bit_mutate = i
                        best_ind_mutate = j
                        best_cross_prob = k
                    prog_bar() # pylint: disable=not-callable
    print(f"Best Func Tally %: {best_func_tally / 6.23e9 * 100}")
    print(f"Best Ind Mutate Prob: {best_bit_mutate}")
    print(f"Best Bit Mutate Prob: {best_ind_mutate}")
    print(f"Best Cross Prob: {best_cross_prob}")


def decode_routing(ind, num_vehicles):
    """
    Take a string of routing indexes and split indices and 
    break up into distinct routes for each vehicle

    Accepts:
        - ind (list of ints): individual from GA, list of integers
        - num_vehicles (int): number of vehicles and therefore routes

    Returns:
        - routes (list of lists of ints): breakdown of distinct routes
    """
    # Get integers representing start of each vehicles route
    start_ints = [x for x in range(num_vehicles)]

    print(f"Individual:                 {ind}")

    # Shift list to start at 0
    ind_shift = ind[ind.index(0):] + ind[:ind.index(0)]
    print(f"Individual Shifted:         {ind_shift}")

    # Get the indices of the starting integers
    start_inds = []
    for i, integer in enumerate(ind_shift):
        if integer in start_ints:
            start_inds.append(i)

    # Split into distinct routes
    routes = [ind_shift[i:j] for i,j in zip(start_inds, start_inds[1:]+[None])]
    print(f"Split Individual:           {routes}")

    # Sort lists by vehicle index
    routes_sorted = sorted(routes, key=lambda x: x[0])
    print(f"Sorted Split Individual:    {routes_sorted}")

    # Shift values in each route by number of vehicles
    routes_shift = []
    for route in routes_sorted:
        routes_shift.append([x-num_vehicles for x in route[1:]])
    print(f"Index-Formed Individual:    {routes_shift}")

    return routes_shift


def test_params():
    # Initialize data storage object
    data_obj = Data()

    optimizer = VehicleRouting(
        data_obj.fitness_func, 10, 3, num_gens=30, pop_size=500, weights=(-1,),
        bit_mutate_prob=0.1, ind_mutate_prob=0.3, cross_prob=0.5
    )
    optimizer.optimize()

    # It would take 1,814,400 (10! / 2) permutations to
    # find one of the two optimal ordered lists without
    # replacement that minimizes the sum of the absolute
    # difference between each integer
    best_ind = [12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    best_perf = data_obj.fitness_func(best_ind)[0]
    print(f"Predicted best: {best_perf}")
    print(data_obj.func_eval_tally)

    gen, avg, min_fit = optimizer.logbook.select("gen", "avg", "min")
    best = [12 * x for x in np.ones(len(gen))]

    fig = plt.figure()
    ax = plt.axes()
    ax.scatter(gen, avg, label="GA Average", s=80, marker='o')
    ax.scatter(gen, min_fit, label="GA Best", s=40, marker='o')
    ax.plot(gen, best, label="Global Optimal", color='red', linewidth=2)
    plt.title("Genetic Algorithm Benchmark Performance")
    plt.xlabel("Generation")
    plt.ylabel("Fitness")
    plt.legend()
    plt.grid()
    plt.show()

    best_perf = []
    with alive_bar(50) as prog_bar:
        for _ in range(50):
            optimizer.optimize()
            best_perf.append(optimizer.best_performance)
            prog_bar() # pylint: disable=not-callable
    print(np.mean(best_perf))
    print(max(best_perf))


if __name__ == "__main__":
    #optimize_params()
    test_params()

    #ind = [2, 6, 12, 3, 1, 5, 10, 8, 7, 0, 11, 4, 9]
    #num_vehicles = 3
    #routes = decode_routing(ind, num_vehicles)
