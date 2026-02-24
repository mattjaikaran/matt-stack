"""Tests for YAML config file parser."""

from __future__ import annotations

from pathlib import Path

from matt_stack.utils.yaml_config import load_config_file


def test_valid_config(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("name: my-app\ntype: fullstack\nvariant: starter\n")
    config = load_config_file(f, tmp_path)
    assert config is not None
    assert config.name == "my-app"


def test_backend_only_config(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("name: my-api\ntype: backend-only\n")
    config = load_config_file(f, tmp_path)
    assert config is not None
    assert config.project_type.value == "backend-only"


def test_with_author(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("name: my-app\nauthor:\n  name: John Doe\n  email: john@example.com\n")
    config = load_config_file(f, tmp_path)
    assert config is not None
    assert config.author_name == "John Doe"
    assert config.author_email == "john@example.com"


def test_default_author_is_empty(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("name: my-app\n")
    config = load_config_file(f, tmp_path)
    assert config is not None
    assert config.author_name == ""
    assert config.author_email == ""


def test_invalid_project_type(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("name: my-app\ntype: invalid\n")
    config = load_config_file(f, tmp_path)
    assert config is None


def test_invalid_variant(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("name: my-app\nvariant: invalid\n")
    config = load_config_file(f, tmp_path)
    assert config is None


def test_invalid_frontend_framework(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("name: my-app\nfrontend:\n  framework: invalid\n")
    config = load_config_file(f, tmp_path)
    assert config is None


def test_invalid_deployment_target(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("name: my-app\ndeployment: invalid\n")
    config = load_config_file(f, tmp_path)
    assert config is None


def test_missing_name(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("type: fullstack\n")
    config = load_config_file(f, tmp_path)
    assert config is None


def test_nonexistent_file(tmp_path: Path) -> None:
    config = load_config_file(tmp_path / "missing.yaml", tmp_path)
    assert config is None


def test_invalid_yaml(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text(": invalid: yaml:\n  - [broken")
    config = load_config_file(f, tmp_path)
    assert config is None


def test_non_mapping_yaml(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("- just\n- a\n- list\n")
    config = load_config_file(f, tmp_path)
    assert config is None


def test_with_ios_and_celery(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("name: my-app\nios: true\nbackend:\n  celery: true\n  redis: true\n")
    config = load_config_file(f, tmp_path)
    assert config is not None
    assert config.include_ios is True
    assert config.use_celery is True


def test_empty_yaml_file(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("")
    config = load_config_file(f, tmp_path)
    assert config is None


def test_empty_name_value(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("name: ''\ntype: fullstack\n")
    config = load_config_file(f, tmp_path)
    assert config is None


def test_name_only_defaults(tmp_path: Path) -> None:
    """Minimal config with just a name should use defaults for all other fields."""
    f = tmp_path / "config.yaml"
    f.write_text("name: minimal-app\n")
    config = load_config_file(f, tmp_path)
    assert config is not None
    assert config.name == "minimal-app"
    assert config.project_type.value == "fullstack"
    assert config.variant.value == "starter"


def test_frontend_only_config(tmp_path: Path) -> None:
    f = tmp_path / "config.yaml"
    f.write_text("name: my-fe\ntype: frontend-only\nfrontend:\n  framework: react-vite-starter\n")
    config = load_config_file(f, tmp_path)
    assert config is not None
    assert config.project_type.value == "frontend-only"
    assert config.frontend_framework.value == "react-vite-starter"


def test_all_fields_populated(tmp_path: Path) -> None:
    """Config with every field explicitly set."""
    f = tmp_path / "config.yaml"
    f.write_text(
        "name: full-app\n"
        "type: fullstack\n"
        "variant: b2b\n"
        "ios: true\n"
        "deployment: railway\n"
        "author:\n"
        "  name: Test Author\n"
        "  email: test@example.com\n"
        "backend:\n"
        "  celery: false\n"
        "  redis: false\n"
        "frontend:\n"
        "  framework: react-vite\n"
    )
    config = load_config_file(f, tmp_path)
    assert config is not None
    assert config.name == "full-app"
    assert config.variant.value == "b2b"
    assert config.include_ios is True
    assert config.deployment.value == "railway"
    assert config.author_name == "Test Author"
    assert config.author_email == "test@example.com"
    assert config.use_celery is False


def test_integer_yaml_content(tmp_path: Path) -> None:
    """YAML that parses to a non-dict type (integer)."""
    f = tmp_path / "config.yaml"
    f.write_text("42\n")
    config = load_config_file(f, tmp_path)
    assert config is None


def test_string_yaml_content(tmp_path: Path) -> None:
    """YAML that parses to a plain string."""
    f = tmp_path / "config.yaml"
    f.write_text("just a string\n")
    config = load_config_file(f, tmp_path)
    assert config is None
