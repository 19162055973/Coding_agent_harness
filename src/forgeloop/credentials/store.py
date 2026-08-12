from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

SERVICE_NAME = "forgeloop"
USERNAME = "api_key"


@dataclass
class CredentialStatus:
    configured: bool
    backend: str
    hint_mask: str = ""


class CredentialStore:
    """OS keyring first; encrypted file fallback for headless/Docker."""

    def __init__(
        self,
        file_path: str | Path | None = None,
        master_password: str | None = None,
        force_file: bool = False,
    ):
        self.file_path = Path(file_path or Path.home() / ".forgeloop" / "secrets.enc")
        self.master_password = master_password or os.getenv("FORGELOOP_MASTER_PASSWORD") or ""
        self.force_file = force_file or os.getenv("FORGELOOP_FORCE_FILE_CREDS", "").lower() in {
            "1",
            "true",
            "yes",
        }

    def _mask(self, value: str) -> str:
        if not value:
            return ""
        if len(value) <= 4:
            return "****"
        return "*" * (len(value) - 4) + value[-4:]

    def _fernet(self) -> Fernet:
        if not self.master_password:
            raise RuntimeError(
                "encrypted file backend requires master password "
                "(FORGELOOP_MASTER_PASSWORD or pass master_password=)"
            )
        digest = hashlib.sha256(self.master_password.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest)
        return Fernet(key)

    def _keyring_available(self) -> bool:
        if self.force_file:
            return False
        try:
            import keyring
            from keyring.errors import KeyringError

            # probe
            keyring.get_password(SERVICE_NAME, "__probe__")
            return True
        except Exception:  # noqa: BLE001
            return False

    def set_key(self, api_key: str) -> str:
        if not api_key:
            raise ValueError("api_key is empty")
        # prefer env-less secure store
        if self._keyring_available():
            import keyring

            keyring.set_password(SERVICE_NAME, USERNAME, api_key)
            return "keyring"
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        token = self._fernet().encrypt(api_key.encode("utf-8")).decode("utf-8")
        payload = {"api_key": token}
        self.file_path.write_text(json.dumps(payload), encoding="utf-8")
        return "encrypted_file"

    def get_key(self) -> str | None:
        # optional dotenv source (documented risk)
        env_key = os.getenv("FORGELOOP_API_KEY")
        if env_key:
            return env_key
        if self._keyring_available():
            import keyring

            val = keyring.get_password(SERVICE_NAME, USERNAME)
            if val:
                return val
        if self.file_path.exists():
            try:
                data = json.loads(self.file_path.read_text(encoding="utf-8"))
                token = data.get("api_key", "")
                return self._fernet().decrypt(token.encode("utf-8")).decode("utf-8")
            except (InvalidToken, OSError, json.JSONDecodeError, RuntimeError):
                return None
        return None

    def clear(self) -> None:
        if self._keyring_available():
            import keyring
            from keyring.errors import PasswordDeleteError

            try:
                keyring.delete_password(SERVICE_NAME, USERNAME)
            except PasswordDeleteError:
                pass
        if self.file_path.exists():
            self.file_path.unlink()

    def status(self) -> CredentialStatus:
        backend = "none"
        key = None
        if os.getenv("FORGELOOP_API_KEY"):
            backend = "env"
            key = os.getenv("FORGELOOP_API_KEY")
        elif self._keyring_available():
            import keyring

            key = keyring.get_password(SERVICE_NAME, USERNAME)
            if key:
                backend = "keyring"
        if not key and self.file_path.exists():
            backend = "encrypted_file"
            key = self.get_key() if not os.getenv("FORGELOOP_API_KEY") else key
            # avoid env override confusion
            if backend == "encrypted_file":
                try:
                    data = json.loads(self.file_path.read_text(encoding="utf-8"))
                    token = data.get("api_key", "")
                    key = self._fernet().decrypt(token.encode("utf-8")).decode("utf-8")
                except Exception:  # noqa: BLE001
                    key = None
        return CredentialStatus(
            configured=bool(key),
            backend=backend if key else ("none" if not self.file_path.exists() else backend),
            hint_mask=self._mask(key or ""),
        )
