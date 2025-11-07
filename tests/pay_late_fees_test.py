import sys
import pytest
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services import library_service as ls

def test_pay_late_fees_success(monkeypatch, stub_book_found, stub_fee, gateway_mock):
    stub_fee(monkeypatch, amt=4.50)
    gateway_mock.process_payment.return_value = (True, "txn_123", "Approved")

    ok, msg, txn = ls.pay_late_fees("700002", 42, payment_gateway=gateway_mock)

    gateway_mock.process_payment.assert_called_once()
    assert ok is True
    assert "Payment successful" in msg
    assert txn == "txn_123"


def test_pay_late_fees_invalid_patron_rejected(gateway_mock, stub_book_found, stub_fee, monkeypatch):
    stub_fee(monkeypatch, amt=3.00)

    ok, msg, txn = ls.pay_late_fees("123", 42, payment_gateway=gateway_mock)

    gateway_mock.process_payment.assert_not_called()
    assert ok is False
    assert "Invalid patron ID" in msg
    assert txn is None


def test_pay_late_fees_zero_fee_skips_gateway(monkeypatch, stub_book_found, stub_fee, gateway_mock):
    stub_fee(monkeypatch, amt=0.0)

    ok, msg, txn = ls.pay_late_fees("700002", 42, payment_gateway=gateway_mock)

    gateway_mock.process_payment.assert_not_called()
    assert ok is False
    assert "No late fees" in msg
    assert txn is None


def test_pay_late_fees_book_not_found(monkeypatch, stub_book_missing, stub_fee, gateway_mock):
    stub_fee(monkeypatch, amt=1.25)

    ok, msg, txn = ls.pay_late_fees("700002", 99, payment_gateway=gateway_mock)

    gateway_mock.process_payment.assert_not_called()
    assert ok is False
    assert "Book not found" in msg
    assert txn is None


def test_pay_late_fees_gateway_declines(monkeypatch, stub_book_found, stub_fee, gateway_mock):
    stub_fee(monkeypatch, amt=2.75)
    gateway_mock.process_payment.return_value = (False, None, "declined")

    ok, msg, txn = ls.pay_late_fees("700002", 42, payment_gateway=gateway_mock)

    gateway_mock.process_payment.assert_called_once()
    assert ok is False
    assert "Payment failed" in msg
    assert txn is None


def test_pay_late_fees_gateway_exception(monkeypatch, stub_book_found, stub_fee, gateway_mock):
    stub_fee(monkeypatch, amt=2.00)
    gateway_mock.process_payment.side_effect = RuntimeError("network down")

    ok, msg, txn = ls.pay_late_fees("700002", 42, payment_gateway=gateway_mock)

    gateway_mock.process_payment.assert_called_once()
    assert ok is False
    assert "Payment processing error" in msg
    assert txn is None


def test_pay_late_fees_fee_info_missing_key(monkeypatch, stub_book_found, gateway_mock):
    monkeypatch.setattr(ls, "calculate_late_fee_for_book",
                        lambda pid, bid: {"days_overdue": 3, "status": "ok"})

    ok, msg, txn = ls.pay_late_fees("700002", 42, payment_gateway=gateway_mock)

    gateway_mock.process_payment.assert_not_called()
    assert ok is False
    assert "Unable to calculate late fees" in msg
    assert txn is None


def test_add_book_insert_5arg_success(monkeypatch):
    monkeypatch.setattr("services.library_service.get_book_by_isbn",
                        lambda isbn: None, raising=True)
    calls = []
    def _insert_capture(*args):
        calls.append(args)
        return True
    monkeypatch.setattr("services.library_service.insert_book",_insert_capture, raising=True)
    ok, msg = ls.add_book_to_catalog("T", "A", "1234567890123", 2)
    assert ok is True
    assert "success" in msg.lower()
    assert len(calls) == 1
    assert len(calls[0]) == 5
    assert calls[0][-2:] == (2, 2)


def test_add_book_insert_4arg_success(monkeypatch):
    monkeypatch.setattr("services.library_service.get_book_by_isbn",
                        lambda isbn: None, raising=True)
    monkeypatch.setattr("services.library_service.insert_book",
                        lambda *args: True, raising=True)
    ok, msg = ls.add_book_to_catalog("T", "A", "1234567890123", 2)
    assert ok is True
    assert "success" in msg.lower()


