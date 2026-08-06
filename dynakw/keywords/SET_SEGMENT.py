"""Implementation of the *SET_SEGMENT keyword."""

from typing import List
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema
from dynakw.core.parameter_ref import ParameterRef


class SetSegment(LSDynaKeyword):
    """
    Represents a *SET_SEGMENT keyword in an LS-DYNA input file.

    The keyword is written as ``*SET_SEGMENT_{OPTION1}_{OPTION2}`` where
    OPTION1 is <BLANK> or GENERAL and OPTION2 is COLLECT, giving the four
    valid forms::

        *SET_SEGMENT
        *SET_SEGMENT_COLLECT
        *SET_SEGMENT_GENERAL
        *SET_SEGMENT_GENERAL_COLLECT

    COLLECT does not change the card layout; only OPTION1 does.

    Card 1 (required, once) holds the set header.  Card 2 is repeating (one
    row per segment or per generation operation) and continues to the next
    keyword line.  Its layout depends on OPTION1:

    * ``<BLANK>``  — segment cards:  N1-N4 (nodes), A1-A4 (attributes)
    * ``GENERAL``  — generalized part ID range cards:  OPTION, E1-E7

    On Card 2 of the GENERAL form the manual declares E4-E7 as "I or F":
    depending on the OPTION value they hold either entity IDs or float
    attribute values.  They are therefore read as strings so that the value
    written in the file is preserved exactly; E1-E3 are always integers.
    """

    keyword_string = "*SET_SEGMENT"
    keyword_aliases = [
        "*SET_SEGMENT_COLLECT",
        "*SET_SEGMENT_GENERAL",
        "*SET_SEGMENT_GENERAL_COLLECT",
    ]

    description = (
        "Defines a set of segments — four-noded surface patches — referenced "
        "by ID from keywords that act on surfaces, such as contacts and "
        "pressure loads."
    )
    manual_section = "Vol I, *SET_SEGMENT"

    card_schemas = [
        # Card 1 — set header.  Required, occurs once.  Column 8 is unused.
        CardSchema("Card 1", [
            CardField("SID", "I", width=10,
                      description="Set ID; must be unique among segment sets",
                      required=True),
            CardField("DA1", "F", width=10,
                      description="First segment attribute default value"),
            CardField("DA2", "F", width=10,
                      description="Second segment attribute default value"),
            CardField("DA3", "F", width=10,
                      description="Third segment attribute default value"),
            CardField("DA4", "F", width=10,
                      description="Fourth segment attribute default value"),
            CardField("SOLVER", "A", width=10,
                      description="Name of the solver using this set "
                                  "(MECH, CESE, …)"),
            CardField("ITS", "I", width=10,
                      description="Coupling type across scales in a two-scale "
                                  "co-simulation; see *INCLUDE_COSIM"),
        ], write_header=True,
           description="Set header: ID and default segment attributes."),

        # Card 2a — segment cards.  Present when OPTION1 is <BLANK>.
        CardSchema("Card 2", [
            CardField("N1", "I", width=10,
                      description="Nodal point 1 of the segment", required=True),
            CardField("N2", "I", width=10,
                      description="Nodal point 2 of the segment", required=True),
            CardField("N3", "I", width=10,
                      description="Nodal point 3 of the segment", required=True),
            CardField("N4", "I", width=10,
                      description="Nodal point 4 of the segment; repeat N3 for "
                                  "a triangle",
                      required=True),
            CardField("A1", "F", width=10,
                      description="First segment attribute; blank means DA1"),
            CardField("A2", "F", width=10,
                      description="Second segment attribute; blank means DA2"),
            CardField("A3", "F", width=10,
                      description="Third segment attribute; blank means DA3"),
            CardField("A4", "F", width=10,
                      description="Fourth segment attribute; blank means DA4"),
        ], repeating=True, condition=lambda kw: not kw.is_general,
           write_header=True,
           condition_doc="for OPTION1 <BLANK>",
           description="One segment per line: four nodes and four attributes."),

        # Card 2b — generalized part ID range cards.  Present for GENERAL.
        CardSchema("Card 2", [
            CardField("OPTION", "A", width=10,
                      description="Generation operation (ALL, BOX, PART, …); "
                                  "see the option table in the manual",
                      required=True),
            CardField("E1", "I", width=10,
                      description="Entity 1 operated on by OPTION"),
            CardField("E2", "I", width=10,
                      description="Entity 2 operated on by OPTION"),
            CardField("E3", "I", width=10,
                      description="Entity 3 operated on by OPTION"),
            CardField("E4", "A", width=10,
                      description="Entity 4, or an attribute value; read as a "
                                  "string because the manual declares it I or F"),
            CardField("E5", "A", width=10,
                      description="Entity 5, or an attribute value; read as a "
                                  "string because the manual declares it I or F"),
            CardField("E6", "A", width=10,
                      description="Entity 6, or an attribute value; read as a "
                                  "string because the manual declares it I or F"),
            CardField("E7", "A", width=10,
                      description="Entity 7, or an attribute value; read as a "
                                  "string because the manual declares it I or F"),
        ], repeating=True, condition=lambda kw: kw.is_general,
           write_header=True,
           condition_doc="for OPTION1 GENERAL",
           description="One generation operation per line."),
    ]

    def __init__(self, keyword_name: str, raw_lines: List[str] = None,
                 start_line: int = None):
        # Set before super().__init__ — the card conditions are evaluated
        # while the raw data is parsed.
        self.is_general = "GENERAL" in keyword_name.upper()
        super().__init__(keyword_name, raw_lines, start_line)

    def _parse_raw_data(self, raw_lines: List[str]):
        """Parse using the declarative schemas, ignoring blank lines.

        Blank lines are dropped so that trailing whitespace at the end of a
        block does not become a spurious all-zero segment row.
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

        if not self.is_general:
            data_lines = [l for l in non_blank if not l.strip().startswith('$')]
            self._apply_attribute_defaults(data_lines[1:])

    def _apply_attribute_defaults(self, segment_lines: List[str]):
        """Fill blank segment attributes from the Card 1 defaults (Remark 2).

        A blank A1-A4 field on a segment card means A1 = DA1, A2 = DA2, etc.
        Blank fields otherwise parse as 0, which on write would emit an
        explicit 0.0 and override a non-zero DA value.
        """
        card1 = self.cards.get("Card 1")
        card2 = self.cards.get("Card 2")
        if card1 is None or card2 is None:
            return

        schema = next(s for s in self.card_schemas
                      if s.name == "Card 2" and s.repeating and s.condition(self))
        field_types = [f.type for f in schema.fields]
        field_lens = [f.width for f in schema.fields]

        n_rows = len(card2["N1"])
        blank_rows = {i: [] for i in range(1, 5)}
        for row, line in enumerate(segment_lines):
            if row >= n_rows:
                break
            values = self.parser.parse_line(
                line, field_types, field_len=field_lens, default_value=None)
            for i in range(1, 5):
                if values[3 + i] is None:
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
