"Implementation of the *PARAMETER_EXPRESSION keyword."

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class ParameterExpression(LSDynaKeyword):
    """Implements the *PARAMETER_EXPRESSION keyword."""

    keyword_string = "*PARAMETER_EXPRESSION"

    description = (
        "Defines a parameter whose value is computed from an algebraic "
        "expression, which may reference other parameters.  The parameter is "
        "then usable as &name in any later data field."
    )
    manual_section = "Vol I, *PARAMETER_EXPRESSION"

    card_schemas = [
        CardSchema("Card 1", [
            CardField("PRMR1", "A", width=10,
                      description="Parameter name prefixed by its type "
                                  "character: R (real) or I (integer)",
                      required=True),
            CardField("EXPRESSION1", "A", width=70,
                      description="Expression evaluated to give the parameter "
                                  "value; may reference other parameters",
                      required=True),
        ], repeating=True, write_header=True,
           description="One parameter definition per line."),
    ]
