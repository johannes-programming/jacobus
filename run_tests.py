from __future__ import annotations

__all__: list[str] = ["main"]

import sys
import unittest


def main() -> unittest.TextTestResult:
    runner: unittest.TextTestRunner
    suite: unittest.TestSuite
    suite = unittest.TestLoader().discover("tests")
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


if __name__ == "__main__":
    sys.exit(1 - main().wasSuccessful())
