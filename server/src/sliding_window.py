from pyrsistent import PRecord, field, pvector_field,  PVector
from invariants import must_be_positive
from typing import Union
from functools import reduce
import operator
from pipetools import pipe, X


class SlidingWindowSample(PRecord):
    exchange_rate = field(type=float, mandatory=True)
    epoch = field(type=float, mandatory=True)


class SlidingWindow(PRecord):
    samples = pvector_field(SlidingWindowSample)
    maximum_size = field(type=int, mandatory=True, invariant=must_be_positive)


def construct(maximum_size: int = 1) -> SlidingWindow:
    return SlidingWindow(
        samples=[],
        maximum_size=maximum_size
    )


def add(sample: SlidingWindowSample, window: SlidingWindow) -> SlidingWindow:
    # Pop oldest sample to keep length of samples less than maximum size
    if len(window.samples) >= window.maximum_size:
        return window.update({'samples': window.samples.append(sample)[1:]})
    return window.update({'samples': window.samples.append(sample)})


def average(n: int, window: SlidingWindow) -> float:
    sliced_samples = time_slice(n, window.samples)
    length = len(sliced_samples)
    if length != 0:
        sum = sliced_samples > pipe | (map, ~X.exchange_rate) | (reduce, operator.add)
        return sum / length
    return 0.0


def derivative(n: int, window: SlidingWindow) -> float:
    if len(window.samples) < 2:
        return 0.0
    sliced_samples = time_slice(n, window.samples)
    first_exchange_rate = sliced_samples[0]['exchange_rate']
    last_exchange_rate = sliced_samples[-1]['exchange_rate']
    first_epoch = sliced_samples[0]['epoch']
    last_epoch = sliced_samples[-1]['epoch']
    exchange_rate_delta = last_exchange_rate - first_exchange_rate
    epoch_delta = last_epoch - first_epoch
    return exchange_rate_delta / epoch_delta if epoch_delta != 0 else 0.0


# Slices the (n) most recent samples in time
def time_slice(n: int, samples: PVector) -> PVector:
    if n > len(samples):
        return samples
    return samples[-n:]


def current_exchange_rate(window: SlidingWindow) -> Union[float, None]:
    if len(window.samples) == 0:
        return None
    return window.samples[-1].exchange_rate


def current_epoch(window: SlidingWindow) -> Union[float, None]:
    if len(window.samples) == 0:
        return None
    return window.samples[-1].epoch
