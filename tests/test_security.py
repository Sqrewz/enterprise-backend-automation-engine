from app.core.security import create_access_token, decode_token, hash_password, verify_password

def test_password_hash_roundtrip():
    hashed = hash_password("a-safe-password-123")
    assert verify_password("a-safe-password-123", hashed)
    assert not verify_password("wrong-password", hashed)

def test_token_contains_claims():
    assert decode_token(create_access_token("9", "admin"))["sub"] == "9"
