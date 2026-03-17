"""Implementation of the *BOUNDARY_PRESCRIBED_MOTION keyword."""

from typing import TextIO, List
import numpy as np

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class BoundaryPrescribedMotion(LSDynaKeyword):
    """Implements the *BOUNDARY_PRESCRIBED_MOTION keyword."""

    keyword_string = "*BOUNDARY_PRESCRIBED_MOTION"

    _CARD_ID_SCHEMA = CardSchema("Card ID", [
        CardField("ID",      "I", width=10),
        CardField("HEADING", "A", width=70),
    ], write_header=True)

    _CARD2_SCHEMA = CardSchema("Card 2", [
        CardField("BOXID",   "I"),
        CardField("TOFFSET", "I"),
        CardField("LCBCHK",  "I"),
    ], write_header=True)

    _CARD4_SCHEMA = CardSchema("Card 4", [
        CardField("NBEG", "I"),
        CardField("NEND", "I"),
    ], write_header=True)

    _CARD5_SCHEMA = CardSchema("Card 5", [
        CardField("PRMR", "A"),
    ], write_header=True)

    _CARD6_SCHEMA = CardSchema("Card 6", [
        CardField("FORM", "I"),
        CardField("SFD",  "F"),
    ], write_header=True)

    _CARD1_SCHEMA = CardSchema("Card 1", [
        CardField("TYPEID", "I", header_name="nid/sid"),
        CardField("DOF",    "I"),
        CardField("VAD",    "I"),
        CardField("LCID",   "I"),
        CardField("SF",     "F"),
        CardField("VID",    "I"),
        CardField("DEATH",  "F"),
        CardField("BIRTH",  "F"),
    ], write_header=True)

    _CARD3_SCHEMA = CardSchema("Card 3", [
        CardField("OFFSET1", "F"),
        CardField("OFFSET2", "F"),
        CardField("LRB",     "I"),
        CardField("NODE1",   "I"),
        CardField("NODE2",   "I"),
    ], write_header=True)

    _CARD6_OPTIONS = frozenset(
        ["POINT_UVW", "EDGE_UVW", "FACE_XYZ",
         "SET_POINT_UVW", "SET_EDGE_UVW", "SET_FACE_XYZ"])

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
