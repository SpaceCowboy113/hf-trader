from typing import Dict

from algorithmic_model import AlgorithmicModel
from mypy_extensions import TypedDict
from q_learning_model import QLearningModel
from mac_algorithm_model import MacAlgorithmModel
from trading_record import TradingRecord

TradingModelRegistry = TypedDict('TradingModelRegistry', {
    'q-learning': QLearningModel,
    'algorithmic': AlgorithmicModel,
    'mac-algorithm': MacAlgorithmModel
})

# TODO: convert to typed dictionary
TradingRecordRegistry = Dict[str, TradingRecord]
