"""Implementation of the *SET_SHELL keyword."""

from typing import Dict, List, TextIO
import numpy as np

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema
from dynakw.core.parameter_ref import ParameterRef


class SetShell(LSDynaKeyword):
    """
    Represents a *SET_SHELL keyword in an LS-DYNA input file.

    The keyword is written as ``*SET_SHELL_{OPTION1}_{OPTION2}`` where OPTION2
    is COLLECT and OPTION1 is one of::

        <BLANK>   LIST   COLUMN
        LIST_GENERATE   LIST_GENERATE_INCREMENT   GENERAL

    COLLECT does not change the card layout; only OPTION1 does.  Card 1
    (required, once) holds the set header.  It is followed by exactly one
    repeating Card 2, whose layout OPTION1 selects:

    ==========================  =======  ==================================
    OPTION1                     Card     Repeating unit
    ==========================  =======  ==================================
    <BLANK>, LIST               Card 2a  8 shell element IDs per line
    COLUMN                      Card 2b  1 shell element per line
    LIST_GENERATE               Card 2c  4 begin/end pairs per line
    LIST_GENERATE_INCREMENT     Card 2d  1 block per line
    GENERAL                     Card 2e  1 operation per line
    ==========================  =======  ==================================

    All five variants are stored under the card name ``'Card 2'``; only one is
    ever present.  OPTION1 is resolved by stripping the ``*SET_SHELL`` prefix
    and any ``_COLLECT`` suffix, so the overlapping names (LIST, LIST_GENERATE,
    LIST_GENERATE_INCREMENT) cannot be confused.

    Note that Card 1 of this keyword carries only SID and DA1-DA4; unlike
    *SET_NODE and *SET_SEGMENT it has no SOLVER and no ITS field.  There is
    also no LIST_SMOOTH option.
    """

    keyword_string = "*SET_SHELL"
    keyword_aliases = [
        "*SET_SHELL_COLLECT",
        "*SET_SHELL_LIST",
        "*SET_SHELL_LIST_COLLECT",
        "*SET_SHELL_COLUMN",
        "*SET_SHELL_COLUMN_COLLECT",
        "*SET_SHELL_LIST_GENERATE",
        "*SET_SHELL_LIST_GENERATE_COLLECT",
        "*SET_SHELL_LIST_GENERATE_INCREMENT",
        "*SET_SHELL_LIST_GENERATE_INCREMENT_COLLECT",
        "*SET_SHELL_GENERAL",
        "*SET_SHELL_GENERAL_COLLECT",
    ]

    # Card 1 — set header.  Required, occurs once.  Columns 6, 7 and 8 unused.
    _CARD_1 = CardSchema("Card 1", [
        CardField("SID", "I", width=10),
        CardField("DA1", "F", width=10),
        CardField("DA2", "F", width=10),
        CardField("DA3", "F", width=10),
        CardField("DA4", "F", width=10),
    ], write_header=True)

    # Card 2a — shell element ID cards.  <BLANK> or LIST.
    _CARD_2A = CardSchema("Card 2", [
        CardField(f"EID{i}", "I", width=10) for i in range(1, 9)
    ], repeating=True, write_header=True,
       condition=lambda kw: kw.option1 in ("", "LIST"))

    # Card 2b — shell element ID with column cards.  COLUMN.
    # Columns 6, 7 and 8 are unused.
    _CARD_2B = CardSchema("Card 2", [
        CardField("EID", "I", width=10),
        CardField("A1",  "F", width=10),
        CardField("A2",  "F", width=10),
        CardField("A3",  "F", width=10),
        CardField("A4",  "F", width=10),
    ], repeating=True, write_header=True,
       condition=lambda kw: kw.option1 == "COLUMN")

    # Card 2c — shell element ID range cards.  LIST_GENERATE.
    _CARD_2C = CardSchema("Card 2", [
        CardField(f"B{b}{end}", "I", width=10)
        for b in range(1, 5) for end in ("BEG", "END")
    ], repeating=True, write_header=True,
       condition=lambda kw: kw.option1 == "LIST_GENERATE")

    # Card 2d — shell element ID range with increment cards.
    # LIST_GENERATE_INCREMENT.  Columns 4 to 8 are unused.
    _CARD_2D = CardSchema("Card 2", [
        CardField("BBEG", "I", width=10),
        CardField("BEND", "I", width=10),
        CardField("INCR", "I", width=10),
    ], repeating=True, write_header=True,
       condition=lambda kw: kw.option1 == "LIST_GENERATE_INCREMENT")

    # Card 2e — generalized shell element ID range cards.  GENERAL.
    # Unlike *SET_SEGMENT, E1-E7 are all integers here.
    _CARD_2E = CardSchema("Card 2", [
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

    card_schemas = [_CARD_1, _CARD_2A, _CARD_2B, _CARD_2C, _CARD_2D, _CARD_2E]

    # Cards holding a packed list of element IDs, where a partly filled final
    # line is normal and 0 is never a valid ID.  Absent IDs are written back as
    # blank fields rather than as a literal 0.
    _PACKED_ID_CARDS = (_CARD_2A, _CARD_2C)

    _OPTION1_VALUES = (
        "LIST_GENERATE_INCREMENT",
        "LIST_GENERATE",
        "LIST",
        "COLUMN",
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
        LIST_GENERATE_INCREMENT is never mistaken for LIST or LIST_GENERATE.
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

        if self.option1 == "COLUMN":
            data_lines = [l for l in non_blank if not l.strip().startswith('$')]
            self._apply_attribute_defaults(data_lines[1:])

    def _apply_attribute_defaults(self, element_lines: List[str]):
        """Fill blank shell attributes from the Card 1 defaults (Remark 2).

        On a COLUMN card a blank A1-A4 field means A1 = DA1, A2 = DA2, etc.
        Blank fields otherwise parse as 0, which on write would emit an
        explicit 0.0 and override a non-zero DA value.
        """
        card1 = self.cards.get("Card 1")
        card2 = self.cards.get("Card 2")
        if card1 is None or card2 is None:
            return

        schema = self._CARD_2B
        field_types = [f.type for f in schema.fields]
        field_lens = [f.width for f in schema.fields]

        n_rows = len(card2["EID"])
        blank_rows = {i: [] for i in range(1, 5)}
        for row, line in enumerate(element_lines):
            if row >= n_rows:
                break
            values = self.parser.parse_line(
                line, field_types, field_len=field_lens, default_value=None)
            for i in range(1, 5):
                if values[i] is None:
                    blank_rows[i].append(row)

        for i, rows in blank_rows.items():
            if not rows:
                continue
            default = card1[f"DA{i}"][0]
            column = card2[f"A{i}"]
            # A DA default may itself be a &VAR reference, which a float
            # column cannot hold — widen the column to object first.
            if isinstance(default, ParameterRef) and column.dtype != object:
                column = column.astype(object)
                card2[f"A{i}"] = column
            for row in rows:
                column[row] = default

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