def test_pay_late_fees_calls_gateway_with_correct_kwargs(monkeypatch, stub_book_found, stub_fee, gateway_mock):
    stub_fee(monkeypatch, amt=3.25)
    gateway_mock.process_payment.return_value = (True, "txn_k1", "Approved")
    ok, msg, txn = ls.pay_late_fees("700002", 101, payment_gateway=gateway_mock)
    assert gateway_mock.process_payment.called
    _, kwargs = gateway_mock.process_payment.call_args
    assert kwargs.get("patron_id") == "700002"
    assert kwargs.get("amount") == 3.25
    assert "Clean Code" in kwargs.get("description", "")  
    assert ok is True and txn == "txn_k1"


def test_pay_late_fees_uses_default_gateway_when_none(monkeypatch, stub_book_found, stub_fee):
    stub_fee(monkeypatch, amt=4.00)
    class DummyGateway:
        def process_payment(self, *, patron_id, amount, description):
            return True, "txn_auto", "OK"
    monkeypatch.setattr(ls, "PaymentGateway", DummyGateway)
    ok, msg, txn = ls.pay_late_fees("700002", 11, payment_gateway=None)
    assert ok is True
    assert "Payment successful" in msg
    assert txn == "txn_auto"


def test_pay_late_fees_fee_info_none(monkeypatch, stub_book_found, gateway_mock):
    monkeypatch.setattr(ls, "calculate_late_fee_for_book", lambda pid, bid: None)
    ok, msg, txn = ls.pay_late_fees("700002", 42, payment_gateway=gateway_mock)
    gateway_mock.process_payment.assert_not_called()
    assert ok is False and "Unable to calculate" in msg and txn is None


def test_pay_late_fees_invalid_book_id_type(monkeypatch, stub_book_found, stub_fee, gateway_mock):
    stub_fee(monkeypatch, amt=2.00)
    gateway_mock.process_payment.return_value = (True, "txn_str_id", "Approved")
    ok, msg, txn = ls.pay_late_fees("700002", "not-an-int", payment_gateway=gateway_mock)
    gateway_mock.process_payment.assert_called_once()
    assert ok is True
    assert txn == "txn_str_id"


def test_pay_late_fees_fee_info_status_not_ok(monkeypatch, stub_book_found, gateway_mock):
    monkeypatch.setattr(ls,"calculate_late_fee_for_book",lambda pid, bid: {"fee_amount": 0.0, "days_overdue": 3, "status": "DB error"}
    )
    ok, msg, txn = ls.pay_late_fees("700002", 1, payment_gateway=gateway_mock)
    gateway_mock.process_payment.assert_not_called()
    assert ok is False
    assert "No late fees" in msg
    assert txn is None


def test_pay_late_fees_negative_fee_rejected(monkeypatch, stub_book_found, gateway_mock):
    monkeypatch.setattr(ls,"calculate_late_fee_for_book",lambda pid, bid: {"fee_amount": -1.0, "days_overdue": 0, "status": "ok"}
    )
    ok, msg, txn = ls.pay_late_fees("700002", 2, payment_gateway=gateway_mock)
    gateway_mock.process_payment.assert_not_called()
    assert ok is False
    assert "No late fees" in msg
    assert txn is None


def test_pay_late_fees_amount_rounds_to_cents(monkeypatch, stub_book_found, gateway_mock):
    monkeypatch.setattr(ls,"calculate_late_fee_for_book",lambda pid, bid: {"fee_amount": 2.345, "days_overdue": 1, "status": "ok"}
    )
    gateway_mock.process_payment.return_value = (True, "txn_rnd", "Approved")
    ok, msg, txn = ls.pay_late_fees("700002", 3, payment_gateway=gateway_mock)
    assert gateway_mock.process_payment.called
    _, kwargs = gateway_mock.process_payment.call_args
    amt = kwargs.get("amount")
    assert abs(float(amt) - 2.35) < 0.005
    assert ok is True and txn == "txn_rnd"


@pytest.mark.parametrize("bad_pid", ["", None, "      ", "00000a", "12345", "1234567"])
def test_pay_late_fees_various_invalid_patrons(monkeypatch, stub_book_found, stub_fee, gateway_mock, bad_pid):
    stub_fee(monkeypatch, amt=1.00)
    ok, msg, txn = ls.pay_late_fees(bad_pid, 5, payment_gateway=gateway_mock)
    gateway_mock.process_payment.assert_not_called()
    assert ok is False
    assert txn is None


def test_add_book_duplicate_isbn(monkeypatch):
    monkeypatch.setattr(ls, "get_book_by_isbn", lambda isbn: {"id": 1})
    ok, msg = ls.add_book_to_catalog("X", "Y", "9781234567890", 1)
    assert ok is False and "already exists" in msg

