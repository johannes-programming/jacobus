import unittest
from typing import Any, Self
from unittest.mock import patch

from jacobus import main

__all__ = ["TestJacobusMain"]


class TestJacobusMain(unittest.TestCase):
    def test_main_no_args(self: Self) -> None:
        # Should run without crashing
        main([])

    def test_main_help(self: Self) -> None:
        # argparse exits after printing help
        with self.assertRaises(SystemExit) as cm:
            main(["--help"])
        self.assertEqual(cm.exception.code, 0)

    @patch("importlib.metadata.version", return_value="1.0.0")
    def test_main_version(self: Self, _: Any) -> None:
        # argparse exits after printing version
        with self.assertRaises(SystemExit) as cm:
            main(["--version"])
        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
