import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from library_service import return_book_by_patron

def test_return_rejects_invalid_patron_id():
    success, message = return_book_by_patron("12AB34", 1)
    assert success == False
    assert "digits" in message.lower()

def test_return_rejects_unknown_book_id():
    success, message = return_book_by_patron("444444", 1122334455)
    assert success == False
    assert "not found" in message.lower()

def test_return_rejects_if_not_borrowed_by_that_patron():
    success, message = return_book_by_patron("555555", 1)
    assert success == True
    assert "not borrowed" in message.lower()

def test_return_if_borrowed_or_not_borroweds():
    success, message = return_book_by_patron("123456", 1)
    assert success in (True, False)
    if success:
        assert "return" in message.lower()
    else:
        assert "not borrowed" in message.lower() 