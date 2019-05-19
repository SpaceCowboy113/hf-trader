"""
A model that predicts trading decisions using handbuilt algorithms
"""
from functools import partial
from typing import Tuple

from pyrsistent import PRecord, field, pvector, pvector_field

import trading_record
from invariants import must_be_positive
from logger import logger
from trading_record import TradingAction, TradingRecord


class PendingTrade(PRecord):
    buyers_price = field(type=float, mandatory=True)
    quantity = field(type=float, mandatory=True)


class MacAlgorithmModel(PRecord):
    pending_trades = pvector_field(PendingTrade)
    little_was_over_big = field(type=bool, mandatory=True)
    selling_threshold = field(type=float, mandatory=True)
    cut_losses_threshold = field(type=float, mandatory=True)
    buy_threshold = field(type=float, mandatory=True, invariant=must_be_positive)


def construct(
    selling_threshold: float = 0.02,
    cut_losses_threshold: float = -0.05,
    buy_threshold: float = 0.001
) -> MacAlgorithmModel:
    return MacAlgorithmModel(
        pending_trades=[],
        little_was_over_big=False,
        selling_threshold=selling_threshold,
        cut_losses_threshold=cut_losses_threshold,
        buy_threshold=buy_threshold
    )


def predict(
    record: TradingRecord,
    model: MacAlgorithmModel
) -> Tuple[TradingAction, MacAlgorithmModel]:
    exchange_rate = trading_record.get_exchange_rate(record)
    little_avg_sub = record.exchange_rates.subroutines['little_moving_average'] 
    little_avg = little_avg_sub.results[-1].data['value']
    big_avg_sub = record.exchange_rates.subroutines['big_moving_average']
    big_avg = big_avg_sub.results[-1].data['value']
    if exchange_rate is None or little_avg is None or big_avg is None:
        logger.log('Error: Failed to compute moving averages.')
        return TradingAction(order='hold', amount=0), model

    # Make sure big N is greater than little N.
    if (little_avg_sub.n > big_avg_sub.n):
        logger.log(f'Error: Invalid big N ({big_avg_sub.n}) little N ({little_avg_sub.n}) pair.')

    # Don't do anything until we've seen at least big N samples.
    if len(record.exchange_rates.samples) < big_avg_sub.n:
        return (TradingAction(order='hold', amount=0),
                model.set('little_was_over_big', little_avg > big_avg))

    should_sell_partial = partial(
        should_sell,
        little_avg,
        big_avg,
        model.little_was_over_big,
        exchange_rate,
        model.selling_threshold,
        model.cut_losses_threshold)
    remaining_pending_trades = []
    crypto_to_sell = 0.0
    for trade in model.pending_trades:
        if (should_sell_partial(trade)):
            crypto_to_sell += trade.quantity
        else:
            remaining_pending_trades.append(trade)

    last_acted_price = 0.001
    for transaction in reversed(record.transaction_window):
        if transaction.quantity > 0:
            last_acted_price = transaction.exchange_rate
            break
    crypto_to_buy = quantity_to_buy(
            little_avg, big_avg, model.little_was_over_big, record.usd, exchange_rate,
            last_acted_price, model.buy_threshold)
    if crypto_to_buy > 0:
        remaining_pending_trades.append(
            PendingTrade(buyers_price=exchange_rate, quantity=crypto_to_buy))
    buy_sell_diff = crypto_to_buy - crypto_to_sell

    updated_model = model.update({
        'pending_trades': pvector(remaining_pending_trades),
        'little_was_over_big': little_avg > big_avg})
    if buy_sell_diff < 0:
        return TradingAction(order='sell', amount=abs(buy_sell_diff)), updated_model
    elif buy_sell_diff > 0:
        return TradingAction(order='buy', amount=buy_sell_diff), updated_model
    else:
        return TradingAction(order='hold', amount=0), updated_model


def quantity_to_buy(
    little_avg: float,
    big_avg: float,
    little_was_over_big: bool,
    usd_available: float,
    exchange_rate: float,
    last_acted_price: float,
    buy_threshold: float
) -> float:
    price_difference = exchange_rate - last_acted_price
    price_difference_ratio = abs(price_difference / last_acted_price)
    if (price_difference_ratio > buy_threshold and
            little_avg > big_avg and
            not little_was_over_big):
        return 0.33 * usd_available / exchange_rate
    else:
        return 0.0


def should_sell(
    little_avg: float,
    big_avg: float,
    little_was_over_big: bool,
    exchange_rate: float,
    selling_threshold: float,
    cut_losses_threshold: float,
    pending_trade: PendingTrade
) -> bool:
    price_difference = exchange_rate - pending_trade.buyers_price
    price_difference_ratio = price_difference / pending_trade.buyers_price
    if little_avg < big_avg and little_was_over_big and price_difference_ratio > selling_threshold:
        return True
    elif price_difference_ratio < cut_losses_threshold:
        return True
    return False


def statistics(model: MacAlgorithmModel) -> None:
    logger.log(f'Pending Trades: {len(model.pending_trades)}')
    logger.log('Little over Big' if model.little_was_over_big else 'Big over Little')
