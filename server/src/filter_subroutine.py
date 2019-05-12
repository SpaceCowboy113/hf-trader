from pyrsistent import PVector, field, pmap

from invariants import must_be_positive, must_be_zero_to_one
from maybe import Maybe
from sliding_window import SlidingWindowSample, Subroutine, SubroutineResult


class FilterSubroutine(Subroutine):
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
    filter_order_ratio = field(type=float, mandatory=True, invariant=must_be_zero_to_one)

    def evaluate(
        self,
        prev_samples: PVector,
        new_sample: SlidingWindowSample
    ) -> Maybe[SubroutineResult]:
        if new_sample is None:
            return None
        else:
            return filter(prev_samples, new_sample, self)
        

def construct(
    first_order_filter_time_constant: float = 1.0,
    second_order_filter_time_constant: float = 0.1,
    filter_order_ratio: float = 0.33
) -> Subroutine:
    return FilterSubroutine(
        results=[],
        first_order_filter_time_constant=first_order_filter_time_constant,
        second_order_filter_time_constant=second_order_filter_time_constant,
        filter_order_ratio=filter_order_ratio
    )


def filter(
    prev_samples: PVector,
    new_sample: SlidingWindowSample, 
    filter: FilterSubroutine
) -> Maybe[SubroutineResult]:
    length = len(prev_samples)
    exchange_rate_filtered = 0.0
    exchange_rate_rate_of_change_filtered = 0.0
    if length == 0:
        exchange_rate_rate_of_change_filtered = 0.0
        exchange_rate_filtered = new_sample.exchange_rate
    elif length == 1:
        t = new_sample.epoch - prev_samples[0].epoch
        if t > 0:
            diff = new_sample.exchange_rate - prev_samples[0].exchange_rate
            exchange_rate_rate_of_change_filtered = diff/t
        else:
            exchange_rate_rate_of_change_filtered = 0.0

        exchange_rate_filtered = new_sample.exchange_rate
    else:
        prev_result = filter.results[-1]
        prev_rate_of_change = prev_result.data['exchange_rate_rate_of_change_filtered']
        t = new_sample.epoch - prev_samples[-1].epoch
        if t > 0:
            diff = new_sample.exchange_rate - prev_samples[-1].exchange_rate
            rate_of_change = diff/t
            exchange_rate_rate_of_change_filtered = (
                prev_rate_of_change +
                (rate_of_change - prev_rate_of_change) *
                min(1, t * filter.second_order_filter_time_constant)
            )
        else:
            exchange_rate_rate_of_change_filtered = prev_rate_of_change

        prev_val = prev_result.value
        exchange_rate_filtered = (
            prev_val +
            filter.filter_order_ratio * (new_sample.exchange_rate - prev_val) *
            min(1, t * filter.first_order_filter_time_constant) +
            (1 - filter.filter_order_ratio) * prev_rate_of_change * t
        )
    return SubroutineResult(
        value=exchange_rate_filtered,
        epoch=new_sample.epoch,
        data=pmap({'exchange_rate_rate_of_change_filtered': exchange_rate_rate_of_change_filtered}))
