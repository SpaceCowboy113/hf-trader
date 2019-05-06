import csv
from typing import List, Tuple  # noqa: F401

import zulu_time
from pyrsistent import PRecord, PVector, field, pvector


# TODO: consolidate this function (duplicated in trading_record)
def valid_order_types(string: str) -> Tuple[bool, str]:
    order_types = {
        'buy': True,
        'sell': True,
        'hold': True
    }
    return string in order_types, 'order must be buy, sell, or hold'


# TODO: figure out a way to consolidate transaction state
# between Transaction, TradingAction, and TradingRecord records
class Transaction(PRecord):
    label = field(type=str, mandatory=True)
    quantity = field(type=float, mandatory=False)
    exchange_rate = field(type=float, mandatory=False)
    epoch = field(type=float, mandatory=False)
    fees = field(type=float, mandatory=False)
    order = field(type=str, invariant=valid_order_types, mandatory=True)


def must_have_same_label(transactions) -> Tuple[bool, str]:
    return transactions.buy.label == transactions.sell.label, 'transactions must have same label'


class PairedTransactions(PRecord):
    __invariant__ = must_have_same_label
    buy = field(type=Transaction, mandatory=True)
    sell = field(type=Transaction, mandatory=True)


# TODO: move into a transaction_window.py file
def window_add(transaction: Transaction, transaction_window: PVector) -> PVector:
    MAXIMUM_SIZE = 1000
    if len(transaction_window) >= MAXIMUM_SIZE:
        return transaction_window.append(transaction)[1:]
    return transaction_window.append(transaction)


def record_paired_transaction(  # TODO: Renamed to record_transaction_pair
    path: str,
    paired_transactions: PairedTransactions
) -> None:
    with open(path, 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow([
            paired_transactions.sell.label,
            paired_transactions.buy.quantity,
            paired_transactions.buy.exchange_rate,
            zulu_time.get_timestamp(paired_transactions.buy.epoch),
            paired_transactions.buy.fees,
            paired_transactions.sell.quantity,
            paired_transactions.sell.exchange_rate,
            zulu_time.get_timestamp(paired_transactions.sell.epoch),
            paired_transactions.sell.fees,
            calculate_capital_gains(paired_transactions)
        ])


def open_transaction_history(path: str) -> PVector:
    transactions = []
    with open(path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            paired_transaction = PairedTransactions(
                buy=Transaction(
                    label=row[0],
                    quantity=float(row[1]),
                    exchange_rate=float(row[2]),
                    epoch=zulu_time.get_epoch(row[3]),
                    fees=float(row[4]),
                ),
                sell=Transaction(
                    label=row[0],
                    quantity=float(row[5]),
                    exchange_rate=float(row[6]),
                    epoch=zulu_time.get_epoch(row[7]),
                    fees=float(row[8])
                )
            )
            transactions.append(paired_transaction)
    return pvector(transactions)


def calculate_capital_gains(transactions: PairedTransactions) -> float:
    purchase_price = transactions.buy.quantity * transactions.buy.exchange_rate
    selling_price = transactions.buy.quantity * transactions.sell.exchange_rate
    price_delta = selling_price - purchase_price
    fees = transactions.buy.fees + transactions.sell.fees
    return price_delta - fees


def calculate_taker_fee(quantity: float, exchange_rate: float) -> float:
    ''' Calculates the fee when making a coinbase pro taker order

    A taker order is an order that is executed immediately and as such,
    has a higher fee structure.

    TODO: update this function to pull the fee rate down dynamically from
    coinbase.pro.  Fee is reduced as transaction volume goes up.
    '''
    FEE_RATE = 0.0025  # 0.25%
    price = quantity * exchange_rate
    return FEE_RATE * price


def pair_transaction(
    sell_transaction: Transaction,
    pending_transactions: PVector
) -> PVector:
    ''' Match pending paired transactions using a FIFO algorithm

    Cryptocurrency purchases are turned into pending paired transactions.
    When cryptocurrency is sold, the oldest purchases are paired with the
    newest sales to calculate capital gains.  Transaction pairs are recorded
    in transaction_history.csv.
    '''
    remaining_quantity_sold = sell_transaction.quantity
    remaining_pending_transactions: List[Transaction] = []
    for buy_transaction in pending_transactions:
        is_complete_match = (
            remaining_quantity_sold >= 0 and
            remaining_quantity_sold >= buy_transaction.quantity
        )
        is_partial_match = (
            remaining_quantity_sold >= 0 and
            remaining_quantity_sold < buy_transaction.quantity
        )
        if is_complete_match:
            remaining_quantity_sold -= buy_transaction.quantity
            quantity_paired = buy_transaction.quantity
            paired_transaction = PairedTransactions(
                buy=buy_transaction,
                sell=sell_transaction.set('quantity', quantity_paired)
            )
            record_paired_transaction('transaction_history.csv', paired_transaction)
        elif is_partial_match:
            quantity_paired = remaining_quantity_sold
            remaining_quantity_sold -= buy_transaction.quantity
            pending_quantity_remaining = abs(remaining_quantity_sold)
            remaining_pending_transactions.append(
                buy_transaction.set('quantity', pending_quantity_remaining)
            )

            paired_transaction = PairedTransactions(
                buy=buy_transaction.set('quantity', quantity_paired),
                sell=sell_transaction.set('quantity', quantity_paired)
            )
            record_paired_transaction('transaction_history.csv', paired_transaction)
        else:
            remaining_pending_transactions.append(buy_transaction)
    return pvector(remaining_pending_transactions)
