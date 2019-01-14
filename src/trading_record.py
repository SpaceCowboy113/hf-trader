from datetime import datetime
from typing import Any, Tuple

from pipetools import pipe
from pyrsistent import PRecord, field

import sliding_window
from invariants import cannot_be_negative
from logger import logger
from maybe import Maybe
from result import Error, Result, Warning
# from main import CoinbaseMessage


class TradingRecord(PRecord):
    name = field(type=str, mandatory=True)
    description = field(type=str, mandatory=True)
    initial_usd = field(type=float, invariant=cannot_be_negative, mandatory=True)
    usd = field(type=float, invariant=cannot_be_negative, mandatory=True)
    crypto = field(type=float, invariant=cannot_be_negative, mandatory=True)
    buys = field(type=int, invariant=cannot_be_negative, mandatory=True)
    sells = field(type=int, invariant=cannot_be_negative, mandatory=True)
    holds = field(type=int, invariant=cannot_be_negative, mandatory=True)
    exchange_rates = field(type=sliding_window.SlidingWindow, mandatory=True)


def construct(name: str, description: str = '', initial_usd: float = 0) -> TradingRecord:
    return TradingRecord(
        name=name,
        description=description,
        initial_usd=initial_usd,
        usd=100000.0,
        crypto=0.0,
        buys=0,
        sells=0,
        holds=0,
        exchange_rates=sliding_window.construct(maximum_size=1000)
    )


def valid_order_types(string: str) -> Tuple[bool, str]:
    order_types = {
        'buy': True,
        'sell': True,
        'hold': True
    }
    return string in order_types, 'order must be buy, sell, or hold'


class TradingAction(PRecord):
    order = field(type=str, invariant=valid_order_types)
    amount = field(type=(float, int), invariant=cannot_be_negative)


def buy_crypto(quantity: float, record: TradingRecord) -> Result[TradingRecord]:
    exchange_rate = sliding_window.current_exchange_rate(record.exchange_rates)
    if exchange_rate is None:
        logger.warn(f'Unable to purchase #{quantity} of cryptocurrency '
                    'because exchange_rate is unknown')
        return Error('exchange rate unknown')

    buying_price = exchange_rate * quantity
    if record.usd - buying_price < 0:
        logger.warn(f'Unable to purchase ${buying_price} worth of '
                    'cryptocurrency with ${record.usd}')
        return Warning('cryptocurrency wallet empty')

    return record.update({
        'usd': record.usd - buying_price,
        'crypto': record.crypto + 1,
        'buys': record.buys + 1
    })


def sell_crypto(quantity: float, record: TradingRecord) -> Result[TradingRecord]:
    exchange_rate = sliding_window.current_exchange_rate(record.exchange_rates)
    if exchange_rate is None:
        logger.error(f'Unable to sell #{quantity} of cryptocurrency '
                     'because exchange_rate is unknown')
        return Error('exchange rate unknown')

    if record.crypto - quantity < 0:
        logger.warn(f'Unable to sell {quantity} cryptocurrency with '
                    '{record.crypto} cryptocurrency in wallet')
        return Warning('cryptocurrency wallet empty')

    selling_price = exchange_rate * quantity
    return record.update({
        'usd': record.usd + selling_price,
        'crypto': record.crypto - 1,
        'sells': record.sells + 1
    })


def hold_crypto(record: TradingRecord) -> Result[TradingRecord]:
    return record.set(holds=record.holds + 1)


# Returns epoch (as a float in seconds) from zulu formatted date string
# (zulu date strings are given by coinbase)
def get_epoch(zulu_date: str) -> float:
    return datetime.strptime(zulu_date, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()


def update_exchange_rate(msg: Any, record: TradingRecord) -> Maybe[TradingRecord]:
    if 'price' in msg and 'time' in msg and 'type' in msg and msg['type'] == 'done':
        exchange_rate = float(msg['price'])
        epoch = get_epoch(msg['time'])
        sliding_window_sample = sliding_window.SlidingWindowSample(
            exchange_rate=exchange_rate,
            epoch=epoch
        )
        return (
            pipe
            | (sliding_window.add, sliding_window_sample)
            | (record.set, 'exchange_rates')
        )(record.exchange_rates)
    return None


def place_order(action: TradingAction, record: TradingRecord) -> Result[TradingRecord]:
    if action['order'] is 'buy':
        return buy_crypto(action['amount'], record)
    elif action['order'] is 'sell':
        return sell_crypto(action['amount'], record)
    return hold_crypto(record)


def statistics(record: TradingRecord):
    logger.log(f'-- {record.name} Statistics --')
    exchange_rate = sliding_window.current_exchange_rate(record.exchange_rates)
    logger.log(f'Exchange Rate: {exchange_rate}')
    logger.log(f'USD: {record.usd}')
    logger.log(f'Cryptocurrency: {record.crypto}')
    logger.log(f'Buys: {record.buys}')
    logger.log(f'Sells: {record.sells}')
    logger.log(f'Holds: {record.holds}')
    # logger.log(f'Pending Sales: {len(record.pending_sales)}')
    # logger.log(f'Losses Cut: {record.losses_cut}')
    # profitable_sales = record.sells - record.losses_cut
    # loss_profit_ratio = None
    # if profitable_sales > 0:
    # loss_profit_ratio = record.losses_cut / profitable_sales
    # logger.log(f'Loss Profit Ratio: {loss_profit_ratio}')
    moving_average = sliding_window.average(100, record.exchange_rates)
    logger.log(f'Moving Average: {moving_average}')
    derivative = sliding_window.derivative(100, record.exchange_rates)
    logger.log(f'Rate of Change: {derivative}')
    exchange_rate = get_exchange_rate(record)
    if exchange_rate is not None:
        net_worth = record.usd + record.crypto * exchange_rate
        profit = net_worth - record.initial_usd
        logger.log(f'Net Worth: {net_worth}')
        logger.log(f'Profit: {profit}')


def get_exchange_rate(record: TradingRecord) -> Maybe[float]:
    return sliding_window.current_exchange_rate(record.exchange_rates)


def get_rate_of_change(record: TradingRecord) -> Maybe[float]:
    return sliding_window.derivative(100, record.exchange_rates)


def get_moving_average(record: TradingRecord) -> Maybe[float]:
    return sliding_window.average(100, record.exchange_rates)
