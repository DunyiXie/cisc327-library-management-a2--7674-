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

