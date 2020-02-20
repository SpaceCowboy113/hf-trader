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

TradingModel = TypeVar('Model')
Number = Union[float, int]
TrainableProperties = Dict[str, Number]
Organism = Tuple[TrainableProperties, TradingRecord, Any]
Population = Dict[str, Organism]


class GeneticModel(PRecord):
    construct_trading_model: field(type=Any, mandatory=True)
    # construct_trading_model: field(type=Callable[TrainableProperties, TradingModel], mandatory=True)
    trade: field(type=Callable[[TradingRecord, TradingModel, PriceInfo], None], mandatory=True)
    trainable_properties: field(type=TrainableProperties, mandatory=True)
    generation_size = field(type=int, mandatory=True)

# def construct() -> GeneticModel:
#     return GeneticModel(
#         generation_size = 10,
#     )

# TODO: lock access to registries with mutex


def start(
    coinbase_websocket_client: CoinbaseWebsocketClient,
    registries: Tuple[TradingRecordRegistry, TradingModelRegistry],
    genetic_model: GeneticModel,
) -> None:
    trading_record_registry, trading_model_registry = registries
    # trading_records = {}
    generation = 0
    # trainables_map = {}
    # TODO: Create dict containing label -> trainable constants, record, model

    # initialize population
    population = {}
    for i in range(0, genetic_model.generation_size):
        label = f'genetic-INITIAL-{i}'

        # TODO: Assign constants from previous generation
        constants = genetic_model.trainable_properties
        # trainables_map[label] = constants
        model = genetic_model.construct_trading_model(constants)
        record = trading_record.construct(
            label,
            '(insert genetic algorithm description)',
            100000.0
        )
        population[label] = (constants, record, model)
        trading_record_registry[label] = record
        trading_model_registry[label] = model

    for generation in range(0, 10):

        # --execution
        execute_trades = []
        for label, organism in population.items():
            constants, record, model = organism
            partial_trade = partial(
                genetic_model.trade,
                record,
                model
            )
            execute_trades.push(partial_trade)

        coinbase_websocket_client = CoinbaseWebsocketClient(execute_trades)
        coinbase_websocket_client.start()

        # sleep for five minutes
        time.sleep(60 * 5)
        coinbase_websocket_client.close()
        # --execution finished

        fittest = select_fittest(
            population,
            genetic_model,
        )
        # Reassign label down here
        children = crossover(fittest, genetic_model)

        population = mutate(children)


def select_fittest(
    population: Population,
    genetic_model: GeneticModel,
) -> Population:
    selected = {}
    generation_filter_size = genetic_model.generation_size / 2
    min_profit = None
    min_profit_label = None

    # select models with the most profit
    for label, organism in population.items():
        trainable_properties, record, model = organism
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
            selected[label] = (trainable_properties, record, model)

        # otherwise, only push record if profit is greater than the minimum profit of selected records
        else:
            if profit > min_profit:
                # Remove old minimum record and select new min_profit_record
                selected.pop(min_profit_label, None)
                min_profit_label = min(
                    selected.iterkeys(),
                    key=(lambda label: trading_record.calculate_profit(selected[label]))
                )
                min_profit = trading_record.calculate_profit(selected[min_profit_label])

                # Finally, once min_profit_record is updated, add new record to selection
                selected[label] = (trainable_properties, record, model)

    return selected


def crossover(
    population: Population,
    genetic_model: GeneticModel,
) -> Population:
    next_generation = {}
    for label, organism in population.items():
        trainable_properties, _, _ = organism
        # organism creates two similar children base on itself
        # TODO: Implement mother and father

        # TODO: create a better label, this is just temporary
        first_child_label = f'{label}+'
        first_child = generate_single_parent_child(
            first_child_label,
            trainable_properties,
            genetic_model
        )
        next_generation[first_child_label] = first_child

        second_child_label = f'{label}-'
        second_child = generate_single_parent_child(
            second_child_label,
            trainable_properties,
            genetic_model
        )
        next_generation[second_child_label] = second_child

    return next_generation


def generate_single_parent_child(
    child_label,
    parent_properties: TrainableProperties,
    genetic_model: GeneticModel,
):
    child_properties = generate_trainable_properties(parent_properties)

    model = genetic_model.construct_trading_model(
        generate_trainable_properties(parent_properties)
    )
    record = trading_record.construct(
        child_label,
        '(insert genetic algorithm description)',
        100000.0
    )
    return child_properties, record, model


def generate_trainable_properties(
    properties: TrainableProperties
) -> TrainableProperties:
    new_properties = {}
    for name, value in properties.items():
        should_add = bool(random.getrandbits(1))
        if should_add:
            new_properties[name] = properties[name] + properties[name] / random.randint(80, 120)
        else:
            new_properties[name] = properties[name] - properties[name] / random.randint(80, 120)
    return new_properties


def mutate(
    population: Population,
) -> Population:
    return population
