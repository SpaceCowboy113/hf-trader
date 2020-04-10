from typing import Dict, Any

from algorithmic_model import AlgorithmicModel
from mypy_extensions import TypedDict
from q_learning_model import QLearningModel
from trading_record import TradingRecord

# TradingModelRegistry = TypedDict('TradingModelRegistry', {
#     'q-learning': QLearningModel,
#     'algorithmic': AlgorithmicModel
# })

# TODO: convert to typed dictionary
# TradingModelRegistry = Dict[str, Union[QLearningModel, AlgorithmicModel, GeneticModel]]
TradingModelRegistry = Dict[str, Any]
TradingRecordRegistry = Dict[str, TradingRecord]
