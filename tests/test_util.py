from make_py.util import to_list


def test_to_list():
    assert to_list(1) == [1]
    assert to_list([1]) == [1]
    assert to_list("abc") == ["abc"]
    assert to_list(["abc"]) == ["abc"]

    s = {"abc"}
    assert to_list(s) == s
