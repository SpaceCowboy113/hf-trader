from typing import Tuple, Callable, TypeVar, Any, Union, Dict
from coinbase_websocket_client import CoinbaseWebsocketClient, PriceInfo
from registries import TradingModelRegistry, TradingRecordRegistry
from functools import partial
import time
import trading_record
from trading_record import TradingRecord
from pyrsistent import PRecord, field, pvector, pvector_field
import maybe
import random
from logger import logger
import types
import result
# TradingModel = TypeVar('Model')
TradingModel = Any
Number = Union[float, int]
Genes = Dict[str, Any]
Organism = Tuple[Genes, TradingRecord, Any]
Population = Dict[str, Organism]


class GeneticModel(PRecord):
    # construct_trading_model = field(type=Number, mandatory=True)
    # construct_trading_model = field(
    construct_trading_model = field(type=types.FunctionType, mandatory=True)
    trade = field(type=types.FunctionType, mandatory=True)
    genome = field(type=dict, mandatory=True)
    generation_size = field(type=int, mandatory=True)

# def construct() -> GeneticModel:
#     return GeneticModel(
#         generation_size = 10,
#     )

# TODO: lock access to registries with mutex

# def randomize_genes(genes: Genes) -> Genes:
#     randomized_genes = {}
#     # Returns new random propertty values +/- 10% of originals
#     for key, value in genes.items():
#         one_percent = value / 100
#         randomize_genes[key] = (value - one_percent * 10) + (one_percent * random.randint(0, 20)


def randomize_multiple_genes(genes: Any) -> Any:
    randomized_genes = {}
    # Returns new random propertty values +/- 10% of originals
    for name, value in genes.items():
        randomized_genes[name] = randomize_gene(value, 10)
    return randomized_genes


def start(
    registries: Tuple[TradingRecordRegistry, TradingModelRegistry],
    genetic_model: GeneticModel,
) -> None:
    trading_record_registry, trading_model_registry = registries
    population = {}

    # Initialize population before execution
    for i in range(0, genetic_model.generation_size):
        label = f'genetic-G0-{i}'

        genes = genetic_model.genome
        randomized_genes = randomize_multiple_genes(genes)
        model = genetic_model.construct_trading_model(randomized_genes)
        record = trading_record.construct(
            label,
            '(insert genetic algorithm description)',
            100000.0
        )
        population[label] = (randomized_genes, record, model)
        trading_record_registry[label] = record
        trading_model_registry[label] = model

    # Once population is initialized, execute genetic algorithm
    for generation in range(0, 100):
        execute_trades: list = []
        for label, organism in population.items():
            constants, record, model = organism

            # Creates a trade function that takes only price_info as parameter, completing
            # the trade interface required by coinbase_websocket_client
            def trade(price_info: PriceInfo) -> None:
                (genes, record, model) = population[label]
                updated_record = result.with_default(
                    organism[1],
                    genetic_model.trade(record, model, price_info)
                )
                population[label] = (genes, updated_record, model)
            execute_trades.append(trade)

        # Batch of organisms trade over a generation for n seconds
        coinbase_websocket_client = CoinbaseWebsocketClient(execute_trades)
        logger.log(f'{coinbase_websocket_client.url} {coinbase_websocket_client.products}')
        logger.log(f'genetic algorithm trading for generation {generation}')
        coinbase_websocket_client.start()
        log_sleep('executing trades', 30)  # sleeps for 30s and logs each second
        coinbase_websocket_client.close()
        logger.log(f'trading finished for generation {generation}')

        # Selects the top 50% of organisms in the generation (those with the most profit)
        logger.log('selecting fittest individuals')
        fittest = select_fittest(
            population,
            genetic_model,
        )
        print_performance(fittest)
        time.sleep(3)
        logger.log('performing crossover')
        # Fittest organisms reproduce using crossover algorithm.  This doubles the fit population
        children: Population = double_parent_crossover(fittest, genetic_model)

        # Perform random mutations on the children.  This helps prevent the algorithm from getting
        # stuck in locally optimal solutions
        mutated_children = mutate(children)

        # Update population with mutated children
        population = {}
        organism_number = 0
        for label, organism in mutated_children.items():
            (child_genes, _, _) = organism
            next_generation_label = f'genetic-G{generation + 1}-{organism_number}'
            child_model = genetic_model.construct_trading_model(child_genes)
            child_record = trading_record.construct(
                next_generation_label,
                '(insert genetic algorithm description)',
                100000.0
            )
            population[next_generation_label] = (child_genes, child_record, child_model)
            organism_number += 1


def log_sleep(log_message: str, t: int) -> None:
    for i in range(0, t):
        logger.log(f'{log_message}: {i}')
        time.sleep(1)


def print_performance(population: Any) -> None:
    for label, organism in population.items():
        genes, record, model = organism
        print(genes)
        print('------------------------------------------------------')
        print(f'selling_threshold: {genes["selling_threshold"]}')
        print(f'cut_losses_threshold: {genes["cut_losses_threshold"]}')
        print(f'profit: {trading_record.calculate_profit(record)}')
        print(f'USD: {record.usd}')
        print(f'Crypto: {record.crypto}')
        print(f'Buys: {record.buys}')
        print(f'Sells: {record.sells}')
        print(f'Holds: {record.holds}')
        print('------------------------------------------------------')


