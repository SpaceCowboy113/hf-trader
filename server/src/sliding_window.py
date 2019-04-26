import operator
from maybe import Maybe
from functools import reduce
from typing import Union

from invariants import must_be_positive
from pipetools import X, pipe
from pyrsistent import PRecord, PVector, field, pvector_field


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


# Returns the average of the n most recent samples in time
def last_average(n: int, window: SlidingWindow) -> float:
    sliced_samples = last_time_slice(n, window.samples)
    length = len(sliced_samples)
    if length != 0:
        sum = sliced_samples > pipe | (map, ~X.exchange_rate) | (reduce, operator.add)
        return sum / length
    return 0.0


# Returns the average of samples [begin, end) in time
def slice_average(begin: int, end:int, window: SlidingWindow) -> float:
    sliced_samples = time_slice(begin, end, window.samples)
    if sliced_samples is None:
        return 0.0
    length = len(sliced_samples)
    if length != 0:
        sum = sliced_samples > pipe | (map, ~X.exchange_rate) | (reduce, operator.add)
        return sum / length
    return 0.0


# Returns the slope of the line of best fit for the last n samples in time
def last_derivative(n: int, window: SlidingWindow) -> float:
    if n < 2 or len(window.samples) < n:
        return 0.0
    sliced_samples = last_time_slice(n, window.samples)
    return samples_derivative(sliced_samples)


# Returns the slope of the line of best fit for samples [begin, end) in time
def slice_derivative(begin: int, end: int, window: SlidingWindow) -> float:
    if end - begin < 2 or len(window.samples) < end - begin:
        return 0.0
    sliced_samples = time_slice(begin, end, window.samples)
    if sliced_samples is None:
        return 0.0
    return samples_derivative(sliced_samples)


# Returns the slope of the line of best for the given samples
def samples_derivative(samples: PVector):
    epoch_average = 0.0
    exchange_rate_average = 0.0
    for sample in samples:
        epoch_average += sample['epoch']
        exchange_rate_average += sample['exchange_rate']
    epoch_average /= len(samples)
    exchange_rate_average /= len(samples)

    # See https://www.varsitytutors.com/hotmath/hotmath_help/topics/line-of-best-fit
    numerator = 0.0
    denom = 0.0
    for sample in samples:
        epoch_error = sample['epoch'] - epoch_average
        exchange_rate_error =  sample['exchange_rate'] - exchange_rate_average
        numerator += epoch_error * exchange_rate_error
        denom += epoch_error * epoch_error

    return numerator / denom if denom != 0 else 0.0


# Returns the most recent extreme value of the moving n-average
#
# Compare against most recent value to determine whether the extreme is a peak
# or trough
def last_extreme(n: int, window: SlidingWindow) -> float:
    N = len(window.samples)
    if N < n + 3:
        return 0.0
    begin = N - n
    slope_b = slice_derivative(begin, begin + n, window)
    begin -= 1
    slope_a = slice_derivative(begin, begin + n, window)
    current_slope_diff = slope_b - slope_a
    previous_slope_diff = current_slope_diff  # So while loops at least once

    while(current_slope_diff * previous_slope_diff > 0):
        begin -= 1
        if (begin < 0):
            return 0.0
        slope_b = slope_a
        current_slope_diff = previous_slope_diff
        slope_a = slice_derivative(begin, begin + n, window)
        previous_slope_diff = slope_b - slope_a

    avg_b = slice_average(begin + 1, begin + n + 1, window)
    avg_a = slice_average(begin, begin + n, window)
    return min(avg_b, avg_a) if current_slope_diff - previous_slope_diff > 0 \
        else max(avg_b, avg_a)


# Slices the (n) most recent samples in time
def last_time_slice(n: int, samples: PVector) -> PVector:
    if n > len(samples):
        return samples
    return samples[-n:]


# Slices samples from [begin, end) of time
def time_slice(begin: int, end: int, samples: PVector) -> Maybe[PVector]:
    length = len(samples)
    if begin < 0 or end < begin or begin > length - 1:
        return None
    elif end > length - 1:
        return samples
    return samples[begin: min(end, len(samples))]


def current_exchange_rate(window: SlidingWindow) -> Union[float, None]:
    if len(window.samples) == 0:
        return None
    return window.samples[-1].exchange_rate


def current_epoch(window: SlidingWindow) -> Union[float, None]:
    if len(window.samples) == 0:
        return None
    return window.samples[-1].epoch
