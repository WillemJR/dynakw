"""Implementation of the *SET_NODE keyword."""

from typing import Dict, List, TextIO
import numpy as np

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema
from dynakw.core.parameter_ref import ParameterRef


class SetNode(LSDynaKeyword):
    """
    Represents a *SET_NODE keyword in an LS-DYNA input file.

    The keyword is written as ``*SET_NODE_{OPTION1}_{OPTION2}`` where OPTION2
    is COLLECT and OPTION1 is one of::

        <BLANK>   LIST   COLUMN   LIST_GENERATE
        LIST_GENERATE_INCREMENT   GENERAL   LIST_SMOOTH

    COLLECT does not change the card layout; only OPTION1 does.  Card 1
    (required, once) holds the set header.  It is followed by exactly one
    repeating Card 2, whose layout OPTION1 selects:

    ==========================  =======  ==============================
    OPTION1                     Card     Repeating unit
    ==========================  =======  ==============================
    <BLANK>, LIST, LIST_SMOOTH  Card 2a  8 node IDs per line
    COLUMN                      Card 2b  1 node per line
    LIST_GENERATE               Card 2c  4 begin/end pairs per line
    LIST_GENERATE_INCREMENT     Card 2d  1 block per line
    GENERAL                     Card 2e  1 operation per line
    ==========================  =======  ==============================

    All five variants are stored under the card name ``'Card 2'``; only one is
    ever present.  OPTION1 is resolved by stripping the ``*SET_NODE`` prefix
    and any ``_COLLECT`` suffix, so the overlapping names (LIST,
    LIST_GENERATE, LIST_GENERATE_INCREMENT, LIST_SMOOTH) cannot be confused.
    """

    keyword_string = "*SET_NODE"
    keyword_aliases = [
        "*SET_NODE_COLLECT",
        "*SET_NODE_LIST",
        "*SET_NODE_LIST_COLLECT",
        "*SET_NODE_COLUMN",
        "*SET_NODE_COLUMN_COLLECT",
        "*SET_NODE_LIST_GENERATE",
        "*SET_NODE_LIST_GENERATE_COLLECT",
        "*SET_NODE_LIST_GENERATE_INCREMENT",
        "*SET_NODE_LIST_GENERATE_INCREMENT_COLLECT",
        "*SET_NODE_GENERAL",
        "*SET_NODE_GENERAL_COLLECT",
        "*SET_NODE_LIST_SMOOTH",
        "*SET_NODE_LIST_SMOOTH_COLLECT",
    ]

    description = (
        "Defines a set of nodes, referenced by ID from keywords that act on "
        "groups of nodes.  OPTION1 selects how the members are listed: "
        "explicitly, one per line with attributes, or as generated ID ranges."
    )
    manual_section = "Vol I, *SET_NODE"

    # Card 1 — set header.  Required, occurs once.  Column 8 is unused.
    _CARD_1 = CardSchema("Card 1", [
        CardField("SID", "I", width=10,
                  description="Set ID; must be unique among node sets",
                  required=True),
        CardField("DA1", "F", width=10,
                  description="First nodal attribute default value"),
        CardField("DA2", "F", width=10,
                  description="Second nodal attribute default value"),
        CardField("DA3", "F", width=10,
                  description="Third nodal attribute default value"),
        CardField("DA4", "F", width=10,
                  description="Fourth nodal attribute default value"),
        CardField("SOLVER", "A", width=10,
                  description="Name of the solver using this set "
                              "(MECH, CESE, …); defaults to MECH"),
        CardField("ITS", "I", width=10,
                  description="Coupling type across scales in a two-scale "
                              "co-simulation; see *INCLUDE_COSIM"),
    ], write_header=True,
       description="Set header: ID and default nodal attributes.")

    # Card 2a — node ID cards.  <BLANK>, LIST or LIST_SMOOTH.
    _CARD_2A = CardSchema("Card 2", [
        CardField(f"NID{i}", "I", width=10,
                  description=f"Node ID {i} of the line")
        for i in range(1, 9)
    ], repeating=True, write_header=True,
       condition=lambda kw: kw.option1 in ("", "LIST", "LIST_SMOOTH"),
       condition_doc="for OPTION1 <BLANK>, LIST or LIST_SMOOTH",
       description="Member node IDs, eight per line.  A partly filled final "
                   "line is normal; absent IDs are written as blanks.")

    # Card 2b — node ID with column cards.  COLUMN.
    # Columns 6, 7 and 8 are unused.
    _CARD_2B = CardSchema("Card 2", [
        CardField("NID", "I", width=10,
                  description="Node ID", required=True),
        CardField("A1", "F", width=10,
                  description="First nodal attribute; blank means DA1"),
        CardField("A2", "F", width=10,
                  description="Second nodal attribute; blank means DA2"),
        CardField("A3", "F", width=10,
                  description="Third nodal attribute; blank means DA3"),
        CardField("A4", "F", width=10,
                  description="Fourth nodal attribute; blank means DA4"),
    ], repeating=True, write_header=True,
       condition=lambda kw: kw.option1 == "COLUMN",
       condition_doc="for OPTION1 COLUMN",
       description="One node per line with its four attributes.")

    # Card 2c — node ID range cards.  LIST_GENERATE.
    _CARD_2C = CardSchema("Card 2", [
        CardField(f"B{b}{end}", "I", width=10,
                  description=f"{'First' if end == 'BEG' else 'Last'} node ID "
                              f"of block {b} on this line")
        for b in range(1, 5) for end in ("BEG", "END")
    ], repeating=True, write_header=True,
       condition=lambda kw: kw.option1 == "LIST_GENERATE",
       condition_doc="for OPTION1 LIST_GENERATE",
       description="Four begin/end node ID blocks per line.  A partly filled "
                   "final line is normal; absent IDs are written as blanks.")

    # Card 2d — node ID range with increment cards.  LIST_GENERATE_INCREMENT.
    # Columns 4 to 8 are unused.
    _CARD_2D = CardSchema("Card 2", [
        CardField("BBEG", "I", width=10,
                  description="First node ID in the block"),
        CardField("BEND", "I", width=10,
                  description="Last node ID in the block"),
        CardField("INCR", "I", width=10,
                  description="Node ID increment; BBEG, BBEG + INCR, … up to "
                              "BEND are added to the set"),
    ], repeating=True, write_header=True,
       condition=lambda kw: kw.option1 == "LIST_GENERATE_INCREMENT",
       condition_doc="for OPTION1 LIST_GENERATE_INCREMENT",
       description="One begin/end/increment block per line.")

    # Card 2e — generalized node ID range cards.  GENERAL.
    # Unlike *SET_SEGMENT, E1-E7 are all integers here.
    _CARD_2E = CardSchema("Card 2", [
        CardField("OPTION", "A", width=10,
                  description="Generation operation (ALL, BOX, PART, …); see "
                              "the option table in the manual",
                  required=True),
    ] + [
        CardField(f"E{i}", "I", width=10,
                  description=f"Entity {i} operated on by OPTION")
        for i in range(1, 8)
    ], repeating=True, write_header=True,
       condition=lambda kw: kw.option1 == "GENERAL",
       condition_doc="for OPTION1 GENERAL",
       description="One generation operation per line.")

    card_schemas = [_CARD_1, _CARD_2A, _CARD_2B, _CARD_2C, _CARD_2D, _CARD_2E]

    # Cards holding a packed list of node IDs, where a partly filled final line
    # is normal and 0 is never a valid ID.  Absent IDs are written back as
    # blank fields rather than as a literal 0.
    _PACKED_ID_CARDS = (_CARD_2A, _CARD_2C)

    _OPTION1_VALUES = (
        "LIST_GENERATE_INCREMENT",
        "LIST_GENERATE",
        "LIST_SMOOTH",
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

        # An empty SOLVER field parses as 0; restore the documented default
        # so that the field is written back as a valid solver name.
        card1 = self.cards.get("Card 1")
        if card1 is not None and "SOLVER" in card1:
            solver = card1["SOLVER"][0]
            if solver is None or str(solver).strip() in ("", "0"):
                card1["SOLVER"][0] = "MECH"

        if self.option1 == "COLUMN":
            data_lines = [l for l in non_blank if not l.strip().startswith('$')]
            self._apply_attribute_defaults(data_lines[1:])

    def _apply_attribute_defaults(self, node_lines: List[str]):
        """Fill blank nodal attributes from the Card 1 defaults (Remark 2).

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

        n_rows = len(card2["NID"])
        blank_rows = {i: [] for i in range(1, 5)}
        for row, line in enumerate(node_lines):
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
        """Write one card, blanking absent IDs on the packed node ID cards.

        The final line of a packed list is normally only partly filled.  Those
        trailing fields parse as 0, and writing them back as a literal 0 would
        add node IDs of 0 to the set, so they are written as blanks instead.
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
