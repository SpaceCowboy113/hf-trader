import random
from datetime import datetime
from typing import Tuple, Union

import cbpro
from pyrsistent import PRecord, field

import algorithmic_model
import maybe
import q_learning_model
import result
import trading_record
from logger import logger
from maybe import Maybe
from q_records import QModelInput
from trading_record import TradingAction, TradingRecord
from registries import TradingRecordRegistry, TradingModelRegistry


class CoinbaseMessage(PRecord):
    price = field(type=str)
    type = field(type=str)
    time = field(type=str)


def predict_random() -> TradingAction:
    """ Returns a random trading action.
    buy 25%, sell 25%, and hold 50% of the time
    """
    prediction = random.randint(0, 3)
    amount = random.uniform(0.0, 1.0)
    if prediction == 0:
        return TradingAction(order='buy', amount=amount)
    elif prediction == 1:
        return TradingAction(order='sell', amount=amount)
    return TradingAction(order='hold', amount=0)

# Returns epoch (as a float in seconds) from zulu formatted date string
# (zulu date strings are given by coinbase)

# TODO: consolidate this function (duplicated in trading_record)
def get_epoch(zulu_date: str) -> float:
    return datetime.strptime(zulu_date, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()


PriceInfo = Tuple[float, float]


def parse_message(msg: CoinbaseMessage) -> Maybe[PriceInfo]:
    has_price_changed = (
        'price' in msg and
        'time' in msg and
        msg['type'] == 'match'
    )
    if has_price_changed:
        exchange_rate = float(msg['price'])
        epoch = get_epoch(msg['time'])

        return exchange_rate, epoch
    return None


class CoinbaseWebsocketClient(cbpro.WebsocketClient):
    def __init__(
            self,
            trading_record_registry: TradingRecordRegistry,
            trading_model_registry: TradingModelRegistry
    ):
        super().__init__()
        self.trading_record_registry = trading_record_registry
        self.trading_model_registry = trading_model_registry

    def on_open(self):
        self.url = "wss://ws-feed.pro.coinbase.com/"
        self.products = ["BTC-USD"]
        self.message_count = 0
        self.time_delta = 0  # TODO: Turn into real time delta

    def q_learning_trade(self, price_info: PriceInfo) -> None:
        record = trading_record.update_exchange_rate(
            price_info,
            self.trading_record_registry['q-learning']
        )
        # TODO: Modify these functions to no longer use default values
        exchange_rate = maybe.with_default(0.0, trading_record.get_exchange_rate(record))
        rate_of_change = maybe.with_default(0.0, trading_record.get_rate_of_change(record))
        moving_average = maybe.with_default(0.0, trading_record.get_moving_average(record))

        q_model_input = QModelInput(
            exchange_rate=exchange_rate,
            rate_of_change=rate_of_change,
            moving_average=moving_average
        )

        action = q_learning_model.predict_greedy_epsilon(
            q_model_input,
            self.trading_model_registry['q-learning'],
            self.time_delta
        )

        finished_order = trading_record.place_order(action, record)
        self.trading_record_registry['q-learning'] = result.with_default(
            self.trading_record_registry['q-learning'],
            finished_order
        )

        reward = q_learning_model.calculate_reward(
            record, self.trading_record_registry['q-learning']
        )

        self.trading_model_registry['q-learning'] = q_learning_model.add_training_sample(
            neural_network_input=q_model_input,
            neural_network_prediction=action,
            reward=reward,
            model=self.trading_model_registry['q-learning']
        )

        # Train model every 15 time delta cycles
        if ((self.time_delta + 1) % 15 == 0):
            logger.log('training q-learning model...')
            q_learning_model.train(self.trading_model_registry['q-learning'])

        trading_record.statistics(self.trading_record_registry['q-learning'])
        self.time_delta += 1

    def algorithmic_trade(self, price_info: PriceInfo) -> None:
        record = trading_record.update_exchange_rate(
            price_info,
            self.trading_record_registry['algorithmic']
        )
        action, self.trading_model_registry['algorithmic'] = algorithmic_model.predict(
            record,
            self.trading_model_registry['algorithmic']
        )

        finished_order = trading_record.place_order(action, record)
        self.trading_record_registry['algorithmic'] = result.with_default(
            self.trading_record_registry['algorithmic'],
            finished_order
        )

        trading_record.statistics(self.trading_record_registry['algorithmic'])
        algorithmic_model.statistics(self.trading_model_registry['algorithmic'])

    def random_trade(self, price_info: PriceInfo) -> None:
        record = trading_record.update_exchange_rate(
            price_info,
            self.trading_record_registry['random']
        )
        action = predict_random()

        finished_order = trading_record.place_order(action, record)
        self.trading_record_registry['random'] = result.with_default(
            self.trading_record_registry['random'],
            finished_order
        )

        trading_record.statistics(self.trading_record_registry['random'])

    def on_message(self, message: CoinbaseMessage):
        self.message_count += 1
        maybe.map_all(
            [self.algorithmic_trade, self.random_trade, self.q_learning_trade],
            parse_message(message)
        )

    def on_close(self):
        logger.log("-- Goodbye! --")
