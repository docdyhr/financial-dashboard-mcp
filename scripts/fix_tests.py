import os
import re


def fix_test_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".py") and "test" in filename:
            file_path = os.path.join(directory, filename)
            with open(file_path) as file:
                content = file.read()

            # Example fix: Remove trailing whitespace
            fixed_content = re.sub(r"\s+\n", "\n", content)

            # Example fix: Ensure assert statements are correctly formatted
            fixed_content = re.sub(
                r"assert\s+(\w+)\s*==\s*(\w+)", r"assert \1 == \2", fixed_content
            )

            with open(file_path, "w") as file:
                file.write(fixed_content)


if __name__ == "__main__":
    fix_test_files(os.path.dirname(__file__))
