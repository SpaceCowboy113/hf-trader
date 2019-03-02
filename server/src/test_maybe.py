import pytest  # noqa: F401
import maybe
import testing_utilities


def test_with_default():
    assert maybe.with_default('default', None) == 'default'
    assert maybe.with_default('default', 'value_exists') == 'value_exists'


def test_and_then():
    def should_not_call_if_maybe_is_none():
        stub = testing_utilities.create_stub()
        maybe.and_then(stub, None)
        assert stub.called == 0

    def should_call_if_maybe_exists():
        stub = testing_utilities.create_stub()
        maybe.and_then(stub, 'maybe_exists')

        assert stub.called == 1
        assert stub.called_with[0][0] == 'maybe_exists'

    should_not_call_if_maybe_is_none()
    should_call_if_maybe_exists()
