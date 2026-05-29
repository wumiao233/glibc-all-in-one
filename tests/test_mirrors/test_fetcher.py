from glibc_aio.mirrors.fetcher import parse_deb_listing

SAMPLE_HTML = b'<a href="libc6_2.35-0ubuntu3.8_amd64.deb">...</a>\n<a href="libc6_2.35-0ubuntu3.8_i386.deb">...</a>\n<a href="libc6-dbg_2.35-0ubuntu3.8_amd64.deb">...</a>'


def test_parse_deb_listing_extracts_libc6_only():
    result = parse_deb_listing(SAMPLE_HTML)
    assert "2.35-0ubuntu3.8_amd64" in result
    assert "2.35-0ubuntu3.8_i386" in result
    assert len(result) == 2


def test_parse_deb_listing_dedup_sorted():
    html = b'<a href="libc6_2.35-0ubuntu3_amd64.deb">x</a>' * 3
    result = parse_deb_listing(html)
    assert result == ["2.35-0ubuntu3_amd64"]
