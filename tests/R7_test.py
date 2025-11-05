import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.library_service import get_patron_status_report

def test_status_returns_dict_type():
    report = get_patron_status_report("700001")
    assert isinstance(report, dict)
    assert report == report 


def test_status_report_has_expected_keys():
    report = get_patron_status_report("700002")
    keys = set(report.keys())
    assert "patron_id" in keys
    assert "borrowed_count" in keys
    assert "current_loans" in keys
    assert "history" in keys
    assert "notes" in keys

def test_status_current_with_due_dates_is_list_if_present():
    report = get_patron_status_report("700003")
    if "current_with_due_dates" in report:
        assert isinstance(report["current_with_due_dates"], list)

def test_get_empty_patron_id():
    result = get_patron_status_report(None)
    assert isinstance(result, dict)
    msg = str(result.get('empty') or result.get('message') or result.get('notes', ''))
    assert msg.strip() != ""
    assert ("6 digits" in msg) or ("invalid" in msg.lower()) or ("empty" in msg.lower())
