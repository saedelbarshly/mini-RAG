from datetime import UTC, datetime, timedelta

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from starlette.concurrency import run_in_threadpool

from .BaseController import BaseController

# Built once: creating the hasher is cheap, but there is no reason to repeat it per call.
_password_hash = PasswordHash.recommended()

# Verified against when the email is unknown, so a failed login takes the same
# time whether or not the account exists (prevents user enumeration by timing).
_DUMMY_HASH = _password_hash.hash("dummy-password-for-timing")


class UserController(BaseController):
    def __init__(self, secert_key, algorithm, minutes):
        super().__init__()
        self.secert_key = secert_key
        self.algorithm = algorithm
        self.minutes = minutes

    async def create_hash_password(self, password: str) -> str:
        # Argon2 is CPU-heavy by design; run it off the event loop.
        return await run_in_threadpool(_password_hash.hash, password)

    @staticmethod
    async def verify_password(plain_password: str, hashed_password: str | None) -> bool:
        """Check a password. Pass hashed_password=None for an unknown user:
        a dummy hash is checked so timing matches, and False is returned."""
        if hashed_password is None:
            await run_in_threadpool(_password_hash.verify, plain_password, _DUMMY_HASH)
            return False
        return await run_in_threadpool(_password_hash.verify, plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=self.minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secert_key, self.algorithm)
        return encoded_jwt

    def verify_access_token(self, token: str) -> str | None:
        """Validate a JWT and return its subject, or None if it is invalid."""
        try:
            payload = jwt.decode(
                token,
                self.secert_key,
                algorithms=[self.algorithm],
            )
        except InvalidTokenError:
            return None

        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject:
            return None
        return subject
