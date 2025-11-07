import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services import library_service as ls

def test_refund_success(gateway_mock):
    gateway_mock.refund_payment.return_value = (True, "OK")
    ok, msg = ls.refund_late_fee_payment("txn_abc", 4.50, payment_gateway=gateway_mock)
    gateway_mock.refund_payment.assert_called_once_with("txn_abc", 4.50)
    assert ok is True
    assert msg == "OK"


@pytest.mark.parametrize("bad_txn", ["", None, "abc", "txn", "tx_"])
def test_refund_invalid_transaction_id_rejected(bad_txn, gateway_mock):
    ok, msg = ls.refund_late_fee_payment(bad_txn, 3.00, payment_gateway=gateway_mock)
    gateway_mock.refund_payment.assert_not_called()
    assert ok is False
    assert "Invalid transaction ID" in msg


@pytest.mark.parametrize("bad_amt", [0.0, -1.0])
def test_refund_nonpositive_amount_rejected(bad_amt, gateway_mock):
    ok, msg = ls.refund_late_fee_payment("txn_123", bad_amt, payment_gateway=gateway_mock)
    gateway_mock.refund_payment.assert_not_called()
    assert ok is False
    assert "greater than 0" in msg


def test_refund_exceeds_max_rejected(gateway_mock):
    ok, msg = ls.refund_late_fee_payment("txn_123", 15.01, payment_gateway=gateway_mock)
    gateway_mock.refund_payment.assert_not_called()
    assert ok is False
    assert "exceeds maximum late fee" in msg


def test_refund_gateway_failure(gateway_mock):
    gateway_mock.refund_payment.return_value = (False, "declined")
    ok, msg = ls.refund_late_fee_payment("txn_123", 2.00, payment_gateway=gateway_mock)
    gateway_mock.refund_payment.assert_called_once_with("txn_123", 2.00)
    assert ok is False
    assert msg.startswith("Refund failed:")


def test_refund_gateway_exception(gateway_mock):
    gateway_mock.refund_payment.side_effect = RuntimeError("timeout")
    ok, msg = ls.refund_late_fee_payment("txn_123", 2.00, payment_gateway=gateway_mock)
    gateway_mock.refund_payment.assert_called_once_with("txn_123", 2.00)
    assert ok is False
    assert "Refund processing error" in msg

def test_refund_boundary_amount_exact_max(gateway_mock):
    gateway_mock.refund_payment.return_value = (True, "OK")
    ok, msg = ls.refund_late_fee_payment("txn_999", 15.00, payment_gateway=gateway_mock)
    gateway_mock.refund_payment.assert_called_once_with("txn_999", 15.00)
    assert ok is True and msg == "OK"


def test_refund_uses_default_gateway_when_none(monkeypatch):
    class DummyGateway:
        def refund_payment(self, transaction_id, amount):
            return True, "OK-AUTO"
    monkeypatch.setattr(ls, "PaymentGateway", DummyGateway)
    ok, msg = ls.refund_late_fee_payment("txn_auto", 1.00, payment_gateway=None)
    assert ok is True and msg == "OK-AUTO"


def test_refund_rejected_message_bubbled(gateway_mock):
    gateway_mock.refund_payment.return_value = (False, "issuer_declined")
    ok, msg = ls.refund_late_fee_payment("txn_decl", 2.00, payment_gateway=gateway_mock)
    assert ok is False and msg.startswith("Refund failed:")


@pytest.mark.parametrize("weird_whitespace", ["  ", "\n", "\t", "   \n"])
def test_refund_transaction_id_whitespace_only(weird_whitespace, gateway_mock):
    ok, msg = ls.refund_late_fee_payment(weird_whitespace, 1.00, payment_gateway=gateway_mock)
    gateway_mock.refund_payment.assert_not_called()
    assert ok is False
    assert "Invalid transaction ID" in msg


@pytest.mark.parametrize("amt", [0.0001, 0.009, 1]) 
def test_refund_amount_normalization_and_success(gateway_mock, amt):
    gateway_mock.refund_payment.return_value = (True, "OK")
    ok, msg = ls.refund_late_fee_payment("txn_norm", amt, payment_gateway=gateway_mock)
    gateway_mock.refund_payment.assert_called_once()
    assert ok is True and msg.startswith("OK")


def test_refund_amount_high_precision_rounding(gateway_mock):
    gateway_mock.refund_payment.return_value = (True, "OK")
    ok, msg = ls.refund_late_fee_payment("txn_hp", 2.999, payment_gateway=gateway_mock)
    gateway_mock.refund_payment.assert_called_once()
    assert ok is True and msg == "OK"


def test_refund_default_gateway_path_and_decline(monkeypatch):
    class DummyGateway:
        def refund_payment(self, transaction_id, amount):
            return (False, f"issuer_declined:{transaction_id}:{amount}")
    monkeypatch.setattr(ls, "PaymentGateway", DummyGateway)
    ok, msg = ls.refund_late_fee_payment("txn_auto_decl", 2.50, payment_gateway=None)
    assert ok is False and msg.startswith("Refund failed:")


def test_refund_default_gateway_exception_includes_tx(monkeypatch):
    class DummyGateway:
        def refund_payment(self, transaction_id, amount):
            raise RuntimeError(f"timeout for {transaction_id}")
    monkeypatch.setattr(ls, "PaymentGateway", DummyGateway)
    ok, msg = ls.refund_late_fee_payment("txn_timeout", 1.00, payment_gateway=None)
    assert ok is False and ("timeout" in msg or "processing error" in msg.lower())


@pytest.mark.parametrize("too_large", [15.0001, 99, 1000.0])
def test_refund_amounts_over_max_rejected(gateway_mock, too_large):
    ok, msg = ls.refund_late_fee_payment("txn_big", too_large, payment_gateway=gateway_mock)
    gateway_mock.refund_payment.assert_not_called()
    assert ok is False and "exceeds maximum late fee" in msg
