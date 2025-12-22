"""
Unit tests for Configuration Management.

Part of Sprint 44 - SDLC Structure Scanner Engine.
"""

import json
from pathlib import Path

import pytest

from sdlcctl.validation import (
    RuleConfig,
    ScannerConfig,
    ConfigLoader,
    load_config,
    Severity,
)


class TestRuleConfig:
    """Test RuleConfig dataclass."""

    def test_create_rule_config(self):
        """Test creating a basic rule config."""
        rule = RuleConfig(
            rule_id="STAGE-001",
            enabled=True,
            severity=Severity.ERROR,
            auto_fix=True,
        )

        assert rule.rule_id == "STAGE-001"
        assert rule.enabled is True
        assert rule.severity == Severity.ERROR
        assert rule.auto_fix is True
        assert rule.options == {}

    def test_rule_config_defaults(self):
        """Test rule config default values."""
        rule = RuleConfig(rule_id="TEST-001")

        assert rule.enabled is True
        assert rule.severity is None
        assert rule.auto_fix is None
        assert rule.options == {}

    def test_rule_config_with_options(self):
        """Test rule config with custom options."""
        rule = RuleConfig(
            rule_id="STAGE-001",
            options={"max_depth": 3, "check_readme": True},
        )

        assert rule.options["max_depth"] == 3
        assert rule.options["check_readme"] is True

    def test_rule_config_from_dict(self):
        """Test creating rule config from dictionary."""
        data = {
            "enabled": True,
            "severity": "WARNING",
            "auto_fix": False,
            "options": {"key": "value"},
        }

        rule = RuleConfig.from_dict("TEST-001", data)

        assert rule.rule_id == "TEST-001"
        assert rule.enabled is True
        assert rule.severity == Severity.WARNING
        assert rule.auto_fix is False
        assert rule.options == {"key": "value"}

    def test_rule_config_from_dict_minimal(self):
        """Test creating rule config from minimal dictionary."""
        data = {}

        rule = RuleConfig.from_dict("TEST-001", data)

        assert rule.rule_id == "TEST-001"
        assert rule.enabled is True
        assert rule.severity is None

    def test_rule_config_to_dict(self):
        """Test converting rule config to dictionary."""
        rule = RuleConfig(
            rule_id="STAGE-001",
            enabled=False,
            severity=Severity.ERROR,
            auto_fix=True,
            options={"test": "value"},
        )

        data = rule.to_dict()

        assert data["enabled"] is False
        assert data["severity"] == "ERROR"
        assert data["auto_fix"] is True
        assert data["options"] == {"test": "value"}

    def test_rule_config_to_dict_minimal(self):
        """Test converting minimal rule config to dictionary."""
        rule = RuleConfig(rule_id="TEST-001")

        data = rule.to_dict()

        assert "enabled" in data
        assert data["enabled"] is True
        # Should not include None values
        assert "severity" not in data or data.get("severity") is None


