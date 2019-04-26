import operator
from functools import reduce
from typing import Union

from invariants import must_be_positive
from pipetools import X, pipe
from pyrsistent import PRecord, PVector, field, pvector_field


class SlidingWindowSample(PRecord):
    exchange_rate = field(type=float, mandatory=True)
    filtered_exchange_rate = field(type=float, mandatory=False)
    filtered_exchange_rate_rate_of_change = field(type=float, mandatory=False)
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
    filtered_sample = filter_sample(sample, window)

    # Pop oldest sample to keep length of samples less than maximum size
    if len(window.samples) >= window.maximum_size:
        return window.update({'samples': window.samples.append(filtered_sample)[1:]})
    return window.update({'samples': window.samples.append(filtered_sample)})


def filter_sample(sample: SlidingWindowSample, window: SlidingWindow) -> SlidingWindowSample:
    length = len(window.samples)
    filtered_exchange_rate = 0.0
    filtered_exchange_rate_rate_of_change = 0.0
    if length == 0:
        filtered_exchange_rate_rate_of_change = 0.0
        filtered_exchange_rate = sample.exchange_rate
    elif length == 1:
        t = sample.epoch - window.samples[0].epoch
        if t > 0:
            diff = sample.exchange_rate - window.samples[0].exchange_rate
            filtered_exchange_rate_rate_of_change = diff/t
        else:
            filtered_exchange_rate_rate_of_change = 0.0

        filtered_exchange_rate = sample.exchange_rate
    else:
        prev_rate_of_change = window.samples[-1].filtered_exchange_rate_rate_of_change
        t = sample.epoch - window.samples[-1].epoch
        if t > 0:
            diff = sample.exchange_rate - window.samples[-1].exchange_rate
            rate_of_change = diff/t
            filtered_exchange_rate_rate_of_change = (prev_rate_of_change +
                (rate_of_change - prev_rate_of_change) * min(1, t * 0.1))
        else:
            filtered_exchange_rate_rate_of_change = prev_rate_of_change

        prev_val = window.samples[-1].filtered_exchange_rate
        filter_order_ratio = 0.25
        filtered_exchange_rate = prev_val + filter_order_ratio * (sample.exchange_rate - prev_val) * min(1, t * 0.1) + (1 - filter_order_ratio) * prev_rate_of_change * t
    filtered_sample = sample.set('filtered_exchange_rate', filtered_exchange_rate)
    filtered_sample = filtered_sample.set('filtered_exchange_rate_rate_of_change', filtered_exchange_rate_rate_of_change)
    return filter_sample


def average(n: int, window: SlidingWindow) -> float:
    sliced_samples = time_slice(n, window.samples)
    length = len(sliced_samples)
    if length != 0:
        sum = sliced_samples > pipe | (map, ~X.exchange_rate) | (reduce, operator.add)
        return sum / length
    return 0.0


def derivative(n: int, window: SlidingWindow) -> float:
    if n < 2 or len(window.samples) < n:
        return 0.0
    sliced_samples = time_slice(n, window.samples)
    epoch_average = 0.0
    exchange_rate_average = 0.0
    for sample in sliced_samples:
        epoch_average += sample['epoch']
        exchange_rate_average += sample['exchange_rate']
    epoch_average /= len(sliced_samples)
    exchange_rate_average /= len(sliced_samples)

    # See https://www.varsitytutors.com/hotmath/hotmath_help/topics/line-of-best-fit
    numerator = 0.0
    denom = 0.0
    for sample in sliced_samples:
        epoch_error = sample['epoch'] - epoch_average
        exchange_rate_error =  sample['exchange_rate'] - exchange_rate_average
        numerator += epoch_error * exchange_rate_error
        denom += epoch_error * epoch_error

    return numerator / denom if denom != 0 else 0.0


# Slices the (n) most recent samples in time
def time_slice(n: int, samples: PVector) -> PVector:
    if n > len(samples):
        return samples
    return samples[-n:]


def current_exchange_rate(window: SlidingWindow) -> Union[float, None]:
    if len(window.samples) == 0:
        return None
    return window.samples[-1].exchange_rate


def current_filtered_exchange_rate(window: SlidingWindow) -> Union[float, None]:
    if len(window.samples) == 0:
        return None
    return window.samples[-1].filtered_exchange_rate


def current_epoch(window: SlidingWindow) -> Union[float, None]:
    if len(window.samples) == 0:
        return None
    return window.samples[-1].epoch
