import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from library_service import add_book_to_catalog

def test_add_book_success_sets_available_and_success_message():
    success, message = add_book_to_catalog("R1 Book OK", "Author A", "1111111111115", 3)
    assert success == True
    assert "success" in message.lower()

def test_add_book_rejects_invalid_isbn_length():
    success, message = add_book_to_catalog("Bad ISBN len", "Author", "123456789012", 1)
    assert success == False
    assert "isbn" in message.lower() and "13" in message

def test_add_book_rejects_invalid_title():
    success, message = add_book_to_catalog("", "Author", "1212121212121", 1)
    assert success == False
    assert "title" in message.lower()

def test_add_book_rejects_invalid_total_copies():
    success, message = add_book_to_catalog("Invalid copies", "Author", "1313131313131", 0)
    assert success == False
    assert "cop" in message.lower() 
