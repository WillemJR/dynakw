"""Implementation of the *NODE keyword."""

from typing import List
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class Node(LSDynaKeyword):
    """Implements the *NODE keyword."""

    keyword_string = "*NODE"

    card_schemas = [
        CardSchema("Card 1", [
            CardField("NID", "I", width=8),
            CardField("X",   "F", width=16),
            CardField("Y",   "F", width=16),
            CardField("Z",   "F", width=16),
            CardField("TC",  "I", width=8),
            CardField("RC",  "I", width=8),
        ], repeating=True)
    ]
