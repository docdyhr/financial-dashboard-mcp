#!/usr/bin/env python3
"""Test file to verify Ruff is working."""



# This is a test to check if Ruff catches various issues:
def bad_function(x):
    unused_var = "This should be flagged"  # F841: unused variable
    if x == True:  # E712: comparison to True
        print("bad spacing")  # E201/E202: whitespace issues
    return x


# Long line that exceeds 88 characters should be flagged by E501
very_long_line = (
    "This is a very long line that definitely exceeds the 88 character limit"
)


class TestClass:
    def method(self):
        pass


if __name__ == "__main__":
    result = bad_function(True)
    print(result)
