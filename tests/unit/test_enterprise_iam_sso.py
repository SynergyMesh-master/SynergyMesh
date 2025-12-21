#!/usr/bin/env python3
"""
Enterprise IAM SSO JWT Validation Test Suite

Tests comprehensive JWT validation in the OIDC authentication flow,
covering security-critical scenarios including:
- Valid token validation
- Missing nonce detection
- Nonce mismatch detection  
- Invalid signature detection
- Expired token detection
- Malformed JWT detection
"""

import asyncio
import json
import pytest
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import UUID, uuid4

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError, DecodeError

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from enterprise.iam.models import Role, SSOConfig
from enterprise.iam.sso import (
    HTTPClient,
    MembershipRepository,
    OIDCTokens,
    SSOManager,
    SSORepository,
    UserRepository,
)


# Test fixtures and helpers
@pytest.fixture
def mock_sso_repository():
    """Mock SSO repository"""
    repo = AsyncMock(spec=SSORepository)
    return repo


@pytest.fixture
def mock_user_repository():
    """Mock user repository"""
    repo = AsyncMock(spec=UserRepository)
    return repo


@pytest.fixture
def mock_membership_repository():
    """Mock membership repository"""
    repo = AsyncMock(spec=MembershipRepository)
    return repo


@pytest.fixture
def mock_http_client():
    """Mock HTTP client"""
    client = AsyncMock(spec=HTTPClient)
    return client


@pytest.fixture
def sso_manager(mock_sso_repository, mock_user_repository, mock_membership_repository, mock_http_client):
    """Create SSO manager with mocked dependencies"""
    return SSOManager(
        sso_repository=mock_sso_repository,
        user_repository=mock_user_repository,
        membership_repository=mock_membership_repository,
        http_client=mock_http_client,
    )


@pytest.fixture
def org_id():
    """Test organization ID"""
    return uuid4()


@pytest.fixture
def sso_config(org_id):
    """Test SSO configuration"""
    return SSOConfig(
        org_id=org_id,
        provider_type="oidc",
        issuer_url="https://accounts.example.com",
        client_id="test-client-id",
        client_secret_hash="test-hash",
        attribute_mapping={"email": "email", "name": "display_name"},
        default_role=Role.MEMBER,
        jit_enabled=True,
        is_active=True,
    )


@pytest.fixture
def rsa_keypair():
    """Generate RSA keypair for JWT signing"""
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import rsa
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    return private_key


@pytest.fixture
def jwks_uri():
    """Mock JWKS URI"""
    return "https://accounts.example.com/.well-known/jwks.json"


@pytest.fixture
def discovery_document(jwks_uri):
    """Mock OIDC discovery document"""
    return {
        "issuer": "https://accounts.example.com",
        "authorization_endpoint": "https://accounts.example.com/authorize",
        "token_endpoint": "https://accounts.example.com/token",
        "userinfo_endpoint": "https://accounts.example.com/userinfo",
        "jwks_uri": jwks_uri,
    }


def create_id_token(private_key, client_id: str, issuer: str, nonce: str, expired: bool = False, include_nonce: bool = True):
    """Helper to create a signed ID token"""
    now = datetime.utcnow()
    
    payload = {
        "iss": issuer,
        "sub": "user-123",
        "aud": client_id,
        "iat": int(now.timestamp()),
        "exp": int((now - timedelta(hours=1) if expired else now + timedelta(hours=1)).timestamp()),
    }
    
    if include_nonce:
        payload["nonce"] = nonce
    
    token = jwt.encode(payload, private_key, algorithm="RS256")
    return token


# ============================================================================
# JWT Validation Tests
# ============================================================================

