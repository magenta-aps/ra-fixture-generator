# --------------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# --------------------------------------------------------------------------------------
import random
from uuid import UUID

import more_itertools
from ramodels.mo import Employee
from ramodels.mo import OrganisationUnit
from ramodels.mo.details import Association

from ..util import EmployeeValidity
from .base import BaseGenerator


class AssociationGenerator(BaseGenerator):
    def __init__(self, association_types: dict[str, UUID]) -> None:
        super().__init__()
        self.association_type_uuids = list(association_types.values())

    def generate(
        self,
        org_layers: list[list[OrganisationUnit]],
        employees: list[Employee],
        employees_per_org: int,
    ) -> list[list[Association]]:
        print("Generating associations")

        def construct_association(org_unit: OrganisationUnit) -> Association:
            employee = random.choice(employees)
            return Association.from_simplified_fields(
                org_unit_uuid=org_unit.uuid,
                person_uuid=employee.uuid,
                association_type_uuid=random.choice(self.association_type_uuids),
                **self.random_validity(org_unit.validity, EmployeeValidity).dict(),
            )

        def construct_associations(org_unit: OrganisationUnit) -> list[Association]:
            return [
                construct_association(org_unit)
                for _ in range(random.randint(0, employees_per_org))
            ]

        return [
            list(more_itertools.flatten(map(construct_associations, layer)))
            for layer in org_layers
        ]
