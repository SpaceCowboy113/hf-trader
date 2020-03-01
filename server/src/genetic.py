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
# TradingModel = TypeVar('Model')
TradingModel = Any
Number = Union[float, int]
TrainableProperties = Dict[str, Any]
Organism = Tuple[TrainableProperties, TradingRecord, Any]
Population = Dict[str, Organism]


class GeneticModel(PRecord):
    # construct_trading_model = field(type=Number, mandatory=True)
    # construct_trading_model = field(
    construct_trading_model = field(type=types.FunctionType, mandatory=True)
    trade = field(type=types.FunctionType, mandatory=True)
    trainable_properties = field(type=dict, mandatory=True)
    generation_size = field(type=int, mandatory=True)

# def construct() -> GeneticModel:
#     return GeneticModel(
#         generation_size = 10,
#     )

# TODO: lock access to registries with mutex


def start(
    registries: Tuple[TradingRecordRegistry, TradingModelRegistry],
    genetic_model: GeneticModel,
) -> None:
    trading_record_registry, trading_model_registry = registries
    # trading_records = {}
    generation = 0
    # trainables_map = {}
    # TODO: Create dict containing label -> trainable constants, record, model

    # initialize population
    print('1')
    population = {}
    for i in range(0, genetic_model.generation_size):
        label = f'genetic-INITIAL-{i}'

        # TODO: Assign constants from previous generation
        trainables = genetic_model.trainable_properties
        # trainables_map[label] = trainables
        model = genetic_model.construct_trading_model(trainables)
        record = trading_record.construct(
            label,
            '(insert genetic algorithm description)',
            100000.0
        )
        population[label] = (trainables, record, model)
        trading_record_registry[label] = record
        trading_model_registry[label] = model
    print('2')
    for generation in range(0, 10):
        print('executing', generation)
        # --execution
        execute_trades: list = []
        for label, organism in population.items():
            constants, record, model = organism
            # Creates new function, trading_model.trade(price_info)
            partial_trade = partial(
                genetic_model.trade,
                record,
                model
            )
            execute_trades.append(partial_trade)

        coinbase_websocket_client = CoinbaseWebsocketClient(execute_trades)
        logger.log(f'{coinbase_websocket_client.url} {coinbase_websocket_client.products}')
        coinbase_websocket_client.start()

        # sleep for five minutes
        # time.sleep(60 * 5)
        time.sleep(1)
        coinbase_websocket_client.close()
        # --execution finished

        fittest = select_fittest(
            population,
            genetic_model,
        )
        # Reassign label down here
        children: Population = crossover(fittest, genetic_model)

        population = mutate(children)


def select_fittest(
    population: Any,
    genetic_model: Any,
) -> Population:
    print('select fittest')
    selected: dict = {}
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
                    selected.keys(),
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
    print('crossover')
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
    population: Any,
) -> Any:
    return population