from dispatch.common.ids import is_valid_ulid, new_ulid


def test_ulid_is_26_chars_from_crockford_alphabet():
    ulid = new_ulid()
    assert len(ulid) == 26
    assert is_valid_ulid(ulid)


def test_ulids_are_unique():
    ulids = {new_ulid() for _ in range(1000)}
    assert len(ulids) == 1000


def test_ulids_sort_lexicographically_by_timestamp():
    earlier = new_ulid(timestamp_ms=1_000_000)
    later = new_ulid(timestamp_ms=2_000_000)
    assert earlier[:10] < later[:10]
    assert sorted([later, earlier]) == [earlier, later]


def test_is_valid_ulid_rejects_garbage():
    assert not is_valid_ulid("not-a-ulid")
    assert not is_valid_ulid("")
    assert not is_valid_ulid("ILOU" + "0" * 22)  # I, L, O, U are not in the Crockford alphabet
