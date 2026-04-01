"""
Tests for the auth module.

Since Clerk auth requires live API keys and JWKS, these tests focus on:
- Token verification error handling (invalid / missing tokens)
- The ``require_auth`` and ``get_current_user`` dependency logic
- JWKS cache behaviour
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

import auth


class TestVerifyToken:
    def test_verify_token_invalid_raises(self):
        """A garbage JWT should raise 401."""
        with patch("auth.get_jwks") as mock_jwks:
            mock_jwks.return_value = {"keys": []}
            with pytest.raises(HTTPException) as exc_info:
                auth.verify_token("invalid.jwt.token")
            assert exc_info.value.status_code == 401

    def test_verify_token_no_matching_kid_raises(self):
        """If JWKS has no matching kid, raise 401."""
        with patch("auth.get_jwks") as mock_jwks:
            mock_jwks.return_value = {
                "keys": [
                    {
                        "kid": "key-1",
                        "kty": "RSA",
                        "use": "sig",
                        "n": "test_n",
                        "e": "AQAB",
                    }
                ]
            }
            with patch("auth.jwt") as mock_jwt:
                mock_jwt.get_unverified_header.return_value = {
                    "kid": "non-existent-kid"
                }
                with pytest.raises(HTTPException) as exc_info:
                    auth.verify_token("some.token.value")
                assert exc_info.value.status_code == 401
                assert "signing key" in exc_info.value.detail.lower()


class TestGetJWKS:
    def test_jwks_cache_reused(self):
        """Once cached, JWKS should not make another network request."""
        original_cache = auth._jwks_cache
        try:
            auth._jwks_cache = {"keys": [{"kid": "cached"}]}
            result = auth.get_jwks()
            assert result["keys"][0]["kid"] == "cached"
        finally:
            auth._jwks_cache = original_cache

    def test_jwks_no_frontend_api_raises(self):
        """If CLERK_FRONTEND_API is empty, should raise 500."""
        original_cache = auth._jwks_cache
        try:
            auth._jwks_cache = None  # force fetch
            with patch("auth.CLERK_FRONTEND_API", ""):
                with pytest.raises(HTTPException) as exc_info:
                    auth.get_jwks()
                assert exc_info.value.status_code == 500
        finally:
            auth._jwks_cache = original_cache


class TestRequireAuth:
    def test_require_auth_no_credentials_raises(self):
        """Calling require_auth with no token should raise 401."""
        with pytest.raises(HTTPException) as exc_info:
            # Simulate credentials=None
            auth.require_auth(credentials=None, db=MagicMock())
        assert exc_info.value.status_code == 401
        assert "authentication required" in exc_info.value.detail.lower()


class TestGetCurrentUser:
    def test_get_current_user_no_credentials_returns_none(self):
        """get_current_user with no token should return None (optional auth)."""
        result = auth.get_current_user(credentials=None, db=MagicMock())
        assert result is None

    def test_get_current_user_user_not_in_db_raises(self):
        """Valid token for a clerk_id not in the local DB should raise 401."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # user not found

        mock_creds = MagicMock()
        mock_creds.credentials = "some.token"

        with patch("auth.verify_token") as mock_verify:
            mock_verify.return_value = {"sub": "clerk_unknown"}
            with pytest.raises(HTTPException) as exc_info:
                auth.get_current_user(credentials=mock_creds, db=mock_db)
            assert exc_info.value.status_code == 401
            assert "not found" in exc_info.value.detail.lower()

    def test_get_current_user_invalid_token_payload_raises(self):
        """Token with no 'sub' claim should raise 401."""
        mock_creds = MagicMock()
        mock_creds.credentials = "some.token"

        with patch("auth.verify_token") as mock_verify:
            mock_verify.return_value = {}  # no 'sub'
            with pytest.raises(HTTPException) as exc_info:
                auth.get_current_user(
                    credentials=mock_creds, db=MagicMock()
                )
            assert exc_info.value.status_code == 401
