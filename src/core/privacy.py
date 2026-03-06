"""Privacy utilities for sensitive voice metrics."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from config.paths import get_output_dir
from utils import ConfigError, get_logger

logger = get_logger(__name__)


class VoicePrivacyService:
    """Encrypt/decrypt sensitive voice metrics with a local key."""

    def __init__(self, key_path: Path | None = None) -> None:
        """Initialize service.

        Args:
            key_path: Optional key file path for tests.
        """
        if key_path is None:
            key_path = get_output_dir() / ".voice_metrics.key"
        self.key_path = key_path
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        self._fernet = self._build_fernet()

    def encrypt_metrics(self, payload: dict[str, Any]) -> str:
        """Encrypt a metrics dictionary.

        Args:
            payload: Sensitive metrics payload.

        Returns:
            Encrypted token string.
        """
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return self._fernet.encrypt(raw).decode("utf-8")

    def decrypt_metrics(self, token: str | None) -> dict[str, Any] | None:
        """Decrypt a token into metrics.

        Args:
            token: Token returned by :meth:`encrypt_metrics`.

        Returns:
            Decrypted payload dictionary or None.
        """
        if not token:
            return None
        try:
            raw = self._fernet.decrypt(token.encode("utf-8"))
            return json.loads(raw.decode("utf-8"))
        except Exception:
            logger.warning("Could not decrypt voice metrics entry")
            return None

    def _build_fernet(self):
        """Build a Fernet instance from local key file."""
        try:
            from cryptography.fernet import Fernet
        except Exception as exc:
            raise ConfigError(
                "La librería 'cryptography' es obligatoria para cifrar métricas de voz."
            ) from exc

        key = self._load_or_create_key()
        return Fernet(key)

    def _load_or_create_key(self) -> bytes:
        """Load local key or create one if missing.

        Returns:
            URL-safe base64 key bytes.
        """
        if self.key_path.exists():
            return self.key_path.read_bytes().strip()
        try:
            from cryptography.fernet import Fernet
        except Exception as exc:
            raise ConfigError("No se pudo inicializar el cifrado local") from exc

        key = Fernet.generate_key()
        self.key_path.write_bytes(key + b"\n")
        logger.info("Created new local voice encryption key: %s", self.key_path)
        return key

    @staticmethod
    def is_probably_encrypted(value: str | None) -> bool:
        """Best-effort check for encrypted token format.

        Args:
            value: Token candidate.

        Returns:
            True if value looks like URL-safe base64 token.
        """
        if not value or not isinstance(value, str):
            return False
        try:
            base64.urlsafe_b64decode(value.encode("utf-8"))
            return True
        except Exception:
            return False

