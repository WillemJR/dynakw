"""Implementation of the *NODE keyword."""

from typing import List
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


_TC_CHOICES = {
    0: "no constraints",
    1: "constrained x displacement",
    2: "constrained y displacement",
    3: "constrained z displacement",
    4: "constrained x and y displacements",
    5: "constrained y and z displacements",
    6: "constrained z and x displacements",
    7: "constrained x, y and z displacements",
}

_RC_CHOICES = {
    0: "no constraints",
    1: "constrained x rotation",
    2: "constrained y rotation",
    3: "constrained z rotation",
    4: "constrained x and y rotations",
    5: "constrained y and z rotations",
    6: "constrained z and x rotations",
    7: "constrained x, y and z rotations",
}


class Node(LSDynaKeyword):
    """Implements the *NODE keyword."""

    keyword_string = "*NODE"

    description = (
        "Defines a node and its coordinates in the global coordinate system, "
        "and optionally its global-direction boundary conditions.  Node IDs "
        "must be unique within the *NODE section."
    )
    manual_section = "Vol I, *NODE"

    card_schemas = [
        CardSchema("Card 1", [
            CardField("NID", "I", width=8,
                      description="Node number",
                      required=True),
            CardField("X", "F", width=16,
                      description="x coordinate",
                      units="length"),
            CardField("Y", "F", width=16,
                      description="y coordinate",
                      units="length"),
            CardField("Z", "F", width=16,
                      description="z coordinate",
                      units="length"),
            CardField("TC", "I", width=8,
                      description="Translational constraint",
                      choices=_TC_CHOICES),
            CardField("RC", "I", width=8,
                      description="Rotational constraint",
                      choices=_RC_CHOICES),
        ], repeating=True,
           description="One node per line: ID, coordinates and constraints."),
    ]
