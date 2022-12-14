# --------------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# --------------------------------------------------------------------------------------
from collections.abc import Callable
from collections.abc import Iterator
from contextlib import contextmanager
from copy import copy
from datetime import date
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import cast
from typing import TypeVar
from unittest.mock import patch

import click
from mimesis.builtins import DenmarkSpecProvider
from mimesis.builtins.base import BaseSpecProvider
from pydantic import AnyHttpUrl
from pydantic import BaseModel
from pydantic import parse_obj_as
from pydantic import ValidationError
from ramodels.mo import Validity


def validate_url(ctx: click.Context, param: Any, value: Any) -> AnyHttpUrl:
    try:
        return cast(AnyHttpUrl, parse_obj_as(AnyHttpUrl, value))
    except ValidationError as e:
        raise click.BadParameter(str(e))


class FixedDenmarkSpecProvider(DenmarkSpecProvider):
    """
    Mimesis DenmarkSpecProvider, but actually allowing you to specify the randomisation
    parameters instead of just hard-coding it (actually wtf?). Hideous implementation,
    but that's what you get for working with hideous libraries.
    """

    def cpr(self, start: int = 1858, end: int = 2021) -> str:
        orig_date = self._datetime.date

        def patched_date(*args: Any, **kwargs: Any) -> date:
            return orig_date(start=start, end=end)  # type: ignore[no-any-return]

        with patch.object(self._datetime, "date", patched_date):
            return super().cpr()  # type: ignore[no-any-return]


class PNummer(BaseSpecProvider):
    class Meta:
        name = "pnummer"

    def _gen_x_digit_number(self, n: int) -> str:
        assert n > 0
        number = self.random.randint(0, 10**n - 1)
        return str(number).zfill(n)

    def pnumber(self) -> str:
        return self._gen_x_digit_number(10)


CallableReturnType = TypeVar("CallableReturnType")
OrgTree = dict[str, dict]


EmployeeValidity = Validity(
    # Bounding when any employee will be valid from. This is used to generate employees,
    # and subsequently to generate associated objects without having to parse the CPR
    # back to a date.
    from_date=datetime.now().date() - timedelta(days=365 * 30),
    to_date=None,
)


def tree_visitor(
    tree: OrgTree,
    yield_func: Callable[[str, int, str], CallableReturnType],
    level: int = 1,
    prefix: str = "",
) -> Iterator[CallableReturnType]:
    for name, children in tree.items():
        yield yield_func(name, level, prefix)
        yield from tree_visitor(children, yield_func, level + 1, prefix + name)


def tree_visitor_levels(
    tree: OrgTree,
    yield_func: Callable[[str, int, str], CallableReturnType],
    level: int = 1,
    prefix: str = "",
) -> Iterator[CallableReturnType]:
    for name, children in tree.items():
        yield yield_func(name, level, prefix)
    for name, children in tree.items():
        yield from tree_visitor_levels(children, yield_func, level + 1, prefix + name)


T = TypeVar("T", bound=BaseModel)


@contextmanager
def thawed(obj: T) -> Iterator[T]:
    config = obj.__config__
    original_config = copy(config)
    try:
        config.frozen = False
        config.validate_assignment = True
        yield obj
    finally:
        config.frozen = original_config.frozen
        config.validate_assignment = original_config.validate_assignment
