"""Script to add missing @pytest.mark.asyncio decorators to async test functions."""

from pathlib import Path
import re


def fix_async_tests(root_dir: str = "tests"):
    """Add @pytest.mark.asyncio decorator to async test functions that are missing it."""
    test_files = list(Path(root_dir).glob("**/*.py"))

    for file_path in test_files:
        if file_path.name.startswith("test_") or file_path.name.endswith("_test.py"):
            fix_file(file_path)


def fix_file(file_path: Path):
    """Fix a single test file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Pattern to match async test functions without @pytest.mark.asyncio
        pattern = r"(\n    )(?!.*@pytest\.mark\.asyncio)(.*\n    async def test_[^(]+\([^)]*\):)"

        def replacement(match):
            indent = match.group(1)
            rest = match.group(2)
            return f"{indent}@pytest.mark.asyncio{indent}{rest}"

        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

        if new_content != content:
            print(f"Fixed async tests in: {file_path}")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

    except (OSError, UnicodeDecodeError) as e:
        print(f"Error processing {file_path}: {e}")


if __name__ == "__main__":
    fix_async_tests()
    print("Done fixing async test decorators!")
