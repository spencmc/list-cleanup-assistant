# ============================================================
# tests/test_geo_cleaner.py
# ============================================================

import pandas as pd
import pytest
from cleaners.geo_cleaner import clean_geo, normalize_value


def test_normalize_usa_variants():
    lookup = {"US": "United States", "USA": "United States", "United States of America": "United States"}
    assert normalize_value("US", lookup)[0] == "United States"
    assert normalize_value("USA", lookup)[0] == "United States"
    assert normalize_value("United States of America", lookup)[0] == "United States"


def test_normalize_uk_variants():
    lookup = {"UK": "United Kingdom", "England": "United Kingdom"}
    assert normalize_value("UK", lookup)[0] == "United Kingdom"
    assert normalize_value("England", lookup)[0] == "United Kingdom"


def test_normalize_case_insensitive():
    lookup = {"USA": "United States"}
    assert normalize_value("usa", lookup)[0] == "United States"


def test_normalize_unknown_value():
    lookup = {"US": "United States"}
    result, changed = normalize_value("Narnia", lookup)
    assert result == "Narnia"
    assert changed == False


def test_normalize_empty_value():
    lookup = {"US": "United States"}
    result, changed = normalize_value("", lookup)
    assert changed == False


def test_clean_geo_normalizes_country():
    df = pd.DataFrame({"Country": ["USA", "UK", "United States of America"]})
    result = clean_geo(df)
    assert result["Country"].iloc[0] == "United States"
    assert result["Country"].iloc[1] == "United Kingdom"
    assert result["Country"].iloc[2] == "United States"


def test_clean_geo_flags_changed():
    df = pd.DataFrame({"Country": ["USA", "United States"]})
    result = clean_geo(df)
    assert result["country_flag_changed"].iloc[0] == True
    assert result["country_flag_changed"].iloc[1] == False


def test_clean_geo_normalizes_state():
    df = pd.DataFrame({"Country": ["United States"], "State": ["CA"]})
    result = clean_geo(df)
    assert result["State"].iloc[0] == "California"


def test_clean_geo_preserves_original():
    df = pd.DataFrame({"Country": ["USA"], "State": ["CA"]})
    result = clean_geo(df)
    assert result["country_original"].iloc[0] == "USA"
    assert result["state_original"].iloc[0] == "CA"
