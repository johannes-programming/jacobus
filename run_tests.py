import unittest

__all__ = ["main"]


def main() -> unittest.TextTestResult:
    suite: unittest.TestSuite
    runner: unittest.TextTestRunner
    suite = unittest.TestLoader().discover("tests")
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


if __name__ == "__main__":
    main()
