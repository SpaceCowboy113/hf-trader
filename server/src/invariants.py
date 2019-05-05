from typing import Tuple, Union


def cannot_be_negative(number: Union[int, float]) -> Tuple[bool, str]:
    return number >= 0, 'cannot be negative'


def must_be_positive(number: Union[int, float]) -> Tuple[bool, str]:
    return number > 0, 'must be positive'

def must_be_zero_to_one(number: float) -> Tuple[bool, str]:
    return number >= 0 and number <= 1, 'must be between 0 and 1 inclusively'
