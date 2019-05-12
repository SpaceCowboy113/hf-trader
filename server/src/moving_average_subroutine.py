import operator
from functools import reduce

from pipetools import X, pipe
from pyrsistent import PVector, field

from invariants import must_be_positive
from maybe import Maybe
from sliding_window import Subroutine, SubroutineResult, time_slice


class MovingAverageSubroutine(Subroutine):
    # The number of exchange rate samples that are averaged into each sliding window sample.
    n = field(type=int, mandatory=True, invariant=must_be_positive)

    def evaluate(self, samples: PVector) -> Maybe[SubroutineResult]:
        if len(samples) < 1:
            return None
        else:
            return SubroutineResult(
                value=average(self.n, samples),
                epoch=samples[-1].epoch
            )
        

def construct(n: int) -> Subroutine:
    return MovingAverageSubroutine(
        results=[],
        n=n
    )

    
def average(n: int, samples: PVector) -> float:
    sliced_samples = time_slice(n, samples)
    length = len(sliced_samples)
    if length != 0:
        sum = sliced_samples > pipe | (map, ~X.exchange_rate) | (reduce, operator.add)
        return sum / length
    return 0.0
