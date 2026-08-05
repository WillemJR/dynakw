"""Implementation of the *SET_SOLID keyword."""

from typing import Dict, List, TextIO
import numpy as np

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema
from dynakw.core.parameter_ref import ParameterRef


class SetSolid(LSDynaKeyword):
    """
    Represents a *SET_SOLID keyword in an LS-DYNA input file.

    The keyword is written as ``*SET_SOLID_{OPTION1}_{OPTION2}`` where OPTION2
    is COLLECT and OPTION1 is one of::

        <BLANK>   GENERATE   GENERATE_INCREMENT   GENERAL

    COLLECT does not change the card layout; only OPTION1 does.  Card 1
    (required, once) holds the set header.  It is followed by exactly one
    repeating Card 2, whose layout OPTION1 selects:

    ====================  =======  ==================================
    OPTION1               Card     Repeating unit
    ====================  =======  ==================================
    <BLANK>               Card 2a  8 solid element IDs per line
    GENERATE              Card 2b  4 begin/end pairs per line
    GENERATE_INCREMENT    Card 2c  1 block per line
    GENERAL               Card 2d  1 operation per line
    ====================  =======  ==================================

    All four variants are stored under the card name ``'Card 2'``; only one is
    ever present.  OPTION1 is resolved by stripping the ``*SET_SOLID`` prefix
    and any ``_COLLECT`` suffix, so GENERATE_INCREMENT is never mistaken for
    GENERATE, and GENERAL is never mistaken for GENERATE.

    Note that Card 1 of this keyword carries only SID and SOLVER; unlike
    *SET_NODE and *SET_SHELL it has no DA1-DA4 attribute defaults, and so this
    keyword has no per-element attribute card and no LIST or COLUMN option.
    """

    keyword_string = "*SET_SOLID"
    keyword_aliases = [
        "*SET_SOLID_COLLECT",
        "*SET_SOLID_GENERATE",
        "*SET_SOLID_GENERATE_COLLECT",
        "*SET_SOLID_GENERATE_INCREMENT",
        "*SET_SOLID_GENERATE_INCREMENT_COLLECT",
        "*SET_SOLID_GENERAL",
        "*SET_SOLID_GENERAL_COLLECT",
    ]

    # Card 1 — set header.  Required, occurs once.  Columns 3 to 8 unused.
    _CARD_1 = CardSchema("Card 1", [
        CardField("SID",    "I", width=10),
        CardField("SOLVER", "A", width=10),
    ], write_header=True)

    # Card 2a — solid element ID cards.  <BLANK>.
    _CARD_2A = CardSchema("Card 2", [
        CardField(f"K{i}", "I", width=10) for i in range(1, 9)
    ], repeating=True, write_header=True,
       condition=lambda kw: kw.option1 == "")

    # Card 2b — solid element ID range cards.  GENERATE.
    _CARD_2B = CardSchema("Card 2", [
        CardField(f"B{b}{end}", "I", width=10)
        for b in range(1, 5) for end in ("BEG", "END")
    ], repeating=True, write_header=True,
       condition=lambda kw: kw.option1 == "GENERATE")

    # Card 2c — solid element ID range with increment cards.
    # GENERATE_INCREMENT.  Columns 4 to 8 are unused.
    _CARD_2C = CardSchema("Card 2", [
        CardField("BBEG", "I", width=10),
        CardField("BEND", "I", width=10),
        CardField("INCR", "I", width=10),
    ], repeating=True, write_header=True,
       condition=lambda kw: kw.option1 == "GENERATE_INCREMENT")

    # Card 2d — generalized solid element ID range cards.  GENERAL.
    # Unlike *SET_SEGMENT, E1-E7 are all integers here.
    _CARD_2D = CardSchema("Card 2", [
        CardField("OPTION", "A", width=10),
        CardField("E1",     "I", width=10),
        CardField("E2",     "I", width=10),
        CardField("E3",     "I", width=10),
        CardField("E4",     "I", width=10),
        CardField("E5",     "I", width=10),
        CardField("E6",     "I", width=10),
        CardField("E7",     "I", width=10),
    ], repeating=True, write_header=True,
       condition=lambda kw: kw.option1 == "GENERAL")

    card_schemas = [_CARD_1, _CARD_2A, _CARD_2B, _CARD_2C, _CARD_2D]

    # Cards holding a packed list of element IDs, where a partly filled final
    # line is normal and 0 is never a valid ID.  Absent IDs are written back as
    # blank fields rather than as a literal 0.
    _PACKED_ID_CARDS = (_CARD_2A, _CARD_2B)

    _OPTION1_VALUES = (
        "GENERATE_INCREMENT",
        "GENERATE",
        "GENERAL",
        "",
    )

    def __init__(self, keyword_name: str, raw_lines: List[str] = None,
                 start_line: int = None):
        # Set before super().__init__ — the card conditions are evaluated
        # while the raw data is parsed.
        self.option1 = self._parse_option1(keyword_name)
        super().__init__(keyword_name, raw_lines, start_line)

    @classmethod
    def _parse_option1(cls, keyword_name: str) -> str:
        """Return the OPTION1 value ('' for <BLANK>) for a keyword name.

        The suffix is taken literally rather than matched by prefix, so
        GENERATE_INCREMENT is never mistaken for GENERATE.
        """
        suffix = keyword_name.strip().upper()
        if suffix.startswith(cls.keyword_string):
            suffix = suffix[len(cls.keyword_string):]
        if suffix.endswith("_COLLECT"):
            suffix = suffix[:-len("_COLLECT")]
        suffix = suffix.lstrip("_")
        return suffix if suffix in cls._OPTION1_VALUES else ""

    def _parse_raw_data(self, raw_lines: List[str]):
        """Parse using the declarative schemas, ignoring blank lines.

        Blank lines are dropped so that trailing whitespace at the end of a
        block does not become a spurious all-zero data row.
        """
        non_blank = [line for line in raw_lines[1:] if line.strip()]
        super()._parse_raw_data([raw_lines[0]] + non_blank)

        # An empty SOLVER field parses as 0; restore the documented default
        # so that the field is written back as a valid solver name.
        card1 = self.cards.get("Card 1")
        if card1 is not None and "SOLVER" in card1:
            solver = card1["SOLVER"][0]
            if solver is None or str(solver).strip() in ("", "0"):
                card1["SOLVER"][0] = "MECH"

    def _write_card(self, file_obj: TextIO, card: Dict[str, np.ndarray],
                    schema: CardSchema):
        """Write one card, blanking absent IDs on the packed element ID cards.

        The final line of a packed list is normally only partly filled.  Those
        trailing fields parse as 0, and writing them back as a literal 0 would
        add element IDs of 0 to the set, so they are written as blanks instead.
        """
        if not any(schema is s for s in self._PACKED_ID_CARDS):
            super()._write_card(file_obj, card, schema)
            return

        if schema.write_header:
            file_obj.write(self.parser.format_header(
                [f.header_name or f.name for f in schema.fields],
                field_len=[f.width for f in schema.fields],
            ))

        n_rows = len(card[schema.fields[0].name])
        for idx in range(n_rows):
            parts = []
            for f in schema.fields:
                value = card[f.name][idx]
                if not isinstance(value, ParameterRef) and value == 0:
                    parts.append(' ' * f.width)
                else:
                    parts.append(self.parser.format_field(
                        value, f.type, field_len=f.width))
            file_obj.write(''.join(parts).rstrip() + '\n')