class TestScannerConfig:
    """Test ScannerConfig dataclass."""

    def test_create_scanner_config(self):
        """Test creating scanner config."""
        config = ScannerConfig(
            validators=["stage-folder", "naming-convention"],
            max_workers=8,
            docs_root="documentation",
        )

        assert config.validators == ["stage-folder", "naming-convention"]
        assert config.max_workers == 8
        assert config.docs_root == "documentation"

    def test_scanner_config_defaults(self):
        """Test scanner config default values."""
        config = ScannerConfig()

        assert config.validators == []
        assert config.rules == {}
        assert config.ignore_patterns == set()
        assert config.max_workers == 4
        assert config.docs_root is None
        assert config.fail_on_error is True
        assert config.fail_on_warning is False
        assert config.output_format == "text"

    def test_scanner_config_from_dict(self):
        """Test creating scanner config from dictionary."""
        data = {
            "validators": ["stage-folder", "naming-convention"],
            "rules": {
                "STAGE-001": {"enabled": True, "severity": "ERROR"},
                "NUM-001": {"enabled": False},
            },
            "ignore_patterns": ["**/node_modules/**", "**/.git/**"],
            "max_workers": 8,
            "docs_root": "docs",
            "fail_on_error": True,
            "fail_on_warning": True,
            "output_format": "json",
        }

        config = ScannerConfig.from_dict(data)

        assert config.validators == ["stage-folder", "naming-convention"]
        assert len(config.rules) == 2
        assert "STAGE-001" in config.rules
        assert config.rules["STAGE-001"].severity == Severity.ERROR
        assert config.ignore_patterns == {"**/node_modules/**", "**/.git/**"}
        assert config.max_workers == 8
        assert config.fail_on_warning is True
        assert config.output_format == "json"

    def test_scanner_config_to_dict(self):
        """Test converting scanner config to dictionary."""
        config = ScannerConfig(
            validators=["stage-folder"],
            max_workers=6,
            ignore_patterns={"**/test/**"},
        )

        data = config.to_dict()

        assert data["validators"] == ["stage-folder"]
        assert data["max_workers"] == 6
        assert "**/test/**" in data["ignore_patterns"]

    def test_get_rule_config(self):
        """Test getting rule configuration."""
        rule = RuleConfig(rule_id="STAGE-001", enabled=False)
        config = ScannerConfig(rules={"STAGE-001": rule})

        retrieved = config.get_rule_config("STAGE-001")
        assert retrieved is not None
        assert retrieved.enabled is False

        missing = config.get_rule_config("NONEXISTENT")
        assert missing is None

    def test_is_rule_enabled(self):
        """Test checking if rule is enabled."""
        config = ScannerConfig(
            rules={
                "STAGE-001": RuleConfig(rule_id="STAGE-001", enabled=True),
                "STAGE-002": RuleConfig(rule_id="STAGE-002", enabled=False),
            }
        )

        assert config.is_rule_enabled("STAGE-001") is True
        assert config.is_rule_enabled("STAGE-002") is False
        # Default enabled if not configured
        assert config.is_rule_enabled("UNKNOWN") is True

    def test_get_rule_severity(self):
        """Test getting rule severity with fallback."""
        config = ScannerConfig(
            rules={
                "STAGE-001": RuleConfig(
                    rule_id="STAGE-001", severity=Severity.WARNING
                ),
                "STAGE-002": RuleConfig(rule_id="STAGE-002"),  # No severity
            }
        )

        # Configured severity
        assert config.get_rule_severity("STAGE-001", Severity.ERROR) == Severity.WARNING

        # Default severity
        assert config.get_rule_severity("STAGE-002", Severity.ERROR) == Severity.ERROR
        assert config.get_rule_severity("UNKNOWN", Severity.INFO) == Severity.INFO

    def test_is_auto_fix_enabled(self):
        """Test checking if auto-fix is enabled."""
        config = ScannerConfig(
            rules={
                "STAGE-001": RuleConfig(rule_id="STAGE-001", auto_fix=True),
                "STAGE-002": RuleConfig(rule_id="STAGE-002", auto_fix=False),
                "STAGE-003": RuleConfig(rule_id="STAGE-003"),  # No auto_fix set
            }
        )

        assert config.is_auto_fix_enabled("STAGE-001") is True
        assert config.is_auto_fix_enabled("STAGE-002") is False
        assert config.is_auto_fix_enabled("STAGE-003", default=True) is True
        assert config.is_auto_fix_enabled("UNKNOWN", default=False) is False

    def test_should_ignore(self, tmp_path):
        """Test path ignore checking."""
        config = ScannerConfig(
            ignore_patterns={"**/node_modules/**", "**/.git/**", "**/test/**"}
        )

        assert config.should_ignore(tmp_path / "node_modules" / "pkg") is True
        assert config.should_ignore(tmp_path / ".git" / "config") is True
        assert config.should_ignore(tmp_path / "test" / "file.py") is True
        assert config.should_ignore(tmp_path / "src" / "main.py") is False


