from peach.misc.encrypt import md5


def test_md5():
    assert md5("abc") == "900150983cd24fb0d6963f7d28e17f72"
