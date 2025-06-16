"""Test file to verify Ruff configuration is working properly."""


def test_function(x, y):  # missing type annotations - should be flagged
    """Test function with various Ruff rule violations."""
    if x == True:  # should suggest x is True instead
        print("Debug message")  # print statement - should be flagged

    try:
        result = 1 / 0
    except:  # bare except - should be flagged
        pass

    return x + y


def another_function():
    pass  # missing return type annotation - should be flagged


if __name__ == "__main__":
    test_function(1, 2)
