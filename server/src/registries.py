from typing import Dict

from algorithmic_model import AlgorithmicModel
from mypy_extensions import TypedDict
from q_learning_model import QLearningModel
from trading_record import TradingRecord
from extrema_algorithm_model import ExtremaAlgorithmModel

TradingModelRegistry = TypedDict('TradingModelRegistry', {
    'q-learning': QLearningModel,
    'algorithmic': AlgorithmicModel,
    'extrema-algorithm': ExtremaAlgorithmModel
})

# TODO: convert to typed dictionary
TradingRecordRegistry = Dict[str, TradingRecord]
