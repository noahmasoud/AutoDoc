import pytest

from services.rules_engine import match_rule


@pytest.mark.parametrize(
    ("selector", "path", "expected"),
    [
        ("src/**/*.py", "src/app/main.py", True),
        ("src/**/*.py", "src/styles.css", False),
        ("**/*.ts", "src/app/pages/rules/rules.component.ts", True),
        ("regex:^src/app/.*\\.ts$", "src/app/pages/rules/rules.component.ts", True),
        ("regex:^src/app/.*\\.ts$", "src/lib/index.js", False),
        ("docs/**", "docs/README.md", True),
        ("docs/**", "src/docs/file.md", False),
        ("**/*.md", "docs/guide.md", True),
        ("**/*.md", "docs/image.png", False),
        ("regex:service$", "my_service", True),
        ("regex:service$", "service/test", False),
    ],
)
def test_match_rule(selector: str, path: str, expected: bool) -> None:
    assert match_rule(selector, path) is expected
