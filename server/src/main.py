import algorithmic_model
import q_learning_model
import tensorflow as tf
import trading_record
import web_application
from coinbase_websocket_client import (CoinbaseWebsocketClient,  # noqa: F401
                                       TradingModelRegistry,
                                       TradingRecordRegistry)
from logger import logger
import signal
import sys

trading_record_registry: TradingRecordRegistry = {}

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
    )
}

coinbase_websocket_client = CoinbaseWebsocketClient(trading_record_registry, trading_model_registry)
coinbase_websocket_client.start()

logger.log(f'{coinbase_websocket_client.url} {coinbase_websocket_client.products}')

web_application.start(trading_record_registry, trading_model_registry)


def close_hf_trader(sig, frame):
    logger.info('closing high-frequency trader')
    coinbase_websocket_client.close()
    sys.exit(0)


signal.signal(signal.SIGINT, close_hf_trader)
