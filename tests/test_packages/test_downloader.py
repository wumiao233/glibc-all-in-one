from glibc_aio.packages.downloader import build_deb_url, resolve_mirror_order


def test_build_deb_url_libc():
    url = build_deb_url("http://example.com/glibc", "libc6", "2.35-0ubuntu3_amd64")
    assert url == "http://example.com/glibc/libc6_2.35-0ubuntu3_amd64.deb"


def test_build_deb_url_dbg():
    url = build_deb_url("http://example.com/glibc", "libc6-dbg", "2.35-0ubuntu3_amd64")
    assert url == "http://example.com/glibc/libc6-dbg_2.35-0ubuntu3_amd64.deb"


def test_resolve_mirror_order_default():
    order = resolve_mirror_order(None)
    assert order[0].type == "regular"
    assert order[-1].type == "fallback"


def test_resolve_mirror_order_specific():
    order = resolve_mirror_order("tuna")
    assert len(order) == 1
    assert order[0].name == "tuna"
