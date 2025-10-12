import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from library_service import borrow_book_by_patron

def test_borrow_rejects_invalid_patron_id_not_6_digits():
    success, message = borrow_book_by_patron("12345", 99999999)
    assert success == False
    assert "6" in message or "digits" in message.lower()

def test_borrow_rejects_non_digit_patron_id():
    success, message = borrow_book_by_patron("ABCDEF", 99999999)
    assert success == False
    assert "digits" in message.lower()

def test_borrow_rejects_when_book_id_not_found():
    success, message = borrow_book_by_patron("123456", 987654321)
    assert success == False
    assert "not found" in message.lower() or "invalid" in message.lower()

def test_borrow_rejects_when_book_unavailable_or_zero_copies():
    success, message = borrow_book_by_patron("222222", 0)
    assert success == False
    assert ("not available" in message.lower()) or ("not found" in message.lower()) or ("invalid" in message.lower())

def test_borrow_success_smoke_assuming_seeded_book_id_1():
    success, message = borrow_book_by_patron("333333", 1)
    assert success == (True, False)
    if success:
        assert "borrow" in message.lower() or "success" in message.lower()
    else:
        assert "not found" in message.lower() or "invalid" in message.lower()
