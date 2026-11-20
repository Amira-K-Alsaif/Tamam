"""Tests for knowledge administrator authorization."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.modules.knowledge.admin_auth import require_admin


def make_credentials():
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="test-token",
    )


def mock_supabase_user(monkeypatch, role):
    db = MagicMock()

    user = SimpleNamespace(
        id="test-user-123",
        app_metadata={"role": role},
    )

    db.auth.get_user.return_value = SimpleNamespace(user=user)

    monkeypatch.setenv(
        "SUPABASE_URL",
        "https://example.supabase.co",
    )
    monkeypatch.setenv(
        "SUPABASE_SECRET_KEY",
        "test-only-key",
    )

    monkeypatch.setattr(
        "supabase.create_client",
        lambda *args, **kwargs: db,
    )

    return db


def test_reject_unauthenticated_user():
    with pytest.raises(HTTPException) as exc:
        require_admin(None)

    assert exc.value.status_code == 401


def test_reject_regular_employee(monkeypatch):
    mock_supabase_user(monkeypatch, "employee")

    with pytest.raises(HTTPException) as exc:
        require_admin(make_credentials())

    assert exc.value.status_code == 403


def test_allow_admin(monkeypatch):
    db = mock_supabase_user(monkeypatch, "admin")

    user_id = require_admin(make_credentials())

    assert user_id == "test-user-123"
    db.auth.get_user.assert_called_once_with("test-token")


def test_reject_invalid_token(monkeypatch):
    db = mock_supabase_user(monkeypatch, "admin")
    db.auth.get_user.side_effect = RuntimeError("Invalid token")

    with pytest.raises(HTTPException) as exc:
        require_admin(make_credentials())

    assert exc.value.status_code == 401
