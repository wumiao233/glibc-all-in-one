from glibc_aio.packages.extractor import parse_ar


def test_parse_ar_single_entry():
    header = b"!<arch>\n"
    name = b"debian-binary   "
    mtime = b"1000000000  "
    owner = b"0     "
    group = b"0     "
    mode = b"100644  "
    size = b"4         "
    magic = b"\x60\x0a"
    file_header = name + mtime + owner + group + mode + size + magic
    content = b"2.0\n"
    ar_data = header + file_header + content

    entries = parse_ar(ar_data)
    assert entries == [(b"debian-binary", b"2.0\n")]


def test_parse_ar_not_ar():
    try:
        parse_ar(b"not an ar archive")
        assert False, "should have raised"
    except ValueError:
        pass


def test_parse_ar_empty():
    entries = parse_ar(b"!<arch>\n")
    assert entries == []
