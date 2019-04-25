"""
A model that predicts trading decisions using handbuilt algorithms
"""
from functools import partial
from typing import Tuple

import maybe
import trading_record
from logger import logger
from pyrsistent import PRecord, field, pvector, pvector_field
from trading_record import TradingAction, TradingRecord


class PendingTrade(PRecord):
    buyers_price = field(type=float)


class ExtremaAlgorithmModel(PRecord):
    pending_trades = pvector_field(PendingTrade)
    selling_threshold = field(type=float)
    cut_losses_threshold = field(type=float)


def construct(
    selling_threshold: float = 0.02,
    cut_losses_threshold: float = -0.05
) -> ExtremaAlgorithmModel:
    return ExtremaAlgorithmModel(
        pending_trades=[],
        selling_threshold=selling_threshold,
        cut_losses_threshold=cut_losses_threshold
    )


def predict(
    record: TradingRecord,
    model: ExtremaAlgorithmModel
) -> Tuple[TradingAction, ExtremaAlgorithmModel]:
    exchange_rate = maybe.with_default(0.0, trading_record.get_exchange_rate(record))
    rate_of_change = maybe.with_default(0.0, trading_record.get_rate_of_change(record))
    moving_average = maybe.with_default(0.0, trading_record.get_moving_average(record))

    should_sell_partial = partial(
        should_sell,
        exchange_rate,
        model.selling_threshold,
        model.cut_losses_threshold
    )
    remaining_pending_trades = pvector(
        [trade for trade in model.pending_trades if not should_sell_partial(trade)]
    )
    amount_sold = len(model.pending_trades) - len(remaining_pending_trades)

    buy_sell_diff = 0
    if should_buy(exchange_rate, rate_of_change, moving_average) and \
            record.usd > exchange_rate:
        remaining_pending_trades = remaining_pending_trades.append(
            PendingTrade(buyers_price=exchange_rate)
        )
        buy_sell_diff += 1
    buy_sell_diff -= amount_sold

    updated_model = model.set('pending_trades', remaining_pending_trades)
    if buy_sell_diff < 0:
        return TradingAction(order='sell', amount=abs(buy_sell_diff)), updated_model
    elif buy_sell_diff > 0:
        return TradingAction(order='buy', amount=buy_sell_diff), updated_model
    else:
        return TradingAction(order='hold', amount=0), updated_model


def should_buy(exchange_rate: float, rate_of_change: float, moving_average: float) -> bool:
    if rate_of_change < 0 and moving_average > exchange_rate:
        return True
    else:
        return False


def should_sell(
    exchange_rate: float,
    selling_threshold: float,
    cut_losses_threshold: float,
    pending_trade: PendingTrade
) -> bool:
    price_difference = exchange_rate - pending_trade.buyers_price
    price_difference_ratio = price_difference / pending_trade.buyers_price
    if price_difference_ratio > selling_threshold:
        return True
    elif price_difference_ratio < cut_losses_threshold:
        return True
    return False


def statistics(model: ExtremaAlgorithmModel) -> None:
    logger.log(f'Pending Trades: {len(model.pending_trades)}')
