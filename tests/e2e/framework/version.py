import tomllib
from pathlib import Path


def expected_version() -> str | None:
    """Version of this checkout, which the CLI under test must report.

    None in the test image, which ships tests/e2e without pyproject.toml.
    """
    pyproject = Path(__file__).parents[3] / "pyproject.toml"
    if pyproject.is_file():
        return tomllib.loads(pyproject.read_text())["project"]["version"]
    return None
