from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Self

from jacobus.core import run


class JacobusRunTests(unittest.TestCase):
    def test_strips_trailing_whitespace_and_outer_blank_lines(
        self: Self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "sample.txt"
            target.write_text(
                "\n\nalpha   \n\n beta\t\t\n\n", encoding="utf-8"
            )

            run(str(root), files=["*.txt"])

            self.assertEqual(
                target.read_text(encoding="utf-8"), "alpha\n\n beta\n"
            )

    def test_rescales_space_indentation_when_indent_is_given(
        self: Self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "sample.py"
            target.write_text("  alpha\n    beta\nplain\n", encoding="utf-8")

            run(str(root), files=["*.py"], indent=4)

            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "    alpha\n        beta\nplain\n",
            )

    def test_unmatched_glob_does_not_touch_files(self: Self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "sample.txt"
            original = "alpha   \n"
            target.write_text(original, encoding="utf-8")

            run(str(root), files=["*.py"])

            self.assertEqual(target.read_text(encoding="utf-8"), original)

    def test_binary_or_invalid_utf8_file_is_left_unchanged_on_decode_error(
        self: Self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "bad.bin"
            original = b"\xff\xfe\x00not utf-8"
            target.write_bytes(original)

            with self.assertRaises(UnicodeDecodeError):
                run(str(root), files=["bad.bin"])

            self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
