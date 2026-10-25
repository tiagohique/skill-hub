from hub.security import hash_password, new_token, token_digest, verify_password


def test_hash_verifies_only_the_right_password() -> None:
    stored = hash_password("admin")
    assert stored.startswith("scrypt$")
    assert verify_password("admin", stored)
    assert not verify_password("outra", stored)


def test_hash_uses_random_salt() -> None:
    assert hash_password("admin") != hash_password("admin")


def test_malformed_hash_is_rejected() -> None:
    assert not verify_password("admin", "texto-qualquer")
    assert not verify_password("admin", "bcrypt$1$2$3$4$5")


def test_token_digest_is_sha256_hex_and_tokens_differ() -> None:
    assert len(token_digest("x")) == 64
    assert new_token() != new_token()
