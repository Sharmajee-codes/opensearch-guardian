"""Rule Marketplace for Community-Contributed Rules.

This module provides a framework for discovering, loading, and managing
community-contributed diagnostic and optimization rules.
"""

from __future__ import annotations

import hashlib
import json
import logging
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RuleMetadata:
    """Metadata for a marketplace rule."""

    rule_id: str
    name: str
    version: str
    description: str
    author: str
    category: str
    severity: str
    tags: list[str] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)
    source_url: str = ""
    checksum: str = ""
    installed: bool = False
    installed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "category": self.category,
            "severity": self.severity,
            "tags": self.tags,
            "config_schema": self.config_schema,
            "source_url": self.source_url,
            "checksum": self.checksum,
            "installed": self.installed,
            "installed_at": self.installed_at,
        }


class RuleMarketplace:
    """
    Marketplace for discovering and installing community rules.

    Provides a registry of curated diagnostic and optimization rules
    that can be installed and used by the Guardian rules engine.
    """

    MARKETPLACE_URL = "https://raw.githubusercontent.com/opensearch-project/guardian-rules/main/marketplace.json"
    RULES_DIR = Path.home() / ".guardian" / "marketplace" / "rules"

    def __init__(
        self,
        client: Any = None,
        marketplace_url: str = None,
    ):
        """
        Initialize the rule marketplace.

        Args:
            client: OpenSearch client (optional)
            marketplace_url: URL to marketplace index
        """
        self.client = client
        self.marketplace_url = marketplace_url or self.MARKETPLACE_URL
        self.RULES_DIR.mkdir(parents=True, exist_ok=True)

    def list_available_rules(self) -> list[RuleMetadata]:
        """
        List all available rules from the marketplace.

        Returns:
            List of RuleMetadata objects
        """
        try:
            response = urllib.request.urlopen(self.marketplace_url, timeout=10)
            marketplace_data = json.loads(response.read().decode())

            rules = []
            for rule_data in marketplace_data.get("rules", []):
                rule = RuleMetadata(
                    rule_id=rule_data.get("id"),
                    name=rule_data.get("name"),
                    version=rule_data.get("version", "1.0.0"),
                    description=rule_data.get("description", ""),
                    author=rule_data.get("author", "unknown"),
                    category=rule_data.get("category", "general"),
                    severity=rule_data.get("severity", "info"),
                    tags=rule_data.get("tags", []),
                    config_schema=rule_data.get("config_schema", {}),
                    source_url=rule_data.get("source_url", ""),
                    checksum=rule_data.get("checksum", ""),
                    installed=self._is_installed(rule_data.get("id")),
                )
                rules.append(rule)

            return rules

        except Exception as e:
            logger.warning("Failed to fetch marketplace rules: %s", e)
            return []

    def install_rule(self, rule_id: str) -> bool:
        """
        Install a rule from the marketplace.

        Args:
            rule_id: Rule ID to install

        Returns:
            True if installation successful
        """
        try:
            # Fetch marketplace index to get rule details
            response = urllib.request.urlopen(self.marketplace_url, timeout=10)
            marketplace_data = json.loads(response.read().decode())

            # Find the rule
            rule_data = None
            for rule in marketplace_data.get("rules", []):
                if rule.get("id") == rule_id:
                    rule_data = rule
                    break

            if not rule_data:
                logger.error("Rule %s not found in marketplace", rule_id)
                return False

            # Download the rule
            rule_url = rule_data.get("source_url")
            if not rule_url:
                logger.error("No source URL for rule %s", rule_id)
                return False

            rule_response = urllib.request.urlopen(rule_url, timeout=30)
            rule_content = rule_response.read()

            # Verify checksum if provided
            if rule_data.get("checksum"):
                actual_checksum = hashlib.sha256(rule_content).hexdigest()
                if actual_checksum != rule_data["checksum"]:
                    logger.error("Checksum mismatch for rule %s", rule_id)
                    return False

            # Save the rule
            rule_path = self.RULES_DIR / f"{rule_id}.json"
            with open(rule_path, "wb") as f:
                f.write(rule_content)

            logger.info("Installed rule %s", rule_id)
            return True

        except Exception as e:
            logger.error("Failed to install rule %s: %s", rule_id, e)
            return False

    def uninstall_rule(self, rule_id: str) -> bool:
        """
        Uninstall a rule.

        Args:
            rule_id: Rule ID to uninstall

        Returns:
            True if successful
        """
        try:
            rule_path = self.RULES_DIR / f"{rule_id}.json"
            if rule_path.exists():
                rule_path.unlink()
                logger.info("Uninstalled rule %s", rule_id)
                return True
            else:
                logger.warning("Rule %s not installed", rule_id)
                return False
        except Exception as e:
            logger.error("Failed to uninstall rule %s: %s", rule_id, e)
            return False

    def list_installed_rules(self) -> list[RuleMetadata]:
        """
        List all installed rules.

        Returns:
            List of installed RuleMetadata objects
        """
        rules = []
        for rule_file in self.RULES_DIR.glob("*.json"):
            try:
                with open(rule_file) as f:
                    rule_data = json.load(f)
                rule = RuleMetadata(
                    rule_id=rule_data.get("id", rule_file.stem),
                    name=rule_data.get("name", "Unknown"),
                    version=rule_data.get("version", "1.0.0"),
                    description=rule_data.get("description", ""),
                    author=rule_data.get("author", "unknown"),
                    category=rule_data.get("category", "general"),
                    severity=rule_data.get("severity", "info"),
                    tags=rule_data.get("tags", []),
                    config_schema=rule_data.get("config_schema", {}),
                    source_url=rule_data.get("source_url", ""),
                    checksum=rule_data.get("checksum", ""),
                    installed=True,
                    installed_at=datetime.now(UTC).isoformat(),
                )
                rules.append(rule)
            except Exception as e:
                logger.warning("Failed to load rule from %s: %s", rule_file, e)

        return rules

    def _is_installed(self, rule_id: str) -> bool:
        """Check if a rule is installed."""
        return (self.RULES_DIR / f"{rule_id}.json").exists()

    def get_rule(self, rule_id: str) -> RuleMetadata | None:
        """
        Get a specific rule by ID.

        Args:
            rule_id: Rule ID

        Returns:
            RuleMetadata or None if not found
        """
        # Check local installation first
        for rule in self.list_installed_rules():
            if rule.rule_id == rule_id:
                return rule

        # Then check marketplace
        try:
            response = urllib.request.urlopen(self.marketplace_url, timeout=10)
            marketplace_data = json.loads(response.read().decode())

            for rule_data in marketplace_data.get("rules", []):
                if rule_data.get("id") == rule_id:
                    return RuleMetadata(
                        rule_id=rule_data.get("id"),
                        name=rule_data.get("name"),
                        version=rule_data.get("version", "1.0.0"),
                        description=rule_data.get("description", ""),
                        author=rule_data.get("author", "unknown"),
                        category=rule_data.get("category", "general"),
                        severity=rule_data.get("severity", "info"),
                        tags=rule_data.get("tags", []),
                        config_schema=rule_data.get("config_schema", {}),
                        source_url=rule_data.get("source_url", ""),
                        checksum=rule_data.get("checksum", ""),
                    )
        except Exception as e:
            logger.warning("Failed to fetch marketplace: %s", e)

        return None

    def update_rules(self) -> int:
        """
        Update all installed rules to latest versions.

        Returns:
            Number of rules updated
        """
        updated = 0
        installed_rules = self.list_installed_rules()

        for rule in installed_rules:
            if self.install_rule(rule.rule_id):
                updated += 1

        return updated