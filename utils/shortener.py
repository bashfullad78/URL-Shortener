"""Short code generation."""

import secrets
import string

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 6
MAX_ATTEMPTS = 10


def generate_short_code(length: int = CODE_LENGTH) -> str:
    """Generate a random short code from a cryptographically secure source."""
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def create_unique_short_code(connection, length: int = CODE_LENGTH) -> str:
    """Generate a short code that does not already exist in the urls table.

    Accepts an existing database connection (rather than opening its own) so
    the generation strategy is explicit and testable. If every candidate
    collides, raises RuntimeError instead of looping forever.
    """
    cursor = connection.cursor()
    for _ in range(MAX_ATTEMPTS):
        code = generate_short_code(length)
        cursor.execute("SELECT 1 FROM urls WHERE short_code = %s", (code,))
        if not cursor.fetchone():
            return code
    raise RuntimeError(
        f"Could not generate a unique short code after {MAX_ATTEMPTS} attempts"
    )
