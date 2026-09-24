"""Password hashing and JWT helpers. Placeholders only — implemented next session."""


def hash_password(password: str) -> str:
    raise NotImplementedError


def verify_password(plain_password: str, password_hash: str) -> bool:
    raise NotImplementedError


def create_access_token(subject: str) -> str:
    raise NotImplementedError


def decode_access_token(token: str) -> str:
    raise NotImplementedError
