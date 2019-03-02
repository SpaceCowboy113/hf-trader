import csv
from typing import List, Tuple  # noqa: F401

from pyrsistent import PRecord, PVector, field, pvector


class Transaction(PRecord):
    label = field(type=str, mandatory=True)
    quantity = field(type=float, mandatory=False)
    exchange_rate = field(type=float, mandatory=False)
    timestamp = field(type=str, mandatory=False)
    fees = field(type=float, mandatory=False)

# TODO: rename to paired transactions to avoid confusion with the term "Match"

# TODO: Validate that labels are same with invariant


def must_have_same_label(transactions) -> Tuple[bool, str]:
    return transactions.buy.label == transactions.sell.label, 'transactions must have same label'


class PairedTransactions(PRecord):
    __invariant__ = must_have_same_label
    buy = field(type=Transaction, mandatory=True)
    sell = field(type=Transaction, mandatory=True)


# TODO: Renamed to record_transaction_pair


def record_paired_transaction(
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
            paired_transactions.buy.timestamp,
            paired_transactions.buy.fees,
            paired_transactions.sell.quantity,
            paired_transactions.sell.exchange_rate,
            paired_transactions.sell.timestamp,
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
                    timestamp=row[3],
                    fees=float(row[4]),
                ),
                sell=Transaction(
                    label=row[0],
                    quantity=float(row[5]),
                    exchange_rate=float(row[6]),
                    timestamp=row[7],
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
    FEE_RATE = 0.003  # 0.30%
    price = quantity * exchange_rate
    return FEE_RATE * price


def pair_transaction(
    sell_transaction: Transaction,
    pending_transactions: PVector
) -> PVector:
    """ Match pending transactions using a FIFO algorithm
    """
    remaining_quantity_sold = sell_transaction.quantity
    remaining_pending_transactions = []  # type: List[Transaction]
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
