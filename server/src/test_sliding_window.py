import pytest  # noqa: F401
from pyrsistent import pvector
from sliding_window import (SlidingWindowSample, add, average, construct,
                            current_exchange_rate, derivative, time_slice)


def add_sample(exchange_rate, window):
    return add(SlidingWindowSample(exchange_rate=exchange_rate, epoch=0.0), window)


def test_add():
    window_size_1 = add_sample(1.0, construct(1))
    assert len(window_size_1.samples) == 1
    truncated_window = add_sample(2.0, window_size_1)
    assert len(truncated_window.samples) == 1
    assert truncated_window.samples[0].exchange_rate == 2.0


def test_average():
    window_size_0 = construct(10)
    assert average(10, window_size_0) == 0.0
    window_size_1 = add_sample(1.0, window_size_0)
    assert average(10, window_size_1) == 1.0
    window_size_2 = add_sample(2.0, window_size_1)
    assert average(10, window_size_2) == 1.5
    window_size_3 = add_sample(1.7, window_size_2)
    assert average(10, window_size_3) == (1.0 + 2.0 + 1.7) / 3
    assert average(2, window_size_3) == (2.0 + 1.7) / 2


def test_derivative():
    window_size_1 = add_sample(1.0, construct(10))
    window_size_2 = add(SlidingWindowSample(exchange_rate=3.0, epoch=1.0), window_size_1)
    window_size_3 = add(SlidingWindowSample(exchange_rate=3.0, epoch=2.0), window_size_2)
    assert derivative(2, window_size_1) == 0.0
    assert derivative(2, window_size_2) == (3.0 - 1.0) / (1.0 - 0.0)
    assert derivative(2, window_size_3) == (3.0 - 3.0) / (2.0 - 1.0)


def test_time_slice():
    assert time_slice(1, pvector([1])) == pvector([1])
    assert time_slice(1, pvector([1, 2])) == pvector([2])
    assert time_slice(2, pvector([1, 2, 3, 4])) == pvector([3, 4])
    assert time_slice(10, pvector([1, 2, 3, 4])) == pvector([1, 2, 3, 4])


def test_current_exchange_rate():
    window_size_0 = construct(10)
    assert current_exchange_rate(window_size_0) is None
    window_size_1 = add_sample(1.0, window_size_0)
    assert current_exchange_rate(window_size_1) == 1.0
    window_size_2 = add_sample(2.0, window_size_1)
    assert current_exchange_rate(window_size_2) == 2.0
