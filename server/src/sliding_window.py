import operator
from functools import reduce
from typing import Union

from invariants import must_be_positive, must_be_zero_to_one
from pipetools import X, pipe
from pyrsistent import PRecord, PVector, field, pvector_field


class SlidingWindowSample(PRecord):
    exchange_rate = field(type=float, mandatory=True)
    exchange_rate_filtered = field(type=float, mandatory=False)
    exchange_rate_rate_of_change_filtered = field(type=float, mandatory=False)
    exchange_rate_moving_average_10 = field(type=float, mandatory=False)
    exchange_rate_moving_average_100 = field(type=float, mandatory=False)
    epoch = field(type=float, mandatory=True)


class SlidingWindow(PRecord):
    samples = pvector_field(SlidingWindowSample)
    maximum_size = field(type=int, mandatory=True, invariant=must_be_positive)
    # Pararmeterizes the response of the first-order filter. Larger values make
    # the filter more responsive but preserve more noise in the signal.
    first_order_filter_time_constant = field(
        type=float, mandatory=True, invariant=must_be_positive)
    # Pararmeterizes the response of the second-order filter. Larger values make
    # the filter more responsive but preserve more noise in the signal.
    second_order_filter_time_constant = field(
        type=float, mandatory=True, invariant=must_be_positive)
    # The ratio of contributions between the first and second order filters. A
    # value of 0.25 means that (1/4) of the filter response comes from the first
    # order filter and (3/4) of the response comes from the second order filter.
    filter_order_ratio = field(type=float, mandatory=True,
                               invariant=must_be_zero_to_one)


def construct(
    maximum_size: int = 1,
    first_order_filter_time_constant: float = 1.0,
    second_order_filter_time_constant: float = 0.1,
    filter_order_ratio: float = 0.33
) -> SlidingWindow:
    return SlidingWindow(
        samples=[],
        maximum_size=maximum_size,
        first_order_filter_time_constant=first_order_filter_time_constant,
        second_order_filter_time_constant=second_order_filter_time_constant,
        filter_order_ratio=filter_order_ratio
    )


def next_moving_average(
    n: int,
    window: SlidingWindow,
    next_sample: SlidingWindowSample,
) -> float:
    last_moving_average = average(n, window)
    last_window_length = len(time_slice(n, window.samples))
    sum = last_moving_average * last_window_length + next_sample.exchange_rate
    return sum / (last_window_length + 1)


def add(sample: SlidingWindowSample, window: SlidingWindow) -> SlidingWindow:
    updated_sample = filter_sample(sample, window).update({
        'exchange_rate_moving_average_10': next_moving_average(10, window, sample),
        'exchange_rate_moving_average_100': next_moving_average(100, window, sample),
    })

    # Pop oldest sample to keep length of samples less than maximum size
    if len(window.samples) >= window.maximum_size:
        return window.update({'samples': window.samples.append(updated_sample)[1:]})
    return window.update({'samples': window.samples.append(updated_sample)})


def filter_sample(sample: SlidingWindowSample, window: SlidingWindow) -> SlidingWindowSample:
    length = len(window.samples)
    exchange_rate_filtered = 0.0
    exchange_rate_rate_of_change_filtered = 0.0
    if length == 0:
        exchange_rate_rate_of_change_filtered = 0.0
        exchange_rate_filtered = sample.exchange_rate
    elif length == 1:
        t = sample.epoch - window.samples[0].epoch
        if t > 0:
            diff = sample.exchange_rate - window.samples[0].exchange_rate
            exchange_rate_rate_of_change_filtered = diff/t
        else:
            exchange_rate_rate_of_change_filtered = 0.0

        exchange_rate_filtered = sample.exchange_rate
    else:
        prev_rate_of_change = window.samples[-1].exchange_rate_rate_of_change_filtered
        t = sample.epoch - window.samples[-1].epoch
        if t > 0:
            diff = sample.exchange_rate - window.samples[-1].exchange_rate
            rate_of_change = diff/t
            exchange_rate_rate_of_change_filtered = (
                prev_rate_of_change +
                (rate_of_change - prev_rate_of_change) *
                min(1, t * window.second_order_filter_time_constant)
            )
        else:
            exchange_rate_rate_of_change_filtered = prev_rate_of_change

        prev_val = window.samples[-1].exchange_rate_filtered
        exchange_rate_filtered = (
            prev_val +
            window.filter_order_ratio * (sample.exchange_rate - prev_val) *
            min(1, t * window.first_order_filter_time_constant) +
            (1 - window.filter_order_ratio) * prev_rate_of_change * t
        )
    return sample.update({
        'exchange_rate_filtered': exchange_rate_filtered,
        'exchange_rate_rate_of_change_filtered': exchange_rate_rate_of_change_filtered
    })


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
        exchange_rate_error = sample['exchange_rate'] - exchange_rate_average
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


def current_exchange_rate_filtered(window: SlidingWindow) -> Union[float, None]:
    if len(window.samples) == 0:
        return None
    return window.samples[-1].exchange_rate_filtered


def current_epoch(window: SlidingWindow) -> Union[float, None]:
    if len(window.samples) == 0:
        return None
    return window.samples[-1].epoch
