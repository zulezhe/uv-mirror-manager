"""UV configuration file operations."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

import tomlkit
from platformdirs import PlatformDirs

from uvm.constants import (
    CONFIG_VERSION,
    USER_CONFIG_FILE,
    UV_CONFIG_BACKUP,
    UV_CONFIG_FILE,
)


class UVConfig:
    """Manages UV configuration file operations."""

    def __init__(self) -> None:
        """Initialize UV config manager."""
        self._dirs = PlatformDirs("uv", appauthor="astral-sh")
        self._uvm_dirs = PlatformDirs("uv-mirror", appauthor="uvm")

    @property
    def uv_config_path(self) -> Path:
        """Get UV configuration file path."""
        return Path(str(self._dirs.user_config_path)) / UV_CONFIG_FILE

    @property
    def uv_config_backup_path(self) -> Path:
        """Get UV configuration backup file path."""
        return Path(str(self._dirs.user_config_path)) / UV_CONFIG_BACKUP

    @property
    def uvm_config_path(self) -> Path:
        """Get UVM configuration file path."""
        return Path(str(self._uvm_dirs.user_config_path)) / USER_CONFIG_FILE

    def ensure_uv_config_dir(self) -> Path:
        """Ensure UV config directory exists."""
        config_dir = self.uv_config_path.parent
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def ensure_uvm_config_dir(self) -> Path:
        """Ensure UVM config directory exists."""
        config_dir = self.uvm_config_path.parent
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def read_uv_config(self) -> dict:
        """Read UV configuration file."""
        if not self.uv_config_path.exists():
            return {}

        try:
            with open(self.uv_config_path, "r", encoding="utf-8") as f:
                return tomlkit.load(f).unwrap()
        except (OSError, tomlkit.exceptions.TOMLKitError) as e:
            raise RuntimeError(f"Failed to read UV config: {e}") from e

    def write_uv_config(self, config: dict, create_backup: bool = True) -> None:
        """Write UV configuration file."""
        self.ensure_uv_config_dir()

        # Create backup if file exists and backup is requested
        if create_backup and self.uv_config_path.exists():
            self.create_backup()

        try:
            # Use tomlkit to preserve formatting and comments
            if self.uv_config_path.exists():
                with open(self.uv_config_path, "r", encoding="utf-8") as f:
                    doc = tomlkit.load(f)
            else:
                doc = tomlkit.document()

            # Handle uv section
            uv_config = config.get("uv", {})

            if "uv" in doc:
                uv_section = doc["uv"]

                # Remove all existing keys that are not in the new config
                keys_to_remove = []
                for key in uv_section:
                    if key not in uv_config:
                        keys_to_remove.append(key)

                for key in keys_to_remove:
                    del uv_section[key]

                # Update or add keys from new config
                for key, value in uv_config.items():
                    if key in uv_section:
                        uv_section[key] = value
                    else:
                        uv_section.add(key, value)

                # Remove uv section if empty
                if not uv_config and not uv_section:
                    del doc["uv"]
            elif uv_config:
                # Add new uv section
                doc.add("uv", tomlkit.table())
                uv_section = doc["uv"]
                for key, value in uv_config.items():
                    uv_section.add(key, value)

            # Write the file
            with open(self.uv_config_path, "w", encoding="utf-8") as f:
                tomlkit.dump(doc, f)

        except (OSError, tomlkit.exceptions.TOMLKitError) as e:
            raise RuntimeError(f"Failed to write UV config: {e}") from e

    def get_current_index_url(self) -> Optional[str]:
        """Get current index URL from UV config."""
        config = self.read_uv_config()
        return config.get("uv", {}).get("index_url")

    def set_index_url(self, url: str, create_backup: bool = True) -> None:
        """Set index URL in UV config."""
        config = self.read_uv_config()

        if "uv" not in config:
            config["uv"] = {}

        config["uv"]["index_url"] = url
        self.write_uv_config(config, create_backup)

    def reset_index_url(self, create_backup: bool = True) -> None:
        """Remove index URL from UV config (reset to default)."""
        config = self.read_uv_config()

        if "uv" in config and "index_url" in config["uv"]:
            del config["uv"]["index_url"]
            # Always write the updated config
            self.write_uv_config(config, create_backup)

    def create_backup(self) -> Path:
        """Create backup of current UV config."""
        if not self.uv_config_path.exists():
            raise FileNotFoundError("UV config file does not exist")

        shutil.copy2(self.uv_config_path, self.uv_config_backup_path)
        return self.uv_config_backup_path

    def restore_backup(self) -> None:
        """Restore UV config from backup."""
        if not self.uv_config_backup_path.exists():
            raise FileNotFoundError("UV config backup file does not exist")

        shutil.copy2(self.uv_config_backup_path, self.uv_config_path)

    def read_uvm_config(self) -> dict:
        """Read UVM configuration file."""
        if not self.uvm_config_path.exists():
            return {"meta": {"version": CONFIG_VERSION}, "mirrors": {"custom": {}}}

        try:
            with open(self.uvm_config_path, "r", encoding="utf-8") as f:
                return tomlkit.load(f).unwrap()
        except (OSError, tomlkit.exceptions.TOMLKitError) as e:
            raise RuntimeError(f"Failed to read UVM config: {e}") from e

    def write_uvm_config(self, config: dict) -> None:
        """Write UVM configuration file."""
        self.ensure_uvm_config_dir()

        try:
            doc = tomlkit.document()

            # Add metadata
            if "meta" not in config:
                config["meta"] = {"version": CONFIG_VERSION}

            for section, data in config.items():
                doc.add(section, data)

            with open(self.uvm_config_path, "w", encoding="utf-8") as f:
                tomlkit.dump(doc, f)

        except (OSError, tomlkit.exceptions.TOMLKitError) as e:
            raise RuntimeError(f"Failed to write UVM config: {e}") from e

    def add_custom_mirror(self, name: str, url: str, description: str = "") -> None:
        """Add custom mirror to UVM config."""
        config = self.read_uvm_config()

        if "mirrors" not in config:
            config["mirrors"] = {}
        if "custom" not in config["mirrors"]:
            config["mirrors"]["custom"] = {}

        config["mirrors"]["custom"][name] = {
            "url": url,
            "description": description,
        }

        self.write_uvm_config(config)

    def remove_custom_mirror(self, name: str) -> bool:
        """Remove custom mirror from UVM config."""
        config = self.read_uvm_config()

        custom_mirrors = config.get("mirrors", {}).get("custom", {})
        if name in custom_mirrors:
            del custom_mirrors[name]
            config["mirrors"]["custom"] = custom_mirrors
            self.write_uvm_config(config)
            return True
        return False

    def get_custom_mirrors(self) -> dict:
        """Get all custom mirrors from UVM config."""
        config = self.read_uvm_config()
        return config.get("mirrors", {}).get("custom", {})

    def __repr__(self) -> str:
        """String representation of UVConfig."""
        return f"UVConfig(uv_path={self.uv_config_path}, uvm_path={self.uvm_config_path})"