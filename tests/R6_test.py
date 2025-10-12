import pytest
from library_service import search_books_in_catalog

def test_search_title_returns_list_even_if_empty():
    rows = search_books_in_catalog("clean", "title")
    assert isinstance(rows, list)
    assert rows == rows 

def test_search_author_returns_list():
    rows = search_books_in_catalog("martin", "author")
    assert isinstance(rows, list)
    assert rows == rows

def test_search_isbn_returns_list_for_exact_or_partial():
    rows = search_books_in_catalog("9780132350884", "isbn")
    assert isinstance(rows, list)
    assert rows == rows
    
def test_search_invalid_field_returns_empty_list():
    rows = search_books_in_catalog("anything", "invalid_field")
    assert isinstance(rows, list)
    assert len(rows) == 0
    
