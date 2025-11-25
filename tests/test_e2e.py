# tests/test_e2e.py
"""
End-to-end browser tests for the Library Management System.

Assumptions (adjust to your app):
- App is running at http://localhost:5000
- There is a navigation link with text "Add Book"
- The "add book" form uses input names: title, author, isbn, copies
- After adding a book you see a table/listing that contains the book title
- Each book row has a "Borrow" link/button
- The borrow page has an input named patron_id and a submit button
- A successful borrow shows a confirmation message containing "successfully"
"""

import re
import uuid

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:5000"


def _create_unique_book_data():
    """Generate unique book data so tests can run repeatedly."""
    suffix = uuid.uuid4().hex[:8]
    return {
        "title": f"E2E Test Book {suffix}",
        "author": "E2E Author",
        "isbn": f"9780000{suffix[:5]}",
        "copies": "3",
    }


def _add_book_via_ui(page: Page, book_data: dict) -> None:
    """Fill in the Add Book form and submit."""
    # Go to home and then to Add Book page
    page.goto(BASE_URL, wait_until="networkidle")

    # If your app goes directly to catalog, adjust this link selector.
    page.get_by_role("link", name=re.compile("Add Book", re.I)).click()

    # Fill the form – adjust names if your inputs are different
    page.locator("input[name='title']").fill(book_data["title"])
    page.locator("input[name='author']").fill(book_data["author"])
    page.locator("input[name='isbn']").fill(book_data["isbn"])
    page.locator("input[name='copies']").fill(book_data["copies"])

    # Submit the form – adjust button text if needed
    page.get_by_role("button", name=re.compile("Add|Submit|Save", re.I)).click()


@pytest.mark.e2e
def test_add_new_book_appears_in_catalog(page: Page):
    """
    Flow 1: Add a new book and verify it appears in the catalog.
    """
    book = _create_unique_book_data()

    _add_book_via_ui(page, book)

    # After submitting, we expect to see the new book somewhere on the page
    # (e.g., in a table of books).
    expect(page.get_by_text(book["title"])).to_be_visible()


@pytest.mark.e2e
def test_borrow_book_shows_confirmation(page: Page):
    """
    Flow 2: Add a book, borrow it, and verify a confirmation message.

    This is a realistic end-to-end user flow:
    - Add a book
    - Click its Borrow link
    - Enter a patron ID
    - See confirmation
    """
    book = _create_unique_book_data()

    _add_book_via_ui(page, book)

    # Find the row that contains our book and click its "Borrow" link/button.
    # Adjust the locator to match your catalog table structure.
    book_row = page.locator("tr", has_text=book["title"])
    expect(book_row).to_be_visible()

    # Click the Borrow link/button in that row
    book_row.get_by_role("link", name=re.compile("Borrow", re.I)).click()

    # Fill patron ID on the borrow page
    page.locator("input[name='patron_id']").fill("12345")

    # Submit borrow request
    page.get_by_role("button", name=re.compile("Borrow", re.I)).click()

    # Assert that some confirmation text appears
    # Change this to match the actual success message in your app.
    expect(
        page.get_by_text(re.compile("successfully|borrowed", re.I))
    ).to_be_visible()
