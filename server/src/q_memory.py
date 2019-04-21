import random

from pyrsistent import PRecord, PVector, field, pvector_field
from q_records import QModelInput
from trading_record import TradingAction


class QMemorySample(PRecord):
    neural_network_input = field(type=QModelInput)
    neural_network_prediction = field(type=TradingAction)
    reward = field(type=float)


class QMemory(PRecord):
    samples = pvector_field(QMemorySample)
    maximum_size = field(type=int)


def construct(maximum_size: int = 1) -> QMemory:
    return QMemory(
        samples=[],
        maximum_size=maximum_size
    )


def add(sample: QMemorySample, memory: QMemory) -> QMemory:
    # Pop oldest sample to keep length of samples less than maximum size
    if len(memory.samples) >= memory.maximum_size:
        return memory.update({'samples': memory.samples.append(sample)[1:]})
    return memory.update({'samples': memory.samples.append(sample)})


# Returns a random list of samples to train with of length sample_size
def get_random_samples(sample_size: int, memory: QMemory) -> PVector:
    if len(memory.samples) < sample_size:
        return memory.samples
    random_index = random.randint(0, len(memory.samples) - sample_size)
    return memory.samples[random_index:random_index + sample_size]
