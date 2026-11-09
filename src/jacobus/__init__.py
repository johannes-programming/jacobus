from __future__ import annotations

__all__: list[str] = ["main", "parse_args", "run"]


import sys

from jacobus.core import main, parse_args, run

if __name__ == "__main__":
    sys.exit(main())
