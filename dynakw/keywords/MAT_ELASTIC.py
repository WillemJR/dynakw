"""Implementation of the *MAT_ELASTIC keyword."""

from typing import List
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class MatElastic(LSDynaKeyword):
    """
    Represents a *MAT_ELASTIC keyword in an LS-DYNA input file.

    This keyword can appear as *MAT_ELASTIC or *MAT_001, with an
    optional _FLUID suffix for fluid material modeling.
    """

    keyword_string = "*MAT_ELASTIC"
    keyword_aliases = ["*MAT_001", "*MAT_ELASTIC_FLUID", "*MAT_001_FLUID"]

    card_schemas = [
        # Card 1 — solid variant (no _FLUID suffix)
        CardSchema("Card 1", [
            CardField("MID", "A", width=10),
            CardField("RO",  "F", width=10),
            CardField("E",   "F", width=10),
            CardField("PR",  "F", width=10),
            CardField("DA",  "F", width=10),
            CardField("DB",  "F", width=10),
            CardField("K",   "F", width=10),
        ], condition=lambda kw: not kw.is_fluid, write_header=True),

        # Card 1 — fluid variant (_FLUID suffix)
        CardSchema("Card 1", [
            CardField("MID", "A", width=10),
            CardField("RO",  "F", width=10),
            CardField("K",   "F", width=10),
        ], condition=lambda kw: kw.is_fluid, write_header=True),

        # Card 2 — fluid only
        CardSchema("Card 2", [
            CardField("VC",  "F", width=10),
            CardField("CP",  "F", width=10),
        ], condition=lambda kw: kw.is_fluid, write_header=True),
    ]

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        self.is_fluid = "_FLUID" in keyword_name.upper()
        super().__init__(keyword_name, raw_lines)
