import pytest  # noqa: F401
import trading_record


def test_time_conversion():
    def epoch_should_not_change():
        epoch = 1552103321.951
        timestamp = trading_record.get_timestamp(epoch)
        converted_epoch = trading_record.get_epoch(timestamp)
        assert epoch == converted_epoch

    def timestamp_should_not_change():
        timestamp = '2019-03-08T19:48:41.951000Z'
        epoch = trading_record.get_epoch(timestamp)
        converted_timestamp = trading_record.get_timestamp(epoch)
        assert timestamp == converted_timestamp
