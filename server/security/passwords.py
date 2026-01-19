from passlib.hash import bcrypt


def hash_password(plain_password: str) -> str:
    if len(plain_password) < 4:
        raise ValueError("Password must be at least 4 characters")
    return bcrypt.hash(plain_password[:72])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.verify(plain_password, hashed_password)
