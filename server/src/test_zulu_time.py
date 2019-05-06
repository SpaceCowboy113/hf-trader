import pytest  # noqa: F401
import zulu_time


def test_time_conversion():
    def epoch_should_not_change():
        epoch = 1552103321.951
        timestamp = zulu_time.get_timestamp(epoch)
        converted_epoch = zulu_time.get_epoch(timestamp)
        assert epoch == converted_epoch

    def timestamp_should_not_change():
        timestamp = '2019-03-08T19:48:41.951000Z'
        epoch = zulu_time.get_epoch(timestamp)
        converted_timestamp = zulu_time.get_timestamp(epoch)
        assert timestamp == converted_timestamp