def test_add_book_author_required_and_length(monkeypatch):
    monkeypatch.setattr(ls, "get_book_by_isbn", lambda isbn: None)
    ok, msg = ls.add_book_to_catalog("Title", "   ", "9781234567890", 1)
    assert ok is False and "Author is required" in msg
    long_author = "A" * 101
    ok, msg = ls.add_book_to_catalog("Title", long_author, "9781234567890", 1)
    assert ok is False and "less than 100 characters" in msg

def test_borrow_unavailable_book(monkeypatch):
    monkeypatch.setattr(ls, "get_book_by_id", lambda bid: {"id": bid, "available_copies": 0})
    ok, msg = ls.borrow_book_by_patron("700002", 1)
    assert ok is False and "not available" in msg

def test_borrow_insert_record_failure(monkeypatch):
    monkeypatch.setattr(ls, "get_book_by_id", lambda bid: {"id": bid, "available_copies": 1, "title": "T"})
    monkeypatch.setattr(ls, "get_patron_borrow_count", lambda pid: 0)
    monkeypatch.setattr(ls, "insert_borrow_record", lambda *a, **k: False)
    ok, msg = ls.borrow_book_by_patron("700002", 1)
    assert ok is False and "creating borrow record" in msg

def test_borrow_update_availability_failure(monkeypatch):
    monkeypatch.setattr(ls, "get_book_by_id", lambda bid: {"id": bid, "available_copies": 1, "title": "T"})
    monkeypatch.setattr(ls, "get_patron_borrow_count", lambda pid: 0)
    monkeypatch.setattr(ls, "insert_borrow_record", lambda *a, **k: True)
    monkeypatch.setattr(ls, "update_book_availability", lambda *a, **k: False)
    ok, msg = ls.borrow_book_by_patron("700002", 1)
    assert ok is False and "updating book availability" in msg


def test_return_no_active_record(monkeypatch):
    monkeypatch.setattr(ls, "get_book_by_id", lambda bid: {"id": bid, "title": "T"})
    monkeypatch.setattr(ls, "update_borrow_record_return_date", lambda *a, **k: False)
    ok, msg = ls.return_book_by_patron("700002", 1)
    assert ok is False and "No active borrow record" in msg

def test_return_update_availability_failure(monkeypatch):
    monkeypatch.setattr(ls, "get_book_by_id", lambda bid: {"id": bid, "title": "T"})
    monkeypatch.setattr(ls, "update_borrow_record_return_date", lambda *a, **k: True)
    monkeypatch.setattr(ls, "update_book_availability", lambda *a, **k: False)
    ok, msg = ls.return_book_by_patron("700002", 1)
    assert ok is False and "update book availability" in msg

def test_return_fee_amount_parse_exception_falls_back_zero(monkeypatch):
    monkeypatch.setattr(ls, "get_book_by_id", lambda bid: {"id": bid, "title": "T"})
    monkeypatch.setattr(ls, "update_borrow_record_return_date", lambda *a, **k: True)
    monkeypatch.setattr(ls, "update_book_availability", lambda *a, **k: True)
    monkeypatch.setattr(ls, "calculate_late_fee_for_book", lambda pid, bid: {"fee_amount": object()})
    ok, msg = ls.return_book_by_patron("700002", 1)
    assert ok is True and " No late fee." in msg
    monkeypatch.setattr(ls, "get_book_by_id", lambda bid: None)
    out = ls.calculate_late_fee_for_book("700002", 9)
    assert out["status"] == "Book not found"

def test_search_isbn_miss_fallback_list_scan(monkeypatch):
    monkeypatch.setattr(ls, "get_book_by_isbn", lambda normalized: None)
    monkeypatch.setattr(ls, "get_all_books", lambda: [
        {"id": 1, "isbn": "9780132350884", "title": "Clean Code"},
        {"id": 2, "isbn": "9780596007126", "title": "Head First Design Patterns"},
    ])
    out = ls.search_books_in_catalog("978-0132350884", "isbn")
    assert len(out) == 1 and out[0]["title"] == "Clean Code"

def test_status_report_borrow_count_exception(monkeypatch):
    monkeypatch.setattr(ls, "get_patron_borrow_count", lambda pid: (_ for _ in ()).throw(RuntimeError("db down")))
    out = ls.get_patron_status_report("700002")
    assert out["notes"] == "Unable to fetch borrow count"