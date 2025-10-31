import secrets
import string


ALPHABET = string.ascii_lowercase + string.ascii_uppercase + string.digits


def generate_challenge(length: int = 48) -> str:
    """Generate a typing challenge string of given length.

    Uses only alphanumerics to avoid locale/layout quirks.
    """
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def generate_nonce(length: int = 32) -> str:
    # URL-safe, roughly 4/3 entropy per char
    return secrets.token_urlsafe(length)


