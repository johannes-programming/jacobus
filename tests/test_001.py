from __future__ import annotations

__all__: list[str] = ["TestJacobusMain"]


import unittest
from typing import Any, Self
from unittest.mock import patch

from jacobus import main


class TestJacobusMain(unittest.TestCase):
    def test_main_no_args(self: Self, /) -> None:
        # Should run without crashing
        main([])

    def test_main_help(self: Self) -> None:
        code: int
        try:
            code = main(["--help"])
        except BaseException as exc:
            self.assertIsNone(exc)
        else:
            self.assertEqual(code, 0)

    @patch("importlib.metadata.version", return_value="1.0.0")
    def test_main_version(self: Self, _: Any, /) -> None:
        code: int
        try:
            code = main(["--version"])
        except BaseException as exc:
            self.assertIsNone(exc)
        else:
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
