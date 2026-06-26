# ============================================================
# tests/test_name_cleaner.py
# ============================================================

import pandas as pd
import pytest
from cleaners.name_cleaner import clean_names, smart_title_case, is_suspicious


def test_smart_title_case_basic():
    assert smart_title_case("JOHN") == "John"
    assert smart_title_case("mARY") == "Mary"
    assert smart_title_case("john smith") == "John Smith"


def test_smart_title_case_obrien():
    assert smart_title_case("o'brien") == "O'Brien"


def test_smart_title_case_mc():
    assert smart_title_case("mcdonald") == "McDonald"


def test_smart_title_case_empty():
    assert smart_title_case("") == ""
    assert smart_title_case(None) == None


def test_is_suspicious_true():
    assert is_suspicious("test", ["test", "n/a", "unknown"]) == True
    assert is_suspicious("N/A", ["test", "n/a", "unknown"]) == True


def test_is_suspicious_false():
    assert is_suspicious("John", ["test", "n/a", "unknown"]) == False
    assert is_suspicious(None, ["test"]) == False


def test_clean_names_title_case():
    df = pd.DataFrame({
        "First Name": ["JOHN", "mARY"],
        "Last Name": ["SMITH", "jones"]
    })
    result = clean_names(df)
    assert result["First Name"].iloc[0] == "John"
    assert result["Last Name"].iloc[1] == "Jones"


def test_clean_names_strips_whitespace():
    df = pd.DataFrame({
        "First Name": ["  John  "],
        "Last Name": ["  Smith  "]
    })
    result = clean_names(df)
    assert result["First Name"].iloc[0] == "John"
    assert result["Last Name"].iloc[0] == "Smith"


def test_clean_names_flags_suspicious():
    df = pd.DataFrame({
        "First Name": ["test", "John"],
        "Last Name": ["Smith", "Doe"]
    })
    result = clean_names(df)
    assert result["first_name_flag_suspicious"].iloc[0] == True
    assert result["first_name_flag_suspicious"].iloc[1] == False


def test_clean_names_preserves_original():
    df = pd.DataFrame({
        "First Name": ["JOHN"],
        "Last Name": ["SMITH"]
    })
    result = clean_names(df)
    assert result["first_name_original"].iloc[0] == "JOHN"
    assert result["last_name_original"].iloc[0] == "SMITH"
