"""Implementation of the *BOUNDARY_PRESCRIBED_MOTION keyword."""

from typing import TextIO, List
import numpy as np

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class BoundaryPrescribedMotion(LSDynaKeyword):
    """Implements the *BOUNDARY_PRESCRIBED_MOTION keyword.

    Most of the optional cards are selected by a multi-token option name
    (``SET_BOX``, ``SET_LINE``, ``POINT_UVW``, …), so they are matched with
    ``has_option`` rather than by testing membership of ``self.options``, which
    holds the option suffix split on ``'_'``.
    """

    keyword_string = "*BOUNDARY_PRESCRIBED_MOTION"

    description = (
        "Imposes a velocity, acceleration or displacement history on a node, "
        "node set, segment set or rigid body, given by a load curve and a "
        "degree of freedom."
    )
    manual_section = "Vol I, *BOUNDARY_PRESCRIBED_MOTION"

    _CARD_ID_SCHEMA = CardSchema("Card ID", [
        CardField("ID", "I", width=10,
                  description="Prescribed motion set ID; need not be unique"),
        CardField("HEADING", "A", width=70,
                  description="Optional descriptor written to the d3hsp and "
                              "bndout files"),
    ], write_header=True,
       condition=lambda kw: kw.has_option("ID"),
       condition_doc="only with the ID option",
       description="Set ID and heading.")

    _CARD2_SCHEMA = CardSchema("Card 2", [
        CardField("BOXID", "I",
                  description="ID of a box region in which the constraint is "
                              "active; the motion applies only to nodes inside"),
        CardField("TOFFSET", "I",
                  description="Time offset flag for the SET_BOX option",
                  choices={0: "no time offset applied to LCID",
                           1: "LCID is offset by the time the node enters the box"}),
        CardField("LCBCHK", "I",
                  description="Optional load curve giving discrete box-check "
                              "times, instead of checking every time step"),
    ], repeating=True, write_header=True,
       condition=lambda kw: kw.has_option("SET_BOX"),
       condition_doc="only with the SET_BOX option",
       description="Box region limiting where the motion is applied.")

    _CARD4_SCHEMA = CardSchema("Card 4", [
        CardField("NBEG", "I",
                  description="First node of the line"),
        CardField("NEND", "I",
                  description="Last node of the line"),
    ], repeating=True, write_header=True,
       condition=lambda kw: kw.has_option("SET_LINE"),
       condition_doc="only with the SET_LINE option",
       description="Node range defining the line.")

    _CARD5_SCHEMA = CardSchema("Card 5", [
        CardField("PRMR", "A",
                  description="Name of the parameter written to the dynain "
                              "file"),
    ], repeating=True, write_header=True,
       condition=lambda kw: kw.has_option("BNDOUT2DYNAIN"),
       condition_doc="only with the BNDOUT2DYNAIN option",
       description="Parameter name for bndout-to-dynain conversion.")

    _CARD6_SCHEMA = CardSchema("Card 6", [
        CardField("FORM", "I",
                  description="Form of the prescribed motion for isogeometric "
                              "entities"),
        CardField("SFD", "F",
                  description="Scale factor on the prescribed value"),
    ], repeating=True, write_header=True,
       condition=lambda kw: any(kw.has_option(o) for o
                                in BoundaryPrescribedMotion._CARD6_OPTIONS),
       condition_doc="only with one of the POINT_UVW, EDGE_UVW, FACE_XYZ, "
                     "SET_POINT_UVW, SET_EDGE_UVW or SET_FACE_XYZ options",
       description="Isogeometric prescribed motion parameters.")

    _CARD1_SCHEMA = CardSchema("Card 1", [
        CardField("TYPEID", "I", header_name="nid/sid",
                  description="Node ID, node set ID, segment set ID or part ID "
                              "of the rigid body the motion applies to",
                  required=True),
        CardField("DOF", "I",
                  description="Applicable degree of freedom; 1-3 are x, y, z "
                              "translation, 5-7 are x, y, z rotation.  See the "
                              "manual for the full list",
                  required=True),
        CardField("VAD", "I",
                  description="Whether the curve gives velocity, acceleration "
                              "or displacement",
                  choices={0: "velocity",
                           1: "acceleration",
                           2: "displacement",
                           3: "velocity versus displacement",
                           4: "relative displacement"}),
        CardField("LCID", "I",
                  description="Curve or function ID giving the motion as a "
                              "function of time; see *DEFINE_CURVE",
                  required=True),
        CardField("SF", "F",
                  description="Load curve scale factor (default 1.0)"),
        CardField("VID", "I",
                  description="Vector ID for DOF values of 4 or 8; see "
                              "*DEFINE_VECTOR"),
        CardField("DEATH", "F",
                  description="Time at which the imposed motion is removed",
                  units="time"),
        CardField("BIRTH", "F",
                  description="Time at which the imposed motion begins",
                  units="time"),
    ], repeating=True, write_header=True,
       description="One prescribed motion per line.")

    _CARD3_SCHEMA = CardSchema("Card 3", [
        CardField("OFFSET1", "F",
                  description="First offset for DOF types 9-11",
                  units="length"),
        CardField("OFFSET2", "F",
                  description="Second offset for DOF types 9-11",
                  units="length"),
        CardField("LRB", "I",
                  description="Lead rigid body for measuring relative "
                              "displacement (VAD = 4)"),
        CardField("NODE1", "I",
                  description="Optional orientation node 1 for relative "
                              "displacement (VAD = 4)"),
        CardField("NODE2", "I",
                  description="Optional orientation node 2 for relative "
                              "displacement (VAD = 4)"),
    ], repeating=True, write_header=True,
       condition_doc="follows a Card 1 row with |DOF| of 9, 10 or 11, or "
                     "VAD = 4.  Stored with one row per Card 1 row; rows "
                     "without a Card 3 hold None",
       description="Offsets and reference bodies for rotational and relative "
                   "motion.")

    _CARD6_OPTIONS = frozenset(
        ["POINT_UVW", "EDGE_UVW", "FACE_XYZ",
         "SET_POINT_UVW", "SET_EDGE_UVW", "SET_FACE_XYZ"])

    # Declared for introspection only: _parse_raw_data and write are both
    # overridden, so the base class never consults this list.
    # Listed in the order of the manual's Card Summary, which is the order the
    # cards appear in the file.
    card_schemas = [
        _CARD_ID_SCHEMA, _CARD1_SCHEMA, _CARD2_SCHEMA, _CARD3_SCHEMA,
        _CARD4_SCHEMA, _CARD5_SCHEMA, _CARD6_SCHEMA,
    ]

    def _active_optional_schemas(self) -> List[CardSchema]:
        """The cards that follow each Card 1, in the manual's Card Summary order.

        Card 3 is included unconditionally: unlike the others it is selected by
        the DOF and VAD values on Card 1 rather than by a keyword option, so
        whether it is really present is decided per definition while parsing.
        Its place in this list is what fixes its position in the sequence.
        """
        schemas = []
        if self.has_option("SET_BOX"):
            schemas.append(self._CARD2_SCHEMA)
        schemas.append(self._CARD3_SCHEMA)
        if self.has_option("SET_LINE"):
            schemas.append(self._CARD4_SCHEMA)
        if self.has_option("BNDOUT2DYNAIN"):
            schemas.append(self._CARD5_SCHEMA)
        if any(self.has_option(o) for o in self._CARD6_OPTIONS):
            schemas.append(self._CARD6_SCHEMA)
        return schemas

    def _parse_raw_data(self, raw_lines: List[str]):
        card_lines = [line for line in raw_lines[1:]
                      if line.strip() and not line.startswith('$')]
        if not card_lines:
            return

        line_idx = 0

        # Card ID — once, ahead of the definitions
        if self.has_option("ID") and line_idx < len(card_lines):
            self.cards["Card ID"] = self._parse_single_card(
                card_lines[line_idx], self._CARD_ID_SCHEMA)
            line_idx += 1

        s1 = self._CARD1_SCHEMA
        s3 = self._CARD3_SCHEMA
        f1_types = [f.type for f in s1.fields]
        f1_lens  = [f.width for f in s1.fields]
        f3_types = [f.type for f in s3.fields]
        f3_lens  = [f.width for f in s3.fields]

        active = self._active_optional_schemas()

        card1_rows = []
        card3_rows = []                                  # None = no Card 3
        opt_lines = {s.name: [] for s in active}         # raw lines per schema

        # One definition per iteration.  The cards within a definition follow
        # the order of the manual's Card Summary: Card 1, Card 2 (SET_BOX),
        # Card 3 (selected by DOF/VAD), Card 4 (SET_LINE), Card 5
        # (BNDOUT2DYNAIN), Card 6 (the UVW/XYZ options).
        while line_idx < len(card_lines):
            vals = self.parser.parse_line(
                card_lines[line_idx], f1_types, field_len=f1_lens)
            card1_rows.append(vals)
            line_idx += 1

            for schema in active:
                if schema is s3:
                    dof = vals[1]
                    vad = vals[2]
                    if (dof is not None and abs(int(dof)) in {9, 10, 11}) or vad == 4:
                        if line_idx < len(card_lines):
                            card3_rows.append(self.parser.parse_line(
                                card_lines[line_idx], f3_types, field_len=f3_lens))
                            line_idx += 1
                        else:
                            card3_rows.append([None] * len(s3.fields))
                    else:
                        card3_rows.append(None)
                elif line_idx < len(card_lines):
                    opt_lines[schema.name].append(card_lines[line_idx])
                    line_idx += 1

        if card1_rows:
            arr = np.array(card1_rows, dtype=object)
            self.cards["Card 1"] = {
                f.name: arr[:, i].astype(self._DTYPE_MAP[f.type], copy=False)
                for i, f in enumerate(s1.fields)
            }

        if any(r is not None for r in card3_rows):
            # Use dtype=object to preserve None for rows without Card 3
            padded = [r if r is not None else [None] * len(s3.fields)
                      for r in card3_rows]
            arr3 = np.array(padded, dtype=object)
            self.cards["Card 3"] = {f.name: arr3[:, i] for i, f in enumerate(s3.fields)}

        for schema in active:
            lines = opt_lines.get(schema.name)
            if lines:
                self.cards[schema.name] = self._parse_repeating_card(lines, schema)

    def write(self, file_obj: TextIO):
        file_obj.write(f"{self.full_keyword}\n")

        # Card ID — once, ahead of the definitions
        card_id = self.cards.get("Card ID")
        if card_id is not None:
            self._write_card(file_obj, card_id, self._CARD_ID_SCHEMA)

        card1 = self.cards.get("Card 1")
        if card1 is None:
            return

        s1 = self._CARD1_SCHEMA
        s3 = self._CARD3_SCHEMA

        headers_written = set()

        def _write_header(schema: CardSchema):
            """Emit a card's header once, before its first data row."""
            if schema.name in headers_written:
                return
            file_obj.write(self.parser.format_header(
                [f.header_name or f.name for f in schema.fields],
                field_len=[f.width for f in schema.fields],
            ))
            headers_written.add(schema.name)

        def _write_row(schema: CardSchema, card, i: int):
            parts = [
                self.parser.format_field(card[f.name][i], f.type, field_len=f.width)
                for f in schema.fields
            ]
            file_obj.write(''.join(parts) + '\n')

        _write_header(s1)

        # Mirrors the parse order, so a file round-trips unchanged.
        active = self._active_optional_schemas()
        num_rows = len(card1[s1.fields[0].name])

        for i in range(num_rows):
            _write_row(s1, card1, i)

            for schema in active:
                card = self.cards.get(schema.name)
                if card is None or i >= len(card[schema.fields[0].name]):
                    continue
                # A definition without a Card 3 holds None in every column.
                if schema is s3 and all(
                        card[f.name][i] is None for f in s3.fields):
                    continue
                _write_header(schema)
                _write_row(schema, card, i)
