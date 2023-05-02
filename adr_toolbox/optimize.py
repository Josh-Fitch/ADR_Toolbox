""" Container for adr_toolbox Optimize class definitions """
###############################################################
##  Implemented by:
##     - Joshua Fitch
##     - Purdue University AAE
##     - January 2023
##     - jfitch007@outlook.com
###############################################################
import random
import numpy as np
from deap import base
from deap import creator
from deap import tools

class VehicleRouting():
    """
    Encapsulates DEAP (Distributed Evolutionary Algorithm for Python)
    functionalities to solve multi-vehicle routing problem

    Attributes:
        - 

    Methods:
        - 
    """
    def __init__(
            self, fit_func, num_targets, num_vehicles, data_obj=None,
            weights=(1,), num_gens=400, pop_size=400, tourney_size=3,
            ind_mutate_prob=0.2, bit_mutate_prob=0.2, cross_prob=0.5
        ) -> None:
        """
        Constructor for Optimize Class

        Accepts:
            - data_obj (object): Object containing all data used in funcs
            - fit_func (func handle): handle to fitness (performance) function
            - ind_size (int): size of bitstring defining an individual
            - weights (tuple): tuple of weights corresponding to n-objective opt. prob.
            - seed (int): rand seed controlling probabilities
            - num_gens (int): number of generations to run genetic algorithm
              default = 200
            - pop_size (int): number of individuals to start with (randomly generated)
              default = 200
            - tourney_size (int): number of individuals that compete for survival during
              each generation
            - ind_mutate_prob (float): probability in range(0, 1) describing liklihood of
              an individual experiencing mutation
              default = 0.2
            - bit_mutate_prob (float): probability in range(0, 1) describing liklihood of
              a bit mutating in an individual that experiences mutation
              default = 0.05
            - cross_prob (float): probability in range(0, 1) describing liklihood of
              two suriving individuals mating and generating a child individual
            
        Returns:
            - Instance of class Optimize
        """
        self.data_obj = data_obj
        self.fit_func = fit_func
        self.ind_size = num_targets + num_vehicles
        self.weights = weights
        self.num_gens = num_gens
        self.pop_size = pop_size
        self.tourney_size = tourney_size
        self.ind_mutate_prob = ind_mutate_prob
        self.bit_mutate_prob = bit_mutate_prob
        self.cross_prob = cross_prob

        # Initialize empty toolbox and population stats
        self.pop = None
        self.hof = None
        self.best_ind = None
        self.best_performance = None
        self.stats = None
        self.toolbox = None
        self.logbook = None


    def optimize(self):
        """ Function to iterate through generations and perform optimization routine """
        # Call general setup methods
        self.__ga_setup()

        # Evaluate the entire population
        fitnesses = list(map(self.toolbox.evaluate, self.pop)) # pylint: disable=no-member
        for ind, fit in zip(self.pop, fitnesses):
            ind.fitness.values = fit

        # Variables keeping track of generations and performances
        gen_iter = 0
        perfs = np.array([])
        # Begin the evolution
        print("Routing Optimization Initialized")
        while True:
            if gen_iter > self.num_gens:
                # Compute percent change in past 5 generations
                perc_imp = abs(np.average(perfs[-5:-1]) - perfs[-1]) * 100 / perfs[-1]
                # Once convergence is less than 1% improvement, stop
                if perc_imp < 1:
                    break

            # A new generation
            gen_iter = gen_iter + 1

            # Select the next generation individuals
            offspring = self.toolbox.select(self.pop, len(self.pop)) # pylint: disable=no-member
            # Clone the selected individuals
            offspring = list(map(self.toolbox.clone, offspring)) # pylint: disable=no-member

            # Apply crossover and mutation on the offspring
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                # cross two individuals with probability cross_prob
                if random.random() < self.cross_prob:
                    self.toolbox.mate(child1, child2) # pylint: disable=no-member

                    # delete fitness values of the children, recalculated later
                    del child1.fitness.values
                    del child2.fitness.values

            for mutant in offspring:
                # mutate an individual with probability mutate_prob
                if random.random() < self.ind_mutate_prob:
                    self.toolbox.mutate(mutant) # pylint: disable=no-member
                    del mutant.fitness.values

            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(self.toolbox.evaluate, invalid_ind) # pylint: disable=no-member
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            # The population is entirely replaced by the offspring
            self.pop[:] = offspring

            # Get and store the best individual for this generation
            best_ind = tools.selBest(self.pop, 1)[0]
            self.hof.insert(best_ind)

            print(f"Generation = {gen_iter} / {self.num_gens} \
                  - Best Perf. = {best_ind.fitness.values[0]}")

            # Log all data
            record = self.stats.compile(self.pop)
            perfs = np.append(perfs, record["avg"])
            self.logbook.record(gen=gen_iter, **record)

        del creator.FitnessMax # pylint: disable=no-member
        del creator.Individual # pylint: disable=no-member


    def __ga_setup(self):
        """ Private method to setup DEAP GA tools """
        # Create problem and toolbox
        self.toolbox = base.Toolbox()
        self.logbook = tools.Logbook()

        # Initialize the problem with weights and max or min
        creator.create("FitnessMax", base.Fitness, weights=self.weights)
        creator.create("Individual", list, fitness=creator.FitnessMax) # pylint: disable=no-member

        # an Individual is a collection of unique indices
        self.toolbox.register(
            "indices", random.sample, range(self.ind_size), self.ind_size
        )
        # an Individual is a collection of unique indices
        self.toolbox.register(
            "individual", tools.initIterate,
            creator.Individual, self.toolbox.indices # pylint: disable=no-member
        )
        # a Population is a collection of Individuals
        self.toolbox.register(
            "population", tools.initRepeat, list, self.toolbox.individual # pylint: disable=no-member
        )

        # register the goal / fitness function
        if self.data_obj is not None:
            self.toolbox.register("evaluate", self.fit_func, data=self.data_obj)
        else:
            self.toolbox.register("evaluate", self.fit_func)

        # register the crossover operator
        self.toolbox.register("mate", tools.cxOrdered)

        # register a mutation operator with a probability for each int
        self.toolbox.register("mutate", tools.mutShuffleIndexes, indpb=self.bit_mutate_prob)

        # operator for selecting individuals for breeding the next
        # generation: each individual of the current generation
        # is replaced by the 'fittest' (best) of three individuals
        # drawn randomly from the current generation.
        self.toolbox.register("select", tools.selTournament, tournsize=self.tourney_size)

        # create an initial population of X individuals (where
        # each individual is a list of integers)
        pop = self.toolbox.population(n=self.pop_size) # pylint: disable=no-member
        self.pop = pop
        self.hof = tools.HallOfFame(1)
        self.__log_stats()


    def __log_stats(self):
        """ Logging of DEAP statistics """
        self.stats = tools.Statistics(key=lambda ind: ind.fitness.values)
        self.stats.register("avg", np.mean)
        self.stats.register("std", np.std)
        self.stats.register("min", np.min)
        self.stats.register("max", np.max)
