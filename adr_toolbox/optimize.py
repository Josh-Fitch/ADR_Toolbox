"""Container for adr_toolbox Optimize class definitions"""
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

class Optimize():
    """Need docstring"""
    def __init__(self) -> None:
        """Need docstring"""

    def ga_setup(
        self,
        weights,
        num_genes,
        architecture,
        pop_size,
        fitness_func,
        mutation_prob,
        tourney_size
    ):
        """ 
        Function to capture basic GA setup functionality

        Accepts:
            - weights [list of ints] = optimization objective weighting
            - num_genes [int] = number of bit genes for each individual
            - fitness_func [object handler] = fitness function to be evaluated
            - mutation_prob [float] = 0 to 1 for probability of bit flip (mutation)
            - tourney_size [int] = Number of individuals pitted against each other each generation

        Returns:
            - toolbox object containing DEAP functionality
        """
        random.seed(64)
        #----------
        # Create problem and toolbox
        #----------
        creator.create("FitnessMax", base.Fitness, weights=weights)
        creator.create("Individual", list, fitness=creator.FitnessMax) # pylint: disable=no-member
        toolbox = base.Toolbox()

        #----------
        # Register individuals, population, and randomization of first generation
        #----------
        # Attribute generator
        #                      define 'attr_bool' to be an attribute ('gene')
        #                      which corresponds to integers sampled uniformly
        #                      from the range [0,1] (i.e. 0 or 1 with equal
        #                      probability)
        toolbox.register("attr_bool", random.randint, 0, 1)

        # Structure initializers
        #                         define 'individual' to be an individual
        #                         consisting of 100 'attr_bool' elements ('genes')
        toolbox.register("individual", tools.initRepeat, creator.Individual, # pylint: disable=no-member
            toolbox.attr_bool, int(num_genes)) # pylint: disable=no-member

        # define the population to be a list of individuals
        toolbox.register("population", tools.initRepeat, list, toolbox.individual) # pylint: disable=no-member

        #----------
        # Operator registration of fitness, mating, mutation, and selection functions
        #----------
        # register the goal / fitness function
        toolbox.register("evaluate", fitness_func, architecture=architecture)

        # register the crossover operator
        toolbox.register("mate", tools.cxTwoPoint)

        # register a mutation operator with a probability to
        # flip each attribute/gene of 0.05
        toolbox.register("mutate", tools.mutFlipBit, indpb=mutation_prob)

        # operator for selecting individuals for breeding the next
        # generation: each individual of the current generation
        # is replaced by the 'fittest' (best) of three individuals
        # drawn randomly from the current generation.
        toolbox.register("select", tools.selTournament, tournsize=tourney_size)

        # create an initial population of X individuals (where
        # each individual is a list of integers)
        pop = toolbox.population(n=pop_size) # pylint: disable=no-member

        return toolbox, pop


    def run_optimization(self, toolbox, pop, num_gens, cross_prob, mutate_prob):
        """Function to iterate through generations"""

        # Evaluate the entire population
        fitnesses = list(map(toolbox.evaluate, pop))
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit

        # Variable keeping track of the number of generations
        gen_iter = 0

        # Begin the evolution
        while gen_iter < num_gens:
            # A new generation
            gen_iter = gen_iter + 1

            # Select the next generation individuals
            offspring = toolbox.select(pop, len(pop))
            # Clone the selected individuals
            offspring = list(map(toolbox.clone, offspring))

            # Apply crossover and mutation on the offspring
            for child1, child2 in zip(offspring[::2], offspring[1::2]):

                # cross two individuals with probability cross_prob
                if random.random() < cross_prob:
                    toolbox.mate(child1, child2)

                    # delete fitness values of the children, recalculated later
                    del child1.fitness.values
                    del child2.fitness.values

            for mutant in offspring:
                # mutate an individual with probability mutate_prob
                if random.random() < mutate_prob:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values

            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            # The population is entirely replaced by the offspring
            pop[:] = offspring

        return pop, gen_iter
