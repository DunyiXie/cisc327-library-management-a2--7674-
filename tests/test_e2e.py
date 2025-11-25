"""
End-to-end browser tests for the Library Management System.

Assumptions:
- App is running at http://localhost:5000 (see BASE_URL below).
- Add-book page is at /add_book (matches your add_book.html form).
- Catalog page is at /catalog and shows a row for each book.
- Each row has a "Borrow" link/button for that book.
- The borrow form has a patron id field (named "patron_id" or similar)
  and shows some success message after borrowing.
"""

import os
import re
import uuid

import pytest

# Try to import Playwright. If not available (e.g. on CI), skip this file.
try:
    from playwright.sync_api import Page, expect
except ImportError:  # pragma: no cover
    pytest.skip(
        "Playwright is not installed; skipping end-to-end browser tests.",
        allow_module_level=True,
    )

# Base URL for the running app
BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:5000")


def _create_unique_book_data() -> dict:
    """Generate a unique book so tests can run repeatedly."""
    suffix = uuid.uuid4().hex[:8]
    return {
        "title": f"E2E Test Book {suffix}",
        "author": "E2E Author",
        "isbn": f"978{suffix[:10]:0<10}",  # pad to 13 digits total
        "copies": "3",
    }


def _add_book_via_ui(page: Page, book_data: dict) -> None:
    """
    Open the Add Book page, fill the form using your add_book.html fields,
    and submit.
    """
    # Go directly to the Add Book page to avoid ambiguous nav links
    page.goto(f"{BASE_URL}/add_book", wait_until="networkidle")

    # Your template uses labels + id/for pairs, so label-based locators are stable
    page.get_by_label("Title").fill(book_data["title"])
    page.get_by_label("Author").fill(book_data["author"])
    page.get_by_label("ISBN").fill(book_data["isbn"])
    page.get_by_label(re.compile(r"Total Copies", re.I)).fill(book_data["copies"])

    # Button text from your template: "Add Book to Catalog"
    page.get_by_role("button", name=re.compile(r"Add Book to Catalog", re.I)).click()


def test_add_new_book_appears_in_catalog(page: Page):
    """
    Flow 1: Add a new book and verify it appears in the catalog.
    """
    book = _create_unique_book_data()

    # Add the book via the UI
    _add_book_via_ui(page, book)

    # After submission, either the app redirects to /catalog or we navigate there
    page.goto(f"{BASE_URL}/catalog", wait_until="networkidle")

    # Check that the new book title appears somewhere on the catalog page
    expect(page.get_by_text(book["title"])).to_be_visible()


def navigate_to_borrow_page(page: Page, book_title: str) -> None:
    """
    From the catalog, find the row containing `book_title`
    and click its Borrow control to go to the borrow page.
    """
    # Go to the catalog page
    page.goto(f"{BASE_URL}/catalog", wait_until="networkidle")

    # Find the table row for this book
    book_row = page.locator("tr", has_text=book_title)
    expect(book_row).to_be_visible()

    # Prefer a Borrow link inside that row
    borrow = book_row.get_by_role("link", name=re.compile(r"Borrow", re.I))
    if borrow.count() == 0:
        # Fallback if it's a button instead of link
        borrow = book_row.get_by_role("button", name=re.compile(r"Borrow", re.I))

    expect(borrow).to_be_visible()
    borrow.first.click()