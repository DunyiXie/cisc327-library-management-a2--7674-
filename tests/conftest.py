import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from unittest.mock import Mock
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]  
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services import library_service as ls 
@pytest.fixture
def stub_book_found(monkeypatch):
    """Stub get_book_by_id to return a minimal book record."""
    monkeypatch.setattr(ls, "get_book_by_id",
                        lambda book_id: {"id": book_id, "title": "Clean Code"})

@pytest.fixture
def stub_book_missing(monkeypatch):
    """Stub get_book_by_id to simulate a missing book."""
    monkeypatch.setattr(ls, "get_book_by_id", lambda book_id: None)

@pytest.fixture
def stub_fee():
    """Factory to stub calculate_late_fee_for_book with a chosen fee."""
    def _factory(monkeypatch, amt=0.0):
        def _calc(_pid, _bid):
            return {"fee_amount": amt, "days_overdue": 0, "status": "ok"}
        monkeypatch.setattr(ls, "calculate_late_fee_for_book", _calc)
    return _factory

@pytest.fixture
def gateway_mock():
    """
    Mock of the external payment gateway.
    process_payment(...) -> (success, transaction_id, message)
    refund_payment(txn_id, amount) -> (success, message)
    """
    return Mock()
