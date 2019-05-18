from typing import Dict

from algorithmic_model import AlgorithmicModel
from mypy_extensions import TypedDict
from q_learning_model import QLearningModel
from extrema_finding_model import ExtremaFindingModel
from trading_record import TradingRecord

TradingModelRegistry = TypedDict('TradingModelRegistry', {
    'q-learning': QLearningModel,
    'algorithmic': AlgorithmicModel,
    'extrema-finding': ExtremaFindingModel
})

# TODO: convert to typed dictionary
TradingRecordRegistry = Dict[str, TradingRecord]
