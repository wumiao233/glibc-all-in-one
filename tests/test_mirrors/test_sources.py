from glibc_aio.mirrors.sources import MIRRORS, Mirror


def test_mirrors_loaded():
    assert len(MIRRORS) >= 4


def test_tuna_is_regular():
    tuna = next(m for m in MIRRORS if m.name == "tuna")
    assert tuna.type == "regular"
    assert "tuna.tsinghua" in tuna.url


def test_old_releases_is_fallback():
    old = next(m for m in MIRRORS if m.name == "old-releases")
    assert old.type == "fallback"


def test_mirror_repr():
    m = Mirror("test", "http://example.com", "regular")
    assert str(m) == "test [regular]"