class TestJWTValidation:
    """Test JWT validation in OIDC authentication flow"""

    @pytest.mark.asyncio
    async def test_valid_jwt_token(self, sso_manager, sso_config, org_id, rsa_keypair, discovery_document):
        """Test successful JWT validation with valid token"""
        state = "test-state"
        nonce = "test-nonce"
        code = "auth-code"
        client_secret = "client-secret"
        
        # Setup pending auth
        sso_manager._pending_auth[state] = {
            "org_id": str(org_id),
            "nonce": nonce,
            "code_verifier": "test-verifier",
            "redirect_uri": "https://app.example.com/callback",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Mock SSO config retrieval
        sso_manager.sso_repository.get_sso_config.return_value = sso_config
        
        # Mock discovery document
        sso_manager.http_client.get.return_value = discovery_document
        
        # Create valid ID token
        id_token = create_id_token(
            rsa_keypair,
            sso_config.client_id,
            discovery_document["issuer"],
            nonce
        )
        
        # Mock token exchange response
        token_response = {
            "access_token": "access-token",
            "id_token": id_token,
            "expires_in": 3600,
        }
        sso_manager.http_client.post.return_value = token_response
        
        # Mock userinfo response
        userinfo_response = {
            "sub": "user-123",
            "email": "user@example.com",
            "email_verified": True,
            "name": "Test User",
        }
        
        # Mock the JWT validation
        with patch('jwt.PyJWKClient') as mock_jwk_client:
            # Setup mock signing key
            mock_signing_key = Mock()
            mock_signing_key.key = rsa_keypair.public_key()
            mock_jwk_instance = Mock()
            mock_jwk_instance.get_signing_key_from_jwt.return_value = mock_signing_key
            mock_jwk_client.return_value = mock_jwk_instance
            
            # Setup userinfo response (called after JWT validation)
            async def get_side_effect(url, headers=None):
                if "userinfo" in url:
                    return userinfo_response
                return discovery_document
            
            sso_manager.http_client.get.side_effect = get_side_effect
            
            # Mock user provisioning
            mock_user = Mock()
            mock_user.email = "user@example.com"
            mock_membership = Mock()
            sso_manager._provision_sso_user = AsyncMock(return_value=(mock_user, mock_membership))
            
            # Execute
            user, membership = await sso_manager.complete_oidc_login(state, code, client_secret)
            
            # Verify
            assert user.email == "user@example.com"
            assert state not in sso_manager._pending_auth  # Cleaned up

    @pytest.mark.asyncio
    async def test_missing_nonce_in_token(self, sso_manager, sso_config, org_id, rsa_keypair, discovery_document):
        """Test JWT validation fails when nonce is missing from token"""
        state = "test-state"
        nonce = "test-nonce"
        code = "auth-code"
        client_secret = "client-secret"
        
        # Setup pending auth
        sso_manager._pending_auth[state] = {
            "org_id": str(org_id),
            "nonce": nonce,
            "code_verifier": "test-verifier",
            "redirect_uri": "https://app.example.com/callback",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        sso_manager.sso_repository.get_sso_config.return_value = sso_config
        sso_manager.http_client.get.return_value = discovery_document
        
        # Create ID token WITHOUT nonce
        id_token = create_id_token(
            rsa_keypair,
            sso_config.client_id,
            discovery_document["issuer"],
            nonce,
            include_nonce=False  # Missing nonce
        )
        
        token_response = {
            "access_token": "access-token",
            "id_token": id_token,
            "expires_in": 3600,
        }
        sso_manager.http_client.post.return_value = token_response
        
        with patch('jwt.PyJWKClient') as mock_jwk_client:
            mock_signing_key = Mock()
            mock_signing_key.key = rsa_keypair.public_key()
            mock_jwk_instance = Mock()
            mock_jwk_instance.get_signing_key_from_jwt.return_value = mock_signing_key
            mock_jwk_client.return_value = mock_jwk_instance
            
            # Should raise ValueError for missing nonce
            with pytest.raises(ValueError, match="Missing nonce claim in ID token"):
                await sso_manager.complete_oidc_login(state, code, client_secret)

    @pytest.mark.asyncio
    async def test_nonce_mismatch(self, sso_manager, sso_config, org_id, rsa_keypair, discovery_document):
        """Test JWT validation fails when nonce doesn't match"""
        state = "test-state"
        expected_nonce = "expected-nonce"
        wrong_nonce = "wrong-nonce"
        code = "auth-code"
        client_secret = "client-secret"
        
        # Setup pending auth with expected nonce
        sso_manager._pending_auth[state] = {
            "org_id": str(org_id),
            "nonce": expected_nonce,
            "code_verifier": "test-verifier",
            "redirect_uri": "https://app.example.com/callback",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        sso_manager.sso_repository.get_sso_config.return_value = sso_config
        sso_manager.http_client.get.return_value = discovery_document
        
        # Create ID token with WRONG nonce
        id_token = create_id_token(
            rsa_keypair,
            sso_config.client_id,
            discovery_document["issuer"],
            wrong_nonce  # Different nonce
        )
        
        token_response = {
            "access_token": "access-token",
            "id_token": id_token,
            "expires_in": 3600,
        }
        sso_manager.http_client.post.return_value = token_response
        
        with patch('jwt.PyJWKClient') as mock_jwk_client:
            mock_signing_key = Mock()
            mock_signing_key.key = rsa_keypair.public_key()
            mock_jwk_instance = Mock()
            mock_jwk_instance.get_signing_key_from_jwt.return_value = mock_signing_key
            mock_jwk_client.return_value = mock_jwk_instance
            
            # Should raise ValueError for nonce mismatch
            with pytest.raises(ValueError, match="Nonce mismatch.*possible replay attack"):
                await sso_manager.complete_oidc_login(state, code, client_secret)

    @pytest.mark.asyncio
    async def test_invalid_jwt_signature(self, sso_manager, sso_config, org_id, rsa_keypair, discovery_document):
        """Test JWT validation fails with invalid signature"""
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.asymmetric import rsa
        
        state = "test-state"
        nonce = "test-nonce"
        code = "auth-code"
        client_secret = "client-secret"
        
        # Setup pending auth
        sso_manager._pending_auth[state] = {
            "org_id": str(org_id),
            "nonce": nonce,
            "code_verifier": "test-verifier",
            "redirect_uri": "https://app.example.com/callback",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        sso_manager.sso_repository.get_sso_config.return_value = sso_config
        sso_manager.http_client.get.return_value = discovery_document
        
        # Create token signed with DIFFERENT key
        wrong_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        id_token = create_id_token(
            wrong_private_key,  # Wrong key
            sso_config.client_id,
            discovery_document["issuer"],
            nonce
        )
        
        token_response = {
            "access_token": "access-token",
            "id_token": id_token,
            "expires_in": 3600,
        }
        sso_manager.http_client.post.return_value = token_response
        
        with patch('jwt.PyJWKClient') as mock_jwk_client:
            # Return the CORRECT public key (mismatch with token signature)
            mock_signing_key = Mock()
            mock_signing_key.key = rsa_keypair.public_key()
            mock_jwk_instance = Mock()
            mock_jwk_instance.get_signing_key_from_jwt.return_value = mock_signing_key
            mock_jwk_client.return_value = mock_jwk_instance
            
            # Should raise ValueError wrapping signature error
            with pytest.raises(ValueError, match="Failed to validate ID token"):
                await sso_manager.complete_oidc_login(state, code, client_secret)

    @pytest.mark.asyncio
    async def test_expired_jwt_token(self, sso_manager, sso_config, org_id, rsa_keypair, discovery_document):
        """Test JWT validation fails with expired token"""
        state = "test-state"
        nonce = "test-nonce"
        code = "auth-code"
        client_secret = "client-secret"
        
        # Setup pending auth
        sso_manager._pending_auth[state] = {
            "org_id": str(org_id),
            "nonce": nonce,
            "code_verifier": "test-verifier",
            "redirect_uri": "https://app.example.com/callback",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        sso_manager.sso_repository.get_sso_config.return_value = sso_config
        sso_manager.http_client.get.return_value = discovery_document
        
        # Create EXPIRED token
        id_token = create_id_token(
            rsa_keypair,
            sso_config.client_id,
            discovery_document["issuer"],
            nonce,
            expired=True  # Expired token
        )
        
        token_response = {
            "access_token": "access-token",
            "id_token": id_token,
            "expires_in": 3600,
        }
        sso_manager.http_client.post.return_value = token_response
        
        with patch('jwt.PyJWKClient') as mock_jwk_client:
            mock_signing_key = Mock()
            mock_signing_key.key = rsa_keypair.public_key()
            mock_jwk_instance = Mock()
            mock_jwk_instance.get_signing_key_from_jwt.return_value = mock_signing_key
            mock_jwk_client.return_value = mock_jwk_instance
            
            # Should raise ValueError wrapping ExpiredSignatureError
            with pytest.raises(ValueError, match="Failed to validate ID token"):
                await sso_manager.complete_oidc_login(state, code, client_secret)

    @pytest.mark.asyncio
    async def test_malformed_jwt_token(self, sso_manager, sso_config, org_id, discovery_document):
        """Test JWT validation fails with malformed token"""
        state = "test-state"
        nonce = "test-nonce"
        code = "auth-code"
        client_secret = "client-secret"
        
        # Setup pending auth
        sso_manager._pending_auth[state] = {
            "org_id": str(org_id),
            "nonce": nonce,
            "code_verifier": "test-verifier",
            "redirect_uri": "https://app.example.com/callback",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        sso_manager.sso_repository.get_sso_config.return_value = sso_config
        sso_manager.http_client.get.return_value = discovery_document
        
        # Malformed token (not valid JWT format)
        token_response = {
            "access_token": "access-token",
            "id_token": "not.a.valid.jwt.token.at.all",  # Malformed
            "expires_in": 3600,
        }
        sso_manager.http_client.post.return_value = token_response
        
        with patch('jwt.PyJWKClient') as mock_jwk_client:
            mock_jwk_instance = Mock()
            # PyJWKClient will raise when trying to get signing key from malformed JWT
            mock_jwk_instance.get_signing_key_from_jwt.side_effect = DecodeError("Invalid token")
            mock_jwk_client.return_value = mock_jwk_instance
            
            # Should raise ValueError wrapping decode error
            with pytest.raises(ValueError, match="Failed to validate ID token"):
                await sso_manager.complete_oidc_login(state, code, client_secret)

    @pytest.mark.asyncio
    async def test_missing_jwks_uri(self, sso_manager, sso_config, org_id):
        """Test JWT validation fails when JWKS URI is missing from discovery"""
        state = "test-state"
        nonce = "test-nonce"
        code = "auth-code"
        client_secret = "client-secret"
        
        # Setup pending auth
        sso_manager._pending_auth[state] = {
            "org_id": str(org_id),
            "nonce": nonce,
            "code_verifier": "test-verifier",
            "redirect_uri": "https://app.example.com/callback",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        sso_manager.sso_repository.get_sso_config.return_value = sso_config
        
        # Discovery document WITHOUT jwks_uri
        discovery_no_jwks = {
            "issuer": "https://accounts.example.com",
            "authorization_endpoint": "https://accounts.example.com/authorize",
            "token_endpoint": "https://accounts.example.com/token",
            "userinfo_endpoint": "https://accounts.example.com/userinfo",
            # Missing jwks_uri
        }
        sso_manager.http_client.get.return_value = discovery_no_jwks
        
        token_response = {
            "access_token": "access-token",
            "id_token": "any-token",
            "expires_in": 3600,
        }
        sso_manager.http_client.post.return_value = token_response
        
        # Should raise ValueError for missing jwks_uri
        with pytest.raises(ValueError, match="OIDC discovery document missing 'jwks_uri'"):
            await sso_manager.complete_oidc_login(state, code, client_secret)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
