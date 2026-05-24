import unittest


def test() -> unittest.TextTestResult:
    loader = unittest.TestLoader()
    tests = loader.discover(start_dir="jacobus.tests")
    runner = unittest.TextTestRunner()
    result = runner.run(tests)
    return result
