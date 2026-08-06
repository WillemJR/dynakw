"""Implementation of the *BOUNDARY_PRESCRIBED_MOTION keyword."""

from typing import TextIO, List
import numpy as np

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class BoundaryPrescribedMotion(LSDynaKeyword):
    """Implements the *BOUNDARY_PRESCRIBED_MOTION keyword.

    .. note::
       The optional cards are selected by testing an option name against
       ``self.options``, which the base class produces by splitting the keyword
       name on ``'_'``.  A multi-token option therefore never matches:
       ``*BOUNDARY_PRESCRIBED_MOTION_SET_BOX`` yields the options
       ``{SET, BOX}``, not ``{SET_BOX}``.  The card conditions below mirror that
       behaviour rather than the manual, so that introspection reports what the
       parser actually produces.
    """

    keyword_string = "*BOUNDARY_PRESCRIBED_MOTION"

    description = (
        "Imposes a velocity, acceleration or displacement history on a node, "
        "node set, segment set or rigid body, given by a load curve and a "
        "degree of freedom."
    )
    manual_section = "Vol I, *BOUNDARY_PRESCRIBED_MOTION"

    @staticmethod
    def _opts(kw) -> set:
        """The keyword's option suffixes, upper-cased."""
        return {o.upper() for o in kw.options}

    _CARD_ID_SCHEMA = CardSchema("Card ID", [
        CardField("ID", "I", width=10,
                  description="Prescribed motion set ID; need not be unique"),
        CardField("HEADING", "A", width=70,
                  description="Optional descriptor written to the d3hsp and "
                              "bndout files"),
    ], write_header=True,
       condition=lambda kw: "ID" in BoundaryPrescribedMotion._opts(kw),
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
    ], write_header=True,
       condition=lambda kw: "SET_BOX" in BoundaryPrescribedMotion._opts(kw),
       condition_doc="only with the SET_BOX option (see the class note: this "
                     "multi-token option does not currently match)",
       description="Box region limiting where the motion is applied.")

    _CARD4_SCHEMA = CardSchema("Card 4", [
        CardField("NBEG", "I",
                  description="First node of the line"),
        CardField("NEND", "I",
                  description="Last node of the line"),
    ], write_header=True,
       condition=lambda kw: "SET_LINE" in BoundaryPrescribedMotion._opts(kw),
       condition_doc="only with the SET_LINE option (see the class note: this "
                     "multi-token option does not currently match)",
       description="Node range defining the line.")

    _CARD5_SCHEMA = CardSchema("Card 5", [
        CardField("PRMR", "A",
                  description="Name of the parameter written to the dynain "
                              "file"),
    ], write_header=True,
       condition=lambda kw: "BNDOUT2DYNAIN" in BoundaryPrescribedMotion._opts(kw),
       condition_doc="only with the BNDOUT2DYNAIN option",
       description="Parameter name for bndout-to-dynain conversion.")

    _CARD6_SCHEMA = CardSchema("Card 6", [
        CardField("FORM", "I",
                  description="Form of the prescribed motion for isogeometric "
                              "entities"),
        CardField("SFD", "F",
                  description="Scale factor on the prescribed value"),
    ], write_header=True,
       condition=lambda kw: bool(BoundaryPrescribedMotion._CARD6_OPTIONS
                                 & BoundaryPrescribedMotion._opts(kw)),
       condition_doc="only with one of the POINT_UVW, EDGE_UVW, FACE_XYZ, "
                     "SET_POINT_UVW, SET_EDGE_UVW or SET_FACE_XYZ options "
                     "(see the class note: these multi-token options do not "
                     "currently match)",
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
    card_schemas = [
        _CARD_ID_SCHEMA, _CARD2_SCHEMA, _CARD4_SCHEMA, _CARD5_SCHEMA,
        _CARD6_SCHEMA, _CARD1_SCHEMA, _CARD3_SCHEMA,
    ]

    def _parse_raw_data(self, raw_lines: List[str]):
        card_lines = [line for line in raw_lines[1:]
                      if line.strip() and not line.startswith('$')]
        if not card_lines:
            return

        line_idx = 0
        options = {o.upper() for o in self.options}

        # Optional prefix cards
        for flag, schema in [
            ("ID",            self._CARD_ID_SCHEMA),
            ("SET_BOX",       self._CARD2_SCHEMA),
            ("SET_LINE",      self._CARD4_SCHEMA),
            ("BNDOUT2DYNAIN", self._CARD5_SCHEMA),
        ]:
            if flag in options and line_idx < len(card_lines):
                self.cards[schema.name] = self._parse_single_card(
                    card_lines[line_idx], schema)
                line_idx += 1

        if self._CARD6_OPTIONS & options and line_idx < len(card_lines):
            self.cards["Card 6"] = self._parse_single_card(
                card_lines[line_idx], self._CARD6_SCHEMA)
            line_idx += 1

        # Card 1 (repeating) + Card 3 (per-row conditional)
        s1 = self._CARD1_SCHEMA
        s3 = self._CARD3_SCHEMA
        f1_types = [f.type for f in s1.fields]
        f1_lens  = [f.width for f in s1.fields]
        f3_types = [f.type for f in s3.fields]
        f3_lens  = [f.width for f in s3.fields]

        card1_rows = []
        card3_rows = []  # None = no Card 3 for this row

        while line_idx < len(card_lines):
            vals = self.parser.parse_line(
                card_lines[line_idx], f1_types, field_len=f1_lens)
            card1_rows.append(vals)
            line_idx += 1

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

    def write(self, file_obj: TextIO):
        file_obj.write(f"{self.full_keyword}\n")

        # Optional prefix cards
        for schema in [self._CARD_ID_SCHEMA, self._CARD2_SCHEMA,
                       self._CARD4_SCHEMA, self._CARD5_SCHEMA, self._CARD6_SCHEMA]:
            card = self.cards.get(schema.name)
            if card is not None:
                self._write_card(file_obj, card, schema)

        card1 = self.cards.get("Card 1")
        if card1 is None:
            return

        s1 = self._CARD1_SCHEMA
        s3 = self._CARD3_SCHEMA

        # Card 1 header
        file_obj.write(self.parser.format_header(
            [f.header_name or f.name for f in s1.fields],
            field_len=[f.width for f in s1.fields],
        ))

        card3 = self.cards.get("Card 3")
        num_rows = len(card1[s1.fields[0].name])
        card3_header_written = False

        for i in range(num_rows):
            parts = [
                self.parser.format_field(card1[f.name][i], f.type, field_len=f.width)
                for f in s1.fields
            ]
            file_obj.write(''.join(parts) + '\n')

            if card3 is not None:
                if any(card3[f.name][i] is not None for f in s3.fields):
                    if not card3_header_written:
                        file_obj.write(self.parser.format_header(
                            [f.header_name or f.name for f in s3.fields],
                            field_len=[f.width for f in s3.fields],
                        ))
                        card3_header_written = True
                    parts3 = [
                        self.parser.format_field(card3[f.name][i], f.type, field_len=f.width)
                        for f in s3.fields
                    ]
                    file_obj.write(''.join(parts3) + '\n')
