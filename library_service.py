"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books
)

def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """
    Add a new book to the catalog.
    Implements R1: Book Catalog Management
    
    Args:
        title: Book title (max 200 chars)
        author: Book author (max 100 chars)
        isbn: 13-digit ISBN
        total_copies: Number of copies (positive integer)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Input validation
    if not title or not title.strip():
        return False, "Title is required."
    
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    
    if not author or not author.strip():
        return False, "Author is required."
    
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    
    if len(isbn) != 13:
        return False, "ISBN must be exactly 13 digits."
    
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."
    
    # Check for duplicate ISBN
    existing = get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."
    
    # Insert new book
    success = insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."

def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Allow a patron to borrow a book.
    Implements R3 as per requirements  
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to borrow
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check if book exists and is available
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."
    
    # Check patron's current borrowed books count
    current_borrowed = get_patron_borrow_count(patron_id)
    
    if current_borrowed > 5:
        return False, "You have reached the maximum borrowing limit of 5 books."
    
    # Create borrow record
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    # Insert borrow record and update availability
    borrow_success = insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    if not borrow_success:
        return False, "Database error occurred while creating borrow record."
    
    availability_success = update_book_availability(book_id, -1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'


def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    if not (isinstance(patron_id, str) and patron_id.isdigit() and len(patron_id) == 6):
        return False, "Invalid patron ID (must be 6 digits)."

    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."

    now = datetime.now()
    updated = update_borrow_record_return_date(patron_id, book_id, now)
    if not updated:
        return False, "No active borrow record for this patron and book."

    # Update availability
    if not update_book_availability(book_id, +1):
        return False, "Could not update book availability."

    fee_info = calculate_late_fee_for_book(patron_id, book_id)
    try:
        fee_amt = float(fee_info.get("fee_amount", 0.0))
    except Exception:
        fee_amt = 0.0

    fee_txt = f" Late fee: ${fee_amt:.2f}." if fee_amt > 0 else " No late fee."
    return True, f'Returned "{book.get("title", "")}" on {now.strftime("%Y-%m-%d")}.{fee_txt}'



def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    if not (isinstance(patron_id, str) and patron_id.isdigit() and len(patron_id) == 6):
        return {'fee_amount': 0.00, 'days_overdue': 0, 'status': 'Invalid patron ID'}
    if not get_book_by_id(book_id):
        return {'fee_amount': 0.00, 'days_overdue': 0, 'status': 'Book not found'}

    return {
        'fee_amount': 0.00,
        'days_overdue': 0,
        'status': 'Late fee calculation unavailable (missing accessor)'
    }


def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    q = (search_term or "").strip()
    st = (search_type or "").strip().lower()
    if not q or st not in {"title", "author", "isbn"}:
        return []

    if st == "isbn":
        normalized = q.replace("-", "").replace(" ", "")
        book = get_book_by_isbn(normalized)
        if book:
            return [book]

        books = get_all_books() or []
        return [
            b for b in books
            if (b.get("isbn") or "").replace("-", "").replace(" ", "") == normalized
        ]

    books = get_all_books() or []
    key = st  # 'title' or 'author'
    ql = q.lower()
    return [b for b in books if ql in (b.get(key) or "").lower()]


def get_patron_status_report(patron_id: str) -> Dict:
    report: Dict = {
        'patron_id': patron_id,
        'borrowed_count': 0,
        'total_late_fees': 0.00,
        'current_loans': [],
        'history': [],
        'notes': 'OK'
    }

    if not (isinstance(patron_id, str) and patron_id.isdigit() and len(patron_id) == 6):
        report['notes'] = 'Invalid patron ID'
        return report

    try:
        report['borrowed_count'] = int(get_patron_borrow_count(patron_id) or 0)
    except Exception:
        report['notes'] = 'Unable to fetch borrow count'
        return report

    report['notes'] = 'Loan/fee details unavailable with current DB helpers'
    return report
