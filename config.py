"""Config loading/saving with DPAPI encryption for the API key."""
import json
import os
import base64

# win32crypt is Windows-only; import conditionally for testability
try:
    import win32crypt
    HAS_DPAPI = True
except ImportError:
    HAS_DPAPI = False

DEFAULT_APP_DIR = os.path.join(os.environ.get("APPDATA", "."), "SocialDecoder")

DEFAULTS = {
    "hotkey": "ctrl+shift+d",
    "theme": "dark",
    "decode_mode": "nd",  # "nd" = neurodivergent user, "nt" = neurotypical user
    "start_on_boot": False,
    "api_key_encrypted": "",
}


class Config:
    """Manages app configuration with encrypted API key storage."""

    def __init__(self, app_dir: str = DEFAULT_APP_DIR):
        self.app_dir = app_dir
        self.config_path = os.path.join(app_dir, "config.json")
        self._data = dict(DEFAULTS)
        self._load()

    def _load(self):
        """Load config from disk if it exists."""
        if os.path.isfile(self.config_path):
            with open(self.config_path, "r") as f:
                saved = json.load(f)
            self._data.update(saved)

    def save(self):
        """Persist config to disk."""
        os.makedirs(self.app_dir, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self._data, f, indent=2)

    def get(self, key: str):
        """Get a config value by key."""
        if key == "api_key":
            return self.get_api_key()
        return self._data.get(key, DEFAULTS.get(key))

    def set(self, key: str, value):
        """Set a config value."""
        self._data[key] = value

    def set_api_key(self, plaintext_key: str):
        """Encrypt and store the API key using Windows DPAPI."""
        if HAS_DPAPI and plaintext_key:
            encrypted = win32crypt.CryptProtectData(
                plaintext_key.encode("utf-8"),
                "SocialDecoder API Key",
            )
            self._data["api_key_encrypted"] = base64.b64encode(encrypted).decode("ascii")
        else:
            # Fallback: base64 only (non-Windows or empty key)
            self._data["api_key_encrypted"] = base64.b64encode(
                plaintext_key.encode("utf-8")
            ).decode("ascii") if plaintext_key else ""

    def get_api_key(self) -> str:
        """Decrypt and return the stored API key."""
        stored = self._data.get("api_key_encrypted", "")
        if not stored:
            return ""
        raw = base64.b64decode(stored)
        if HAS_DPAPI:
            try:
                _, decrypted = win32crypt.CryptUnprotectData(raw)
                return decrypted.decode("utf-8")
            except Exception:
                return ""
        else:
            return raw.decode("utf-8")

    @property
    def is_first_run(self) -> bool:
        """True if no config file exists yet."""
        return not os.path.isfile(self.config_path)

    @property
    def db_path(self) -> str:
        """Path to the SQLite history database."""
        return os.path.join(self.app_dir, "history.db")
