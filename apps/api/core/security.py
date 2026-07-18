# core/security.py
"""
Two things live here for Phase 5:

1. verify_clerk_session(token) — verifies a Clerk session JWT against Clerk's
   JWKS and returns the decoded claims. This is the ONLY place that decides
   "is this request authenticated." No Google/integration token is ever
   consulted here.

2. verify_webhook_signature(...) — generic HMAC/svix-based signature check,
   reused by the Clerk webhook (routers/webhooks.py) and later the Gmail
   Pub/Sub webhook (Phase 6/11).
"""

import time
from dataclasses import dataclass

import jwt
from jwt import PyJWKClient
from svix.webhooks import Webhook, WebhookVerificationError
from fastapi import Request

from core.config import settings
from core.exceptions import AuthError, ConfigError


# --- 1. Clerk session verification -----------------------------------------

@dataclass
class ClerkClaims:
    user_id: str          # Clerk's `sub` claim
    session_id: str | None
    org_role: str | None  # only present if Clerk Organizations is enabled
    raw: dict


# PyJWKClient caches keys internally and refreshes automatically on a
# kid it hasn't seen before, so we can build this once at import time.
if not settings.clerk_jwks_url:
    raise ConfigError(
        "CLERK_JWKS_URL is not configured. Set CLERK_JWT_ISSUER or CLERK_JWKS_URL in your .env."
    )
_jwk_client = PyJWKClient(settings.clerk_jwks_url)


def verify_clerk_session(token: str) -> ClerkClaims:
    """
    Verifies a Clerk session JWT's signature, expiry, and issuer.
    Raises AuthError on anything invalid — missing token, bad signature,
    expired, wrong issuer, or malformed claims.
    """
    if not token:
        raise AuthError("Missing bearer token")

    try:
        signing_key = _jwk_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer,
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise AuthError(f"Invalid session token: {exc}") from exc

    # Clerk sets `nbf` sometimes too; PyJWT checks exp automatically when
    # decoding, but double check `nbf` explicitly since it's not in `require`.
    nbf = payload.get("nbf")
    if nbf and nbf > time.time():
        raise AuthError("Session token not yet valid")

    return ClerkClaims(
        user_id=payload["sub"],
        session_id=payload.get("sid"),
        org_role=payload.get("org_role"),
        raw=payload,
    )


def extract_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise AuthError("Missing or malformed Authorization header")
    return auth_header.removeprefix("Bearer ").strip()


# --- 2. Generic webhook signature verification ------------------------------

def verify_webhook_signature(payload_body: bytes, headers: dict, signing_secret: str) -> dict:
    """
    Verifies a webhook payload signed with svix-compatible signing
    (Clerk webhooks use svix under the hood; reuse this for any future
    svix-signed webhook too — e.g. Gmail Pub/Sub can use a similar
    HMAC pattern if you don't use Pub/Sub's own OIDC verification instead).

    Returns the parsed, verified JSON payload as a dict.
    Raises AuthError if the signature doesn't match.
    """
    wh = Webhook(signing_secret)
    try:
        return wh.verify(payload_body, headers)
    except WebhookVerificationError as exc:
        raise AuthError(f"Webhook signature verification failed: {exc}") from exc


# --- 3. Google OAuth Cryptography Helpers ----------------------------------

import base64
import os
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from itsdangerous import URLSafeSerializer
from core.exceptions import AppError


def _get_encryption_key() -> bytes:
    key_str = settings.token_encryption_key
    # Generate a secure 32-byte key from the configured encryption key via SHA-256
    return hashlib.sha256(key_str.encode("utf-8")).digest()


def encrypt_token(token: str) -> str:
    """
    Encrypts a token string using AES-256-GCM and returns a base64 encoded string
    containing the IV (nonce) followed by the ciphertext.
    """
    if not token:
        return ""
    try:
        key = _get_encryption_key()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)  # Standard 12-byte nonce for GCM
        ciphertext = aesgcm.encrypt(nonce, token.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("utf-8")
    except Exception as exc:
        raise AppError(f"Token encryption failed: {str(exc)}")


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypts a base64 encoded token string that was encrypted using AES-256-GCM.
    """
    if not encrypted_token:
        return ""
    try:
        key = _get_encryption_key()
        aesgcm = AESGCM(key)
        data = base64.b64decode(encrypted_token.encode("utf-8"))
        if len(data) < 12:
            raise ValueError("Encrypted data is too short")
        nonce = data[:12]
        ciphertext = data[12:]
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted.decode("utf-8")
    except Exception as exc:
        raise AppError(f"Token decryption failed: {str(exc)}")


def generate_oauth_state(user_id: str) -> str:
    """
    Generates a secure, cryptographically signed state parameter for Google OAuth.
    """
    serializer = URLSafeSerializer(settings.SECRET_KEY, salt="oauth-state")
    return serializer.dumps({"user_id": user_id})


def verify_oauth_state(state: str) -> str:
    """
    Verifies the signature of the Google OAuth state parameter and returns the user ID.
    Raises AuthError if signature is invalid or expired.
    """
    serializer = URLSafeSerializer(settings.SECRET_KEY, salt="oauth-state")
    try:
        data = serializer.loads(state)
        return data["user_id"]
    except Exception as exc:
        raise AuthError(f"Invalid or expired OAuth state: {str(exc)}")