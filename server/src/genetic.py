from typing import Tuple, Callable, TypeVar, Any, Union, Dict
from coinbase_websocket_client import CoinbaseWebsocketClient, PriceInfo
from registries import TradingModelRegistry, TradingRecordRegistry
from functools import partial
import time
import trading_record
from trading_record import TradingRecord
from pyrsistent import PRecord, field, pvector, pvector_field
import maybe

TradingModel = TypeVar('Model')
Number = Union[float, int]
TrainableProperties = Dict[str, Number]


class GeneticModel(PRecord):
    construct_trading_model: field(type=Callable[TrainableProperties, TradingModel], mandatory=True)
    trade: field(type=Callable[[TradingRecord, TradingModel, PriceInfo], None], mandatory=True)
    trainable_properties: field(type=TrainableProperties, mandatory=True)
    generation_size = field(type=int, mandatory=True)


# TODO: lock access to registries with mutex
def start(
    coinbase_websocket_client: CoinbaseWebsocketClient,
    registries: Tuple[TradingRecordRegistry, TradingModelRegistry],
    genetic_model: GeneticModel,
) -> None:
    trading_record_registry, trading_model_registry = registries
    # trading_records = {}
    generation = 0
    execute_trades = []

    for i in range(0, genetic_model.generation_size):
        label = f'genetic-{generation}-{i}'
        constants = genetic_model.trainable_properties
        model = genetic_model.construct_trading_model(constants)
        record = trading_record.construct(
            label,
            '(insert genetic algorithm description)',
            100000.0
        )
        trading_record_registry[label] = record
        trading_model_registry[label] = model

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

    selected = {}
    generation_filter_size = genetic_model.generation_size / 2
    min_profit = None
    min_profit_label = None

    coinbase_websocket_client.close()

    # select models with the most profit
    for label, record in trading_record_registry.items():
        # TODO: refactor out this if statement with list comprehension
        if 'genetic' in label:
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
                selected[label] = record
            # otherwise, only push record if profit is greater than the minimum profit
            # of selected records
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
                    selected[label] = record


    return None
