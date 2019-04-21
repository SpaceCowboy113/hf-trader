from typing import Callable, List, TypeVar, Union

T = TypeVar('T')
V = TypeVar('V')
Maybe = Union[T, None]


def with_default(default: T, maybe: Maybe[T]) -> T:
    return default if maybe is None else maybe


def map1(callback: Callable[[T], V], maybe: Maybe[T]) -> Maybe[V]:
    if maybe is None:
        return None
    return callback(maybe)


def map2(callback: Callable[[T, T], V], maybe1: Maybe[T], maybe2: Maybe[T]) -> Maybe[V]:
    if maybe1 is None or maybe2 is None:
        return None
    return callback(maybe1, maybe2)


def map3(
    callback: Callable[[T, T, T], V],
    maybe1: Maybe[T],
    maybe2: Maybe[T],
    maybe3: Maybe[T]
) -> Maybe[V]:
    if maybe1 is None or maybe2 is None or maybe3 is None:
        return None
    return callback(maybe1, maybe2, maybe3)


def map_all(callbacks: List[Callable[[T], V]], maybe: Maybe[T]) -> List[Maybe[V]]:
    results = []
    for fn in callbacks:
        results.append(map1(fn, maybe))
    return results


def and_then(callback: Callable[[T], Maybe[V]], maybe: Maybe[T]) -> Maybe[V]:
    if maybe is None:
        return None
    return callback(maybe)
