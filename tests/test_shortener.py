"""Unit tests for utils/shortener.py."""

import string

import pytest

from utils.shortener import (
    ALPHABET,
    CODE_LENGTH,
    MAX_ATTEMPTS,
    create_unique_short_code,
    generate_short_code,
)


class FakeCursor:
    """Minimal cursor stub: records SQL and returns configured results."""

    def __init__(self, existing_codes=()):
        self.existing_codes = set(existing_codes)
        self.queries = []

    def execute(self, query, params=None):
        self.queries.append((query, params))

    def fetchone(self):
        last_params = self.queries[-1][1]
        code = last_params[0] if last_params else None
        if code in self.existing_codes:
            return (1,)
        return None


class FakeConnection:
    def __init__(self, existing_codes=()):
        self.cursor_obj = FakeCursor(existing_codes)

    def cursor(self):
        return self.cursor_obj


def test_generate_short_code_length_and_alphabet():
    code = generate_short_code()
    assert len(code) == CODE_LENGTH
    assert set(code) <= set(ALPHABET)


def test_generate_short_code_is_alphanumeric_only():
    for _ in range(50):
        code = generate_short_code()
        assert all(c in string.ascii_letters + string.digits for c in code)


def test_generate_short_code_custom_length():
    assert len(generate_short_code(12)) == 12


def test_generate_short_code_uses_secure_source():
    import utils.shortener as s

    assert "secrets" in s.__dict__ or s.secrets is not None


def test_create_unique_short_code_returns_code_when_free():
    conn = FakeConnection(existing_codes=())
    code = create_unique_short_code(conn)
    assert code not in conn.cursor_obj.existing_codes
    assert len(code) == CODE_LENGTH


def test_create_unique_short_code_retries_on_collision(monkeypatch):
    # First 2 generated codes collide with existing rows, the 3rd is free.
    codes = iter(["AAA111", "BBB222", "CCC333"])
    monkeypatch.setattr(
        "utils.shortener.generate_short_code", lambda length=6: next(codes)
    )
    conn = FakeConnection(existing_codes={"AAA111", "BBB222"})

    code = create_unique_short_code(conn)

    assert code == "CCC333"
    # One SELECT issued per attempted code, including the collisions.
    select_count = sum(1 for q, _ in conn.cursor_obj.queries if "SELECT" in q)
    assert select_count == 3


def test_create_unique_short_code_gives_up_after_max_attempts(monkeypatch):
    monkeypatch.setattr(
        "utils.shortener.generate_short_code", lambda length=6: "ALWAYS-COLLIDE"
    )
    conn = FakeConnection(existing_codes={"ALWAYS-COLLIDE"})

    with pytest.raises(RuntimeError):
        create_unique_short_code(conn)
    assert len(conn.cursor_obj.queries) == MAX_ATTEMPTS
