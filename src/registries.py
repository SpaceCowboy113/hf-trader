from typing import Dict

from mypy_extensions import TypedDict

from algorithmic_model import AlgorithmicModel
from q_learning_model import QLearningModel
from trading_record import TradingRecord

TradingModelRegistry = TypedDict('TradingModelRegistry', {
    'q-learning': QLearningModel,
    'algorithmic': AlgorithmicModel
})

TradingRecordRegistry = Dict[str, TradingRecord]
