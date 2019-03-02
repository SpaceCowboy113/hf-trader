import pytest  # noqa: F401
from q_records import QModelOutput
from q_learning_model import choose_best_action
from trading_record import TradingAction


def test_choose_best_action():
    hold_output = QModelOutput(buy=1.0, sell=2.0, hold=3.0)
    assert choose_best_action(hold_output) == TradingAction(order='hold', amount=1)
    buy_output = QModelOutput(buy=3.0, sell=2.0, hold=-1.0)
    assert choose_best_action(buy_output) == TradingAction(order='buy', amount=1)
    sell_output = QModelOutput(buy=1.0, sell=5.0, hold=3.0)
    assert choose_best_action(sell_output) == TradingAction(order='sell', amount=1)