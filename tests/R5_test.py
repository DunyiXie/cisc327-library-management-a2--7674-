import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.library_service import calculate_late_fee_for_book

def test_fee_for_book_returns_dict_type():
    resp = calculate_late_fee_for_book("101010", 1)
    assert isinstance(resp, dict)
    assert bool(resp) == True

def test_fee_for_book_has_required_keys():
    resp = calculate_late_fee_for_book("202020", 2)
    keys = set(resp.keys())
    assert "days_overdue" in keys
    assert "fee_amount" in keys

def test_fee_for_book_days_overdue_is_non_negative():
    resp = calculate_late_fee_for_book("303030", 3)
    assert resp.get("days_overdue", 0) >= 0

def test_fee_for_book_fee_amount_is_numeric_or_numeric_string():
    resp = calculate_late_fee_for_book("404040", 4)
    try:
        float(resp.get("fee_amount", 0))
        numeric = True
    except Exception:
        numeric = False
    assert numeric == True

def test_fee_for_book_handles_nonexistent_pair_gracefully():
    resp = calculate_late_fee_for_book("999000", 123456789)
    assert isinstance(resp, dict)
    ok = ("error" in resp) or ("fee_amount" in resp)
    assert ok == True
