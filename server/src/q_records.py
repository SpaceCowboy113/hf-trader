
from pyrsistent import PRecord, field

# TODO: rename to NeuralNetworkInput and NeuralNetworkOutput


class QModelInput(PRecord):
    exchange_rate = field(type=float)
    rate_of_change = field(type=float)
    moving_average = field(type=float)


# TODO: rename to QRewards?
class QModelOutput(PRecord):
    buy = field(type=float)
    sell = field(type=float)
    hold = field(type=float)
