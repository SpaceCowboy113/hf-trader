import csv

from pyrsistent import PRecord, PVector, field, pvector


class Transaction(PRecord):
    label = field(type=str)

    # Purchase info
    quantity_purchased = field(type=float)
    purchase_exchange_rate = field(type=float)
    purchase_timestamp = field(type=str)
    purchase_fees = field(type=float)

    # Selling info
    quantity_sold = field(type=float)
    selling_exchange_rate = field(type=float)
    selling_timestamp = field(type=str)
    selling_fees = field(type=float)


def record_transaction(path: str, transaction: Transaction) -> None:
    with open(path, 'a', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow([
            transaction.label,
            transaction.quantity_purchased,
            transaction.purchase_exchange_rate,
            transaction.purchase_timestamp,
            transaction.purchase_fees,
            transaction.quantity_sold,
            transaction.selling_exchange_rate,
            transaction.selling_timestamp,
            transaction.selling_fees,
            calculate_capital_gains(transaction)
        ])


def open_transaction_history(path: str) -> PVector:
    transactions = []
    with open(path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            transaction = Transaction(
                label=row[0],
                quantity_purchased=float(row[1]),
                purchase_exchange_rate=float(row[2]),
                purchase_timestamp=row[3],
                purchase_fees=float(row[4]),
                quantity_sold=float(row[5]),
                selling_exchange_rate=float(row[6]),
                selling_timestamp=row[7],
                selling_fees=float(row[8])
            )
            transactions.append(transaction)
    return pvector(transactions)


def calculate_capital_gains(transaction: Transaction) -> float:
    purchase_price = transaction.quantity_purchased * transaction.purchase_exchange_rate
    selling_price = transaction.quantity_sold * transaction.selling_exchange_rate
    price_delta = selling_price - purchase_price
    fees = transaction.purchase_fees + transaction.selling_fees
    return price_delta - fees


def calculate_taker_fee(quantity: float, exchange_rate: float) -> float:
    FEE_RATE = 0.003  # 0.30%
    price = quantity * exchange_rate
    return FEE_RATE * price


# transaction = Transaction(
#     label='BTC-USD',
#     quantity_purchased=1.0,
#     purchase_exchange_rate=3000.0,
#     purchase_timestamp='0:00',
#     purchase_fees=calculate_taker_fee(1.0, 3000.0),
#     quantity_sold=1.0,
#     selling_exchange_rate=3050.0,
#     selling_timestamp='0:01',
#     selling_fees=calculate_taker_fee(1.0, 3050.0),
# )

# record_transaction('transaction_history.csv', transaction)
# transactions = open_transaction_history('transaction_history.csv')

# print(transactions)
