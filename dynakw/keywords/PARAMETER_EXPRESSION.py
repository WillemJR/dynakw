"Implementation of the *PARAMETER_EXPRESSION keyword."

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class ParameterExpression(LSDynaKeyword):
    """Implements the *PARAMETER_EXPRESSION keyword."""

    keyword_string = "*PARAMETER_EXPRESSION"

    card_schemas = [
        CardSchema("Card 1", [
            CardField("PRMR1",       "A", width=10),
            CardField("EXPRESSION1", "A", width=70),
        ], repeating=True, write_header=True),
    ]
