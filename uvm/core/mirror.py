"""Mirror management functionality."""

from __future__ import annotations

from urllib.parse import urlparse

from uvm.constants import BUILTIN_MIRRORS
from uvm.core.config import UVConfig
from uvm.models.mirror import Mirror


class MirrorManager:
    """Manages built-in and custom mirror sources."""

    def __init__(self) -> None:
        """Initialize mirror manager."""
        self._config = UVConfig()
        self._builtin_mirrors = BUILTIN_MIRRORS.copy()
        self._custom_mirrors: list[Mirror] = []

    def _load_custom_mirrors(self) -> None:
        """Load custom mirrors from configuration."""
        custom_data = self._config.get_custom_mirrors()
        self._custom_mirrors = []

        for name, data in custom_data.items():
            try:
                mirror = Mirror(
                    name=name,
                    url=data["url"],
                    region=data.get("region", "CN"),
                    builtin=False,
                    description=data.get("description", ""),
                )
                self._custom_mirrors.append(mirror)
            except (KeyError, ValueError) as e:
                # Skip invalid custom mirrors
                continue

    @property
    def all_mirrors(self) -> list[Mirror]:
        """Get all mirrors (built-in + custom)."""
        self._load_custom_mirrors()
        return self._builtin_mirrors + self._custom_mirrors

    @property
    def builtin_mirrors(self) -> list[Mirror]:
        """Get built-in mirrors."""
        return self._builtin_mirrors.copy()

    @property
    def custom_mirrors(self) -> list[Mirror]:
        """Get custom mirrors."""
        self._load_custom_mirrors()
        return self._custom_mirrors.copy()

    def get_mirror_by_name(self, name: str) -> Mirror | None:
        """Get mirror by name (case-insensitive)."""
        for mirror in self.all_mirrors:
            if mirror.name.lower() == name.lower():
                return mirror
        return None

    def get_current_mirror(self) -> Mirror | None:
        """Get currently active mirror."""
        current_url = self._config.get_current_index_url()
        if not current_url:
            return None

        # Normalize URLs for comparison
        current_url = current_url.rstrip('/')
        if not current_url.endswith('/simple'):
            current_url += '/simple'

        for mirror in self.all_mirrors:
            mirror_url = str(mirror.url).rstrip('/')
            if mirror_url == current_url:
                return mirror

        return None

    def use_mirror(self, name: str) -> bool:
        """Switch to specified mirror."""
        mirror = self.get_mirror_by_name(name)
        if not mirror:
            return False

        try:
            self._config.set_index_url(str(mirror.url))
            return True
        except Exception:
            return False

    def reset_mirror(self) -> None:
        """Reset to default (official) mirror."""
        self._config.reset_index_url()

    def add_custom_mirror(
        self,
        name: str,
        url: str,
        description: str = "",
        region: str = "CN"
    ) -> bool:
        """Add custom mirror."""
        # Check if name already exists
        existing = self.get_mirror_by_name(name)
        if existing:
            return False

        try:
            Mirror(
                name=name,
                url=url,
                region=region,
                builtin=False,
                description=description,
            )
            self._config.add_custom_mirror(name, url, description)
            return True
        except ValueError:
            return False

    def remove_custom_mirror(self, name: str) -> bool:
        """Remove custom mirror."""
        mirror = self.get_mirror_by_name(name)
        if not mirror or mirror.builtin:
            return False

        return self._config.remove_custom_mirror(name)

    def list_mirrors(self, show_current: bool = True) -> list[dict]:
        """List all mirrors with current status."""
        current_mirror = self.get_current_mirror() if show_current else None
        current_url = self._config.get_current_index_url() if show_current else None

        result = []
        for mirror in self.all_mirrors:
            is_current = (
                current_mirror and mirror.name == current_mirror.name
            ) or (
                not current_mirror and current_url and str(mirror.url) == current_url
            )

            item = {
                "name": mirror.name,
                "url": str(mirror.url),
                "region": mirror.region,
                "builtin": mirror.builtin,
                "description": mirror.description,
                "current": is_current,
            }
            result.append(item)

        return result

    def search_mirrors(self, query: str) -> list[Mirror]:
        """Search mirrors by name or description."""
        query = query.lower()
        results = []

        for mirror in self.all_mirrors:
            if (
                query in mirror.name.lower()
                or query in mirror.description.lower()
                or query in mirror.region.lower()
                or query in mirror.netloc.lower()
            ):
                results.append(mirror)

        return results

    def validate_mirror_url(self, url: str) -> bool:
        """Validate if URL is a valid PyPI mirror URL."""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            if parsed.scheme not in ('http', 'https'):
                return False
            if not url.endswith('/simple'):
                return False
            return True
        except Exception:
            return False

    def get_mirror_statistics(self) -> dict:
        """Get mirror statistics."""
        self._load_custom_mirrors()
        regions = {}
        for mirror in self.all_mirrors:
            region = mirror.region
            regions[region] = regions.get(region, 0) + 1

        return {
            "total_mirrors": len(self.all_mirrors),
            "builtin_mirrors": len(self._builtin_mirrors),
            "custom_mirrors": len(self._custom_mirrors),
            "regions": regions,
            "current_mirror": self.get_current_mirror().name if self.get_current_mirror() else None,
        }

    def export_mirrors(self, format_type: str = "toml") -> str:
        """Export mirrors configuration."""
        if format_type == "toml":
            import tomlkit
            doc = tomlkit.document()

            # Export built-in mirrors
            builtin_data = {}
            for mirror in self._builtin_mirrors:
                builtin_data[mirror.name] = mirror.to_dict()
            doc["builtin_mirrors"] = builtin_data

            # Export custom mirrors
            custom_data = {}
            for mirror in self._custom_mirrors:
                custom_data[mirror.name] = mirror.to_dict()
            doc["custom_mirrors"] = custom_data

            return tomlkit.dumps(doc)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    def __repr__(self) -> str:
        """String representation of MirrorManager."""
        return (
            f"MirrorManager(builtin={len(self._builtin_mirrors)}, "
            f"custom={len(self._custom_mirrors)})"
        )
