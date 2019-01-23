import random
from datetime import datetime
from typing import Tuple

import cbpro
import tensorflow as tf
from pyrsistent import PRecord, field

import algorithmic_model
import maybe
import q_learning_model
import result
import trading_record
from logger import logger
from maybe import Maybe
from q_records import QModelInput
from trading_record import TradingAction


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
    def on_open(self):
        self.url = "wss://ws-feed.pro.coinbase.com/"
        self.products = ["BTC-USD"]
        self.message_count = 0
        self.time_delta = 0  # TODO: Turn into real time delta

        q_learning_description = (
            'Uses reinforcement learning to make trading decisions.  Neural network is used \n'
            'predict future rewards for buying, selling, or holding assets.  Once a trading \n'
            'decision is made, the real reward is calculated and used to train the neural \n'
            'network.  Uses epsilon greedy algorithm to explore many different trading \n'
            'strategies by initially making random predictions and then gradually using \n'
            'the neural network more and more over time.'
        )
        self.q_trading_record = trading_record.construct(
            'Q Learning Trading Record',
            q_learning_description,
            100000.0
        )
        session = tf.Session()
        self.q_model = q_learning_model.construct(session)

        # TODO: Rename "Algorithmic" to something else
        algorithmic_description = (
            'Uses an algorithmic approach that looks at moving average and rate of change to \n'
            'make trading decisions.  Once an asset is purchased it is put into a queue of \n'
            'pending sales.  Pending sales are sold when current exchange rate rises \n'
            'or when current exchange rate drops to cut losses.'
        )
        self.a_trading_record = trading_record.construct(
            'Algorithmic Trading Record',
            algorithmic_description,
            100000.0
        )
        self.a_model = algorithmic_model.construct(
            selling_threshold=0.02,
            cut_losses_threshold=-0.05
        )

        random_description = (
            'Makes trading decisions randomly.  Used as baseline to judge the \n'
            'effectiveness of other trading strategies.'
        )
        self.r_trading_record = trading_record.construct(
            'Random Trading Record',
            random_description,
            100000.0
        )

    def q_learning_trade(self, price_info: PriceInfo) -> None:
        record = trading_record.update_exchange_rate(price_info, self.q_trading_record)
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
            self.q_model,
            self.time_delta
        )

        finished_order = trading_record.place_order(action, record)
        self.q_trading_record = result.with_default(self.q_trading_record, finished_order)

        reward = q_learning_model.calculate_reward(record, self.q_trading_record)

        self.q_model = q_learning_model.add_training_sample(
            neural_network_input=q_model_input,
            neural_network_prediction=action,
            reward=reward,
            model=self.q_model
        )

        # Train model every 15 time delta cycles
        if ((self.time_delta + 1) % 15 == 0):
            q_learning_model.train(self.q_model)

        trading_record.statistics(self.q_trading_record)
        self.time_delta += 1

    def algorithmic_trade(self, price_info: PriceInfo) -> None:
        record = trading_record.update_exchange_rate(price_info, self.a_trading_record)
        action, self.a_model = algorithmic_model.predict(
            record,
            self.a_model
        )

        finished_order = trading_record.place_order(action, record)
        self.a_trading_record = result.with_default(self.a_trading_record, finished_order)

        trading_record.statistics(self.a_trading_record)
        algorithmic_model.statistics(self.a_model)

    def random_trade(self, price_info: PriceInfo) -> None:
        record = trading_record.update_exchange_rate(price_info, self.r_trading_record)
        action = predict_random()

        finished_order = trading_record.place_order(action, record)
        self.r_trading_record = result.with_default(self.r_trading_record, finished_order)

        trading_record.statistics(self.r_trading_record)

    def on_message(self, message: CoinbaseMessage):
        self.message_count += 1
        maybe.map_all([self.algorithmic_trade, self.random_trade], parse_message(message))

    def on_close(self):
        logger.log("-- Goodbye! --")


ws_client = CoinbaseWebsocketClient()
ws_client.start()

logger.log(f'{ws_client.url} {ws_client.products}')

# while (ws_client.message_count < 100000):
# while (True):
# logger.log ("\nmessage_count =", "{} \n".format(ws_client.message_count))
# time.sleep(1)

# ws_client.close()
