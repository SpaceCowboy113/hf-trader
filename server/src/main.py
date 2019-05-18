import signal
import sys

import tensorflow as tf
from pyrsistent import m

import algorithmic_model
import moving_average_subroutine
import q_learning_model
import mac_algorithm_model
import trading_record
import web_application
from coinbase_websocket_client import CoinbaseWebsocketClient  # noqa: F401
from coinbase_websocket_client import (TradingModelRegistry,
                                       TradingRecordRegistry)
from logger import logger


def close_hf_trader(sig, frame):
    logger.info('closing high-frequency trader')
    coinbase_websocket_client.close()
    sys.exit(0)


trading_record_registry: TradingRecordRegistry = {}

mac_algorithm_description = (
    'Looks for peaks and valleys and makes buy/sell decisions on the \n'
    'upswings and downswings respectively.'
)
trading_record_registry['mac-algorithm'] = trading_record.construct(
    'Moving Average Crossings Trading Record',
    mac_algorithm_description,
    100.0,
    m(little_moving_average=moving_average_subroutine.construct(10),
        big_moving_average=moving_average_subroutine.construct(30))
)

q_learning_description = (
    'Uses reinforcement learning to make trading decisions.  Neural network is used \n'
    'predict future rewards for buying, selling, or holding assets.  Once a trading \n'
    'decision is made, the real reward is calculated and used to train the neural \n'
    'network.  Uses epsilon greedy algorithm to explore many different trading \n'
    'strategies by initially making random predictions and then gradually using \n'
    'the neural network more and more over time.'
)
trading_record_registry['q-learning'] = trading_record.construct(
    'Q Learning Trading Record',
    q_learning_description,
    100000.0
)

# TODO: Rename "Algorithmic" to something else
algorithmic_description = (
    'Uses an algorithmic approach that looks at moving average and rate of change to \n'
    'make trading decisions.  Once an asset is purchased it is put into a queue of \n'
    'pending sales.  Pending sales are sold when current exchange rate rises \n'
    'or when current exchange rate drops to cut losses.'
)
trading_record_registry['algorithmic'] = trading_record.construct(
    'Algorithmic Trading Record',
    algorithmic_description,
    100000.0
)

random_description = (
    'Makes trading decisions randomly.  Used as baseline to judge the \n'
    'effectiveness of other trading strategies.'
)
trading_record_registry['random'] = trading_record.construct(
    'Random Trading Record',
    random_description,
    100000.0
)

session = tf.Session()
trading_model_registry: TradingModelRegistry = {
    'q-learning': q_learning_model.construct(session),
    'algorithmic': algorithmic_model.construct(
        selling_threshold=0.02,
        cut_losses_threshold=-0.05
    ),
    'mac-algorithm': mac_algorithm_model.construct(
        little_n=10,
        big_n=30,
        selling_threshold=0.0,
        cut_losses_threshold=-0.05
    )
}

coinbase_websocket_client = CoinbaseWebsocketClient(trading_record_registry, trading_model_registry)

if hasattr(signal, 'SIGINT'):
    logger.log('listening for ctrl-c on signal.SIGINT')
    signal.signal(signal.SIGINT, close_hf_trader)
elif hasattr(signal, 'SIGBREAK'):
    logger.warn('listening for ctrl-c on signal.SIGBREAK')
    signal.signal(signal.SIGBREAK, close_hf_trader)
else:
    logger.error('unable to set up ctrl-c listeners')


coinbase_websocket_client.start()

logger.log(f'{coinbase_websocket_client.url} {coinbase_websocket_client.products}')

web_application.start(trading_record_registry, trading_model_registry)