def select_fittest(
    population: Any,
    genetic_model: Any,
) -> Population:
    selected: dict = {}
    generation_filter_size = genetic_model.generation_size / 2
    min_profit = None
    min_profit_label = None

    # select models with the most profit
    for label, organism in population.items():
        genes, record, model = organism
        profit = trading_record.calculate_profit(record)

        # initialize min_profit for initial run through loop
        min_profit = maybe.with_default(profit, min_profit)
        min_profit_label = maybe.with_default(label, min_profit_label)

        # if less than generation filter size, push record and update
        # minimum profit of selected records if necessary
        if len(selected) < generation_filter_size:
            if profit < min_profit:
                min_profit = profit
                min_profit_label = label
            selected[label] = (genes, record, model)

        # otherwise, only push record if profit is greater than the minimum profit of
        # selected records
        else:
            if profit > min_profit:
                # Remove old minimum record and select new min_profit_record
                selected.pop(min_profit_label, None)
                min_profit_label = min(
                    selected.keys(),
                    key=(lambda label: trading_record.calculate_profit(selected[label][1]))
                )
                min_profit = trading_record.calculate_profit(selected[min_profit_label][1])

                # Finally, once min_profit_record is updated, add new record to selection
                selected[label] = (genes, record, model)

    return selected


# TODO: Create triple parent crossover?
def double_parent_crossover(
    population: Population,
    genetic_model: GeneticModel,
) -> Population:
    print('double parent crossover')
    next_generation: Population = {}

    # Creates a list of tuples from dictionary. ie. [(key, value), ... ]
    population_list = [(label, organism) for label, organism in population.items()]

    for i in range(0, len(population_list)):
        father_tuple = population_list[i]
        father_label = father_tuple[0]
        father_organism = father_tuple[1]
        father_genes, _, _ = father_organism

        # Mother is next organism in list.  If last item in list, mother is first item
        mother_tuple: Any = (None, None)
        if i < len(population_list) - 1:
            mother_tuple = population_list[i + 1]
        else:
            mother_tuple = population_list[0]
        mother_label = mother_tuple[0]
        mother_organism = mother_tuple[1]
        mother_genes, _, _ = mother_organism

        first_child_label = f'F{father_label}-M{mother_label}-C0'
        first_child = generate_double_parent_child(
            first_child_label,
            (mother_genes, father_genes),
            genetic_model
        )
        next_generation[first_child_label] = first_child

        second_child_label = f'F{father_label}-M{mother_label}-C1'
        second_child = generate_double_parent_child(
            second_child_label,
            (mother_genes, father_genes),
            genetic_model
        )
        next_generation[second_child_label] = second_child
    return next_generation


def generate_double_parent_child(
    child_label,
    parent_genes: Tuple[Genes, Genes],
    genetic_model: GeneticModel,
):
    father_genes = parent_genes[0]
    mother_genes = parent_genes[1]

    child_genes = {}
    for gene_name, value in father_genes.items():
        should_select_father = bool(random.getrandbits(1))  # Generates random boolean
        if should_select_father:
            child_genes[gene_name] = father_genes[gene_name]
        else:
            child_genes[gene_name] = mother_genes[gene_name]

    model = genetic_model.construct_trading_model(child_genes)
    record = trading_record.construct(
        child_label,
        '(insert genetic algorithm description)',
        100000.0
    )
    return (child_genes, record, model)


def single_parent_crossover(
    population: Population,
    genetic_model: GeneticModel,
) -> Population:
    print('single parent crossover')
    next_generation = {}
    for label, organism in population.items():
        genes, _, _ = organism
        # organism creates two similar children base on itself
        # TODO: Implement mother and father

        # TODO: create a better label, this is just temporary
        first_child_label = f'{label}-C0'
        first_child = generate_single_parent_child(
            first_child_label,
            genes,
            genetic_model
        )
        next_generation[first_child_label] = first_child

        second_child_label = f'{label}-C1'
        second_child = generate_single_parent_child(
            second_child_label,
            genes,
            genetic_model
        )
        next_generation[second_child_label] = second_child

    return next_generation


def generate_single_parent_child(
    child_label,
    parent_properties: Genes,
    genetic_model: GeneticModel,
):
    child_properties = generate_genome(parent_properties)

    model = genetic_model.construct_trading_model(
        generate_genome(parent_properties)
    )
    record = trading_record.construct(
        child_label,
        '(insert genetic algorithm description)',
        100000.0
    )
    return (child_properties, record, model)


def generate_genome(
    properties: Genes
) -> Genes:
    new_properties = {}
    for name, value in properties.items():
        should_add = bool(random.getrandbits(1))  # Generates random boolean
        if should_add:
            new_properties[name] = properties[name] + properties[name] / random.randint(80, 120)
        else:
            new_properties[name] = properties[name] - properties[name] / random.randint(80, 120)
    return new_properties


def mutate(
    population: Any,
) -> Any:
    mutated_population = {}
    for label, organism in population.items():
        genes, _, _ = organism
        mutated_genes = {}
        for key, value in genes.items():
            should_mutate = random.randint(0, 10)  # 10% chance to mutate
            if should_mutate == 0:
                mutated_value = randomize_gene(value, 50)
                logger.log(f'mutating gene {key} from {value} to {mutated_value}')
                mutated_genes[key] = randomize_gene(value, 10)
            else:
                mutated_genes[key] = value
        mutated_population[label] = organism
    return population


# randomizes gene by +/- percentage
def randomize_gene(gene: Number, percentage: float) -> float:
    one_percent = gene / 100
    return (gene - one_percent * percentage) + (one_percent * random.random() * percentage * 2)
