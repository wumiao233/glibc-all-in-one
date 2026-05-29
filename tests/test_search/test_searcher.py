import tempfile
import os
from glibc_aio.search.searcher import (
    SearchQuery,
    match_version_name,
    load_version_list,
)


def test_match_version_name_exact():
    ids = ["2.35-0ubuntu3.8_amd64", "2.35-0ubuntu3.8_i386", "2.27-3ubuntu1_amd64"]
    result = match_version_name("2.27", ids)
    assert result == ["2.27-3ubuntu1_amd64"]


def test_match_version_name_substring():
    ids = ["2.35-0ubuntu3.8_amd64", "2.35-0ubuntu3.8_i386"]
    result = match_version_name("ubuntu3", ids)
    assert len(result) == 2


def test_match_version_name_no_hit():
    result = match_version_name("9.99", ["2.35-0ubuntu3_amd64"])
    assert result == []


def test_search_query_symbol_hex():
    q = SearchQuery(symbols={"system": 0x4c490})
    assert q.symbols["system"] == 0x4c490


def test_search_query_multi_symbol():
    q = SearchQuery(
        symbols={"system": 0x4c490, "puts": 0x80970},
        tol=5,
    )
    assert len(q.symbols) == 2
    assert q.tol == 5


def test_parse_symbol_arg_hex():
    name, addr = SearchQuery.parse_symbol_arg("system=0x4c490")
    assert name == "system"
    assert addr == 0x4c490


def test_parse_symbol_arg_hex_no_prefix():
    name, addr = SearchQuery.parse_symbol_arg("puts=80970")
    assert name == "puts"
    assert addr == 0x80970


def test_parse_symbol_arg_invalid():
    import pytest
    with pytest.raises(ValueError, match="Invalid format"):
        SearchQuery.parse_symbol_arg("system")


def test_parse_symbol_arg_invalid_addr():
    import pytest
    with pytest.raises(ValueError, match="Invalid address"):
        SearchQuery.parse_symbol_arg("system=xyz")


def test_load_version_list_empty():
    result = load_version_list("/nonexistent/list_file")
    assert result == []


def test_load_version_list_content():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("2.35-0ubuntu3_amd64\n\n2.27-3ubuntu1_i386\n")
        path = f.name
    try:
        result = load_version_list(path)
        assert result == ["2.35-0ubuntu3_amd64", "2.27-3ubuntu1_i386"]
    finally:
        os.unlink(path)
