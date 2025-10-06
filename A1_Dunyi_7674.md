# A1_Dunyi_7674 — Project Implementation Status

**Name:** Dunyi Xie 
**Student ID:** 20437674
**Course:** CISC/CMPE 327 — Software Quality Assurance  
**Assignment:** A1 — Library Management System  
**Date:** 2025-09-15


## Summary Table (R1–R7)

| Req | Functions | Implementation Status | What’s missing |
|---|---|---|---|
| `add_book_to_catalog` (R1) | **Completed** | None |
| `book_catalog_display` (R2) | **Completed** |
| `borrow_book_by_patron` (R3) | **Completed** | None |
| `return_book_by_patron` (R4) | **Missing** | Explicitly returns `False, "Book return functionality is not yet implemented."` Implement: verify the patron actually borrowed the book; set return date (e.g., `update_borrow_record_return_date`); increment availability; compute and surface any late fee. |
| `calculate_late_fee_for_book` (R5) | **Missing** | Marked `TODO` (R5). Implement per spec: 14-day grace; then $0.50/day for first 7 overdue days, then $1.00/day; **cap at $15.00**; return a dict including `days_overdue` and a 2-decimal `fee_amount`. (Optionally factor a pure helper `calculate_late_fee(borrow_date, today)` to keep math testable.) |
| `search_books_in_catalog` (R6) | **Missing** | Marked `TODO` and currently returns `[]`. Implement: partial, case-insensitive match for `title`/`author`; **exact** match for `isbn`; validate `type ∈ {title, author, isbn}`; return rows with `{id, title, author, isbn, available, total, borrow_action_enabled}` (borrow enabled only if `available > 0`). |
| `get_patron_status_report` (R7) | **Missing** | Marked `TODO` and returns `{}`. Implement summary: `currently_borrowed_count`, `current_with_due_dates` (list), `history_count`, and `total_fees_owed` (use R5 for fees). |
| *(R2 helper)* `prepare_catalog_rows(books)` | **Missing** | Not currently defined, but recommended: a pure helper that formats catalog items into `{id, title, author, isbn, available, total, borrow_action_enabled}`. This keeps view logic testable and shared by catalog/search. |


## Test Scripts
| Req | Test Script File | Coverage Summary |
|---|---|---|
| R1 `add_book_to_catalog` | `R1_Test.py` | Tests book addition success, ISBN length and digit validation, title validity, and total copies validation. |
| R2 `book_catalog_display` | *No separate script* | Indirectly verified via other functions; recommend adding display format tests. |
| R3 `borrow_book_by_patron` | `R3_Test.py` | Tests patron ID validation, book existence, availability, borrow limit, and success/failure messages. |
| R4 `return_book_by_patron` | `R4_Test.py` | Tests patron and book validation, not-borrowed rejection, idempotency (double return), and success/failure messages. |
| R5 `calculate_late_fee_for_book` | `R5_Test.py` | Tests late fee calculation type, required fields, overdue days, fee value, and error handling. |
| R6 `search_books_in_catalog` | `R6_Test.py` | Tests search by title/author/ISBN, return type, result format, and field completeness. |
| R7 `get_patron_status_report` | `R7_Test.py` | Tests report type, required fields, borrow/history counts, and fee field validity. |