class TestConfigLoader:
    """Test ConfigLoader class."""

    def test_create_config_loader(self, tmp_path):
        """Test creating config loader."""
        loader = ConfigLoader(tmp_path)

        assert loader.project_root == tmp_path

    def test_load_default_config(self, tmp_path):
        """Test loading default config when no file exists."""
        loader = ConfigLoader(tmp_path)
        config = loader.load()

        # Should return default config
        assert len(config.validators) == 5  # Default validators
        assert config.max_workers == 4

    def test_load_config_from_file(self, tmp_path):
        """Test loading config from .sdlc-config.json."""
        config_data = {
            "validators": ["stage-folder"],
            "max_workers": 8,
            "output_format": "json",
        }

        config_file = tmp_path / ".sdlc-config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        loader = ConfigLoader(tmp_path)
        config = loader.load()

        assert config.validators == ["stage-folder"]
        assert config.max_workers == 8
        assert config.output_format == "json"

    def test_find_config_in_parent(self, tmp_path):
        """Test finding config file in parent directory."""
        # Create nested structure
        subdir = tmp_path / "docs" / "subfolder"
        subdir.mkdir(parents=True)

        # Place config in root
        config_data = {"max_workers": 6}
        config_file = tmp_path / ".sdlc-config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Load from subdirectory
        loader = ConfigLoader(tmp_path)
        config = loader.load(search_path=subdir)

        assert config.max_workers == 6

    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON file."""
        config_file = tmp_path / ".sdlc-config.json"
        with open(config_file, "w") as f:
            f.write("{ invalid json }")

        loader = ConfigLoader(tmp_path)
        config = loader.load()

        # Should fall back to default config
        assert config.max_workers == 4

    def test_validate_config_schema(self, tmp_path):
        """Test config schema validation."""
        loader = ConfigLoader(tmp_path)

        # Valid config
        valid_data = {
            "validators": ["stage-folder"],
            "max_workers": 4,
            "output_format": "json",
        }
        loader._validate_config_schema(valid_data)  # Should not raise

        # Invalid validators type
        with pytest.raises(ValueError, match="must be a list"):
            loader._validate_config_schema({"validators": "not-a-list"})

        # Invalid max_workers
        with pytest.raises(ValueError, match="must be a positive integer"):
            loader._validate_config_schema({"max_workers": 0})

        # Invalid output_format
        with pytest.raises(ValueError, match="must be one of"):
            loader._validate_config_schema({"output_format": "invalid"})

    def test_save_config(self, tmp_path):
        """Test saving config to file."""
        config = ScannerConfig(
            validators=["stage-folder"],
            max_workers=8,
        )

        loader = ConfigLoader(tmp_path)
        output_path = loader.save(config)

        assert output_path.exists()

        # Load it back
        with open(output_path) as f:
            data = json.load(f)

        assert data["validators"] == ["stage-folder"]
        assert data["max_workers"] == 8

    def test_save_config_custom_path(self, tmp_path):
        """Test saving config to custom path."""
        config = ScannerConfig(max_workers=6)
        custom_path = tmp_path / "custom-config.json"

        loader = ConfigLoader(tmp_path)
        output_path = loader.save(config, custom_path)

        assert output_path == custom_path
        assert custom_path.exists()


class TestLoadConfigFunction:
    """Test load_config convenience function."""

    def test_load_config_function(self, tmp_path):
        """Test load_config convenience function."""
        config_data = {"max_workers": 7}
        config_file = tmp_path / ".sdlc-config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = load_config(tmp_path)

        assert config.max_workers == 7

    def test_load_config_with_search_path(self, tmp_path):
        """Test load_config with search path."""
        subdir = tmp_path / "docs"
        subdir.mkdir()

        config_data = {"max_workers": 5}
        config_file = tmp_path / ".sdlc-config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = load_config(tmp_path, search_path=subdir)

        assert config.max_workers == 5
