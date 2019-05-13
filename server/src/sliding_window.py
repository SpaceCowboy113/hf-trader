import operator
from functools import reduce
from typing import Union

from invariants import must_be_positive
from maybe import Maybe
from pipetools import X, pipe
from pyrsistent import PRecord, PVector, field, pvector_field, pmap_field, PMap, m


class SlidingWindowSample(PRecord):
    exchange_rate = field(type=float, mandatory=True)
    epoch = field(type=float, mandatory=True)


class SubroutineResult(PRecord):
    # TODO: Allow any value types.
    data = pmap_field(str, float)
    epoch = field(type=float, mandatory=True)


class Subroutine(PRecord):
    results = pvector_field(SubroutineResult)

    def evaluate(
        self,
        prev_samples: PVector,
        new_sample: SlidingWindowSample
    ) -> Maybe[SubroutineResult]:
        ...


class SlidingWindow(PRecord):
    samples = pvector_field(SlidingWindowSample)
    maximum_size = field(type=int, mandatory=True, invariant=must_be_positive)
    subroutines = pmap_field(str, Subroutine)


def construct(
    maximum_size: int = 1,
    subroutines: PMap = m()
) -> SlidingWindow:
    return SlidingWindow(
        samples=[],
        maximum_size=maximum_size,
        subroutines=subroutines
    )


def add(sample: SlidingWindowSample, window: SlidingWindow) -> SlidingWindow:
    updated_subroutines = window.subroutines
    for name, subroutine in window.subroutines.items():
        result = subroutine.evaluate(window.samples, sample)
        if result is None:
            continue
        if len(subroutine.results) >= window.maximum_size:
            updated_subroutine = subroutine.update(
                {'results': subroutine.results.append(result)[1:]})
        else:
            updated_subroutine = subroutine.update({'results': subroutine.results.append(result)})
        updated_subroutines = updated_subroutines.update({name: updated_subroutine})
    
    # Pop oldest sample to keep length of samples less than maximum size
    if len(window.samples) >= window.maximum_size:
        return window.update(
            {'samples': window.samples.append(sample)[1:], 'subroutines': updated_subroutines})
    else:
        return window.update(
            {'samples': window.samples.append(sample), 'subroutines': updated_subroutines})


def average(n: int, samples: PVector) -> float:
    sliced_samples = time_slice(n, samples)
    length = len(sliced_samples)
    if length != 0:
        sum = sliced_samples > pipe | (map, ~X.exchange_rate) | (reduce, operator.add)
        return sum / length
    return 0.0


def derivative(n: int, samples: PVector) -> float:
    if n < 2 or len(samples) < n:
        return 0.0
    sliced_samples = time_slice(n, samples)
    epoch_average = 0.0
    exchange_rate_average = 0.0
    for sample in sliced_samples:
        epoch_average += sample.epoch
        exchange_rate_average += sample.exchange_rate
    epoch_average /= len(sliced_samples)
    exchange_rate_average /= len(sliced_samples)

    # See https://www.varsitytutors.com/hotmath/hotmath_help/topics/line-of-best-fit
    numerator = 0.0
    denom = 0.0
    for sample in sliced_samples:
        epoch_error = sample.epoch - epoch_average
        exchange_rate_error = sample.exchange_rate - exchange_rate_average
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


def current_epoch(window: SlidingWindow) -> Union[float, None]:
    if len(window.samples) == 0:
        return None
    return window.samples[-1].epoch
