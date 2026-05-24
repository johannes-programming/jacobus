import enum
import functools
import tomllib
from importlib import resources
from typing import Any, Self

__all__ = ["Const"]


class Const(enum.StrEnum):
    const = "jacobus.const/const.toml"

    @functools.cached_property
    def data(self: Self) -> dict[str, Any]:
        text: str
        text = resources.read_text(*self.value.split("/"))
        return tomllib.loads(text)

    @functools.cached_property
    def varia(self: Self) -> dict[str, Any]:
        ans: Any
        ans = self.data.get("varia")
        if isinstance(ans, dict):
            return ans
        else:
            return dict()
