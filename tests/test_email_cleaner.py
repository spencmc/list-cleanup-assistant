# ============================================================
# tests/test_email_cleaner.py
# ============================================================

import pandas as pd
import pytest
from cleaners.email_cleaner import clean_emails, is_valid_email_syntax, get_email_domain


def test_valid_email_syntax():
    assert is_valid_email_syntax("john.smith@acme.com") == True
    assert is_valid_email_syntax("mary@company.co.uk") == True


def test_invalid_email_syntax():
    assert is_valid_email_syntax("notanemail") == False
    assert is_valid_email_syntax("@nodomain.com") == False
    assert is_valid_email_syntax("missing@") == False
    assert is_valid_email_syntax("") == False
    assert is_valid_email_syntax(None) == False


def test_get_email_domain():
    assert get_email_domain("john@acme.com") == "acme.com"
    assert get_email_domain("mary@gmail.com") == "gmail.com"
    assert get_email_domain("bad_email") == ""


def test_clean_emails_normalizes_to_lowercase():
    df = pd.DataFrame({"Email": ["JOHN@ACME.COM", "Mary@Gmail.Com"]})
    result = clean_emails(df)
    assert result["Email"].iloc[0] == "john@acme.com"
    assert result["Email"].iloc[1] == "mary@gmail.com"


def test_clean_emails_flags_blanks():
    df = pd.DataFrame({"Email": ["", None, "valid@acme.com"]})
    result = clean_emails(df)
    assert result["email_flag_blank"].iloc[0] == True
    assert result["email_flag_blank"].iloc[1] == True
    assert result["email_flag_blank"].iloc[2] == False


def test_clean_emails_flags_duplicates():
    df = pd.DataFrame({"Email": ["john@acme.com", "john@acme.com", "mary@acme.com"]})
    result = clean_emails(df)
    assert result["email_flag_duplicate"].iloc[0] == False
    assert result["email_flag_duplicate"].iloc[1] == True
    assert result["email_flag_duplicate"].iloc[2] == False


def test_clean_emails_flags_disposable():
    df = pd.DataFrame({"Email": ["test@mailinator.com", "real@acme.com"]})
    result = clean_emails(df)
    assert result["email_flag_disposable"].iloc[0] == True
    assert result["email_flag_disposable"].iloc[1] == False


def test_clean_emails_flags_personal():
    df = pd.DataFrame({"Email": ["user@gmail.com", "user@acme.com"]})
    result = clean_emails(df)
    assert result["email_flag_personal"].iloc[0] == True
    assert result["email_flag_personal"].iloc[1] == False
