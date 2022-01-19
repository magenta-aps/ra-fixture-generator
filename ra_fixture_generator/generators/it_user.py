# --------------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# --------------------------------------------------------------------------------------
import random
from uuid import UUID

import more_itertools
from mimesis import Person
from ramodels.mo import Employee
from ramodels.mo.details import ITUser

from .base import BaseGenerator
from ..util import EmployeeValidity


class ITUserGenerator(BaseGenerator):
    def __init__(self) -> None:
        super().__init__()
        self.person_gen = Person("da")

    def generate(
        self, employees: list[Employee], it_systems: dict[str, UUID]
    ) -> list[ITUser]:
        it_systems_uuids = list(it_systems.values())

        def construct_it_users(employee: Employee) -> list[ITUser]:
            return [
                ITUser.from_simplified_fields(
                    user_key=self.person_gen.username(mask="ld"),
                    itsystem_uuid=it_system_uuid,
                    person_uuid=employee.uuid,
                    **self.random_validity(EmployeeValidity).dict(),
                )
                for it_system_uuid in it_systems_uuids
                if random.random() < 0.6
            ]

        return list(more_itertools.flatten(map(construct_it_users, employees)))
