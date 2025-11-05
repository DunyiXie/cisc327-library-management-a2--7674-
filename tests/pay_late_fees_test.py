import sys
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
