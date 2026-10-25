import hashlib

from hub.domain.hashing import bundle_sha256, sha256_hex
from hub.domain.models import FileEntry


def test_sha256_hex_known_value() -> None:
    assert sha256_hex(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_bundle_sha256_sorted_by_path() -> None:
    a = FileEntry("a.md", sha256_hex(b"A"), 1)
    b = FileEntry("b.md", sha256_hex(b"B"), 1)
    expected = hashlib.sha256(f"a.md\0{a.sha256}\nb.md\0{b.sha256}".encode()).hexdigest()
    assert bundle_sha256([b, a]) == expected
    assert bundle_sha256([a, b]) == expected


def test_bundle_sha256_changes_with_content() -> None:
    a1 = FileEntry("a.md", sha256_hex(b"1"), 1)
    a2 = FileEntry("a.md", sha256_hex(b"2"), 1)
    assert bundle_sha256([a1]) != bundle_sha256([a2])
