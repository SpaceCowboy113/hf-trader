from pyrsistent import PVector, field

from invariants import must_be_positive
from maybe import Maybe
from sliding_window import SlidingWindowSample, Subroutine, SubroutineResult, average


class MovingAverageSubroutine(Subroutine):
    # The number of exchange rate samples that are averaged into each sliding window sample.
    n = field(type=int, mandatory=True, invariant=must_be_positive)

    def evaluate(
        self,
        prev_samples: PVector,
        new_sample: SlidingWindowSample
    ) -> Maybe[SubroutineResult]:
        if new_sample is not None:
            return SubroutineResult(
                value=next_moving_average(self.n, prev_samples, new_sample),
                epoch=new_sample.epoch)
        return None
        

def construct(n: int) -> Subroutine:
    return MovingAverageSubroutine(
        results=[],
        n=n
    )

    
def next_moving_average(
    n: int,
    prev_samples: PVector,
    new_sample: SlidingWindowSample
) -> float:
    all_samples = prev_samples.append(new_sample)
    return average(n, all_samples)
