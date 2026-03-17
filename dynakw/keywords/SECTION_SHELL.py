"""Implementation of the *SECTION_SHELL keyword."""

import math
from typing import TextIO, List
import numpy as np

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class SectionShell(LSDynaKeyword):
    """Implements the *SECTION_SHELL keyword."""

    keyword_string = "*SECTION_SHELL"

    _CARD1_SCHEMA = CardSchema("Card 1", [
        CardField("SECID",   "A", width=10),
        CardField("ELFORM",  "I", width=10),
        CardField("SHRF",    "F", width=10),
        CardField("NIP",     "I", width=10),
        CardField("PROPT",   "F", width=10),
        CardField("QR/IRID", "I", width=10),
        CardField("ICOMP",   "I", width=10),
        CardField("SETYP",   "I", width=10),
    ], write_header=True)

    _CARD2_SCHEMA = CardSchema("Card 2", [
        CardField("T1",     "F", width=10),
        CardField("T2",     "F", width=10),
        CardField("T3",     "F", width=10),
        CardField("T4",     "F", width=10),
        CardField("NLOC",   "F", width=10),
        CardField("MAREA",  "F", width=10),
        CardField("IDOF",   "I", width=10),
        CardField("EDGSET", "I", width=10),
    ], write_header=True)

    def _parse_raw_data(self, raw_lines: List[str]):
        card_lines = [line for line in raw_lines[1:]
                      if line.strip() and not line.startswith('$')]
        if not card_lines:
            return

        line_idx = 0

        # Card 1 (required)
        if line_idx >= len(card_lines):
            return
        self.cards["Card 1"] = self._parse_single_card(
            card_lines[line_idx], self._CARD1_SCHEMA)
        line_idx += 1

        elform = int(self.cards["Card 1"]["ELFORM"][0])
        nip    = int(self.cards["Card 1"]["NIP"][0])
        icomp  = int(self.cards["Card 1"]["ICOMP"][0])

        # Card 2 (required)
        if line_idx >= len(card_lines):
            return
        self.cards["Card 2"] = self._parse_single_card(
            card_lines[line_idx], self._CARD2_SCHEMA)
        line_idx += 1

        # Card 3 — conditional on ICOMP==1 and NIP>0
        if icomp == 1 and nip > 0:
            num_card3 = math.ceil(nip / 8)
            all_b_values = []
            for _ in range(num_card3):
                if line_idx >= len(card_lines):
                    break
                data = self.parser.parse_line(card_lines[line_idx], ["F"] * 8)
                all_b_values.extend(d for d in data if d is not None)
                line_idx += 1
            if all_b_values:
                b_cols = [f"B{i+1}" for i in range(len(all_b_values))]
                self.cards["Card 3"] = {
                    col: np.array([val], dtype=np.float64)
                    for col, val in zip(b_cols, all_b_values)
                }

        # Keyword option cards
        options = [o.upper() for o in self.options]
        if "EFG" in options and line_idx < len(card_lines):
            cols  = ["DX", "DY", "ISPLINE", "IDILA", "IEBT", "IDIM"]
            types = ["F",  "F",  "I",       "I",     "I",    "I"]
            data  = self.parser.parse_line(card_lines[line_idx], types)
            self.cards["Card 4a"] = {
                col: np.array([v], dtype=np.int32 if t == 'I' else np.float64)
                for col, t, v in zip(cols, types, data)
            }
            line_idx += 1

        if "THERMAL" in options and line_idx < len(card_lines):
            data = self.parser.parse_line(card_lines[line_idx], ["I"])
            self.cards["Card 4b"] = {
                "ITHELFM": np.array([data[0]], dtype=np.int32)
            }
            line_idx += 1

        if "XFEM" in options and line_idx < len(card_lines):
            cols  = ["CMID", "BASELM", "DOMINT", "FAILCR", "PROPCR", "FS", "LS/FS1", "NC/CL"]
            types = ["I",    "I",      "I",      "I",      "I",      "F",  "F",      "F"]
            data  = self.parser.parse_line(card_lines[line_idx], types)
            self.cards["Card 4c"] = {
                col: np.array([v], dtype=np.int32 if t == 'I' else np.float64)
                for col, t, v in zip(cols, types, data)
            }
            line_idx += 1

        if "MISC" in options and line_idx < len(card_lines):
            data = self.parser.parse_line(card_lines[line_idx], ["F"])
            self.cards["Card 4d"] = {
                "THKSCL": np.array([data[0]], dtype=np.float64)
            }
            line_idx += 1

        # User-defined element cards (ELFORM 101-105)
        if elform in [101, 102, 103, 104, 105] and line_idx < len(card_lines):
            cols  = ["NIPP", "NXDOF", "IUNF", "IHGF", "ITAJ", "LMC", "NHSV", "ILOC"]
            data  = self.parser.parse_line(card_lines[line_idx], ["I"] * 8)
            self.cards["Card 5"] = {
                col: np.array([v], dtype=np.int32) for col, v in zip(cols, data)
            }
            line_idx += 1
            nipp = int(data[0]) if data[0] is not None else 0
            lmc  = int(data[5]) if data[5] is not None else 0

            if nipp > 0:
                card51_data = []
                for _ in range(nipp):
                    if line_idx >= len(card_lines):
                        break
                    card51_data.append(
                        self.parser.parse_line(card_lines[line_idx], ["F"] * 3))
                    line_idx += 1
                if card51_data:
                    arr = np.array(card51_data, dtype=np.float64)
                    self.cards["Card 5.1"] = {
                        col: arr[:, i] for i, col in enumerate(["XI", "ETA", "WGT"])
                    }

            if lmc > 0:
                num_card52 = math.ceil(lmc / 8)
                all_p = []
                for _ in range(num_card52):
                    if line_idx >= len(card_lines):
                        break
                    all_p.extend(d for d in self.parser.parse_line(
                        card_lines[line_idx], ["F"] * 8) if d is not None)
                    line_idx += 1
                p_vals = all_p[:lmc]
                if p_vals:
                    self.cards["Card 5.2"] = {
                        f"P{i+1}": np.array([v], dtype=np.float64)
                        for i, v in enumerate(p_vals)
                    }

    def write(self, file_obj: TextIO):
        file_obj.write(f"{self.full_keyword}\n")

        # Cards 1 and 2 — schema-driven
        for schema in [self._CARD1_SCHEMA, self._CARD2_SCHEMA]:
            card = self.cards.get(schema.name)
            if card is not None:
                self._write_card(file_obj, card, schema)

        # Card 3
        card3 = self.cards.get("Card 3")
        if card3 is not None:
            b_values = [card3[f"B{i+1}"][0] for i in range(len(card3))]
            file_obj.write(self.parser.format_header([f"b{i+1}" for i in range(8)]))
            for i in range(0, len(b_values), 8):
                chunk = b_values[i:i + 8]
                chunk += [None] * (8 - len(chunk))
                file_obj.write(
                    "".join(self.parser.format_field(b, "F") for b in chunk) + "\n")

        # Option cards
        for card_name, cols, types in [
            ("Card 4a", ["DX", "DY", "ISPLINE", "IDILA", "IEBT", "IDIM"],
                        ["F",  "F",  "I",       "I",     "I",    "I"]),
            ("Card 4b", ["ITHELFM"], ["I"]),
            ("Card 4c", ["CMID", "BASELM", "DOMINT", "FAILCR", "PROPCR", "FS", "LS/FS1", "NC/CL"],
                        ["I",   "I",      "I",      "I",      "I",      "F",  "F",      "F"]),
            ("Card 4d", ["THKSCL"], ["F"]),
        ]:
            card = self.cards.get(card_name)
            if card is not None:
                file_obj.write(self.parser.format_header(cols))
                parts = [self.parser.format_field(card.get(col, [None])[0], t)
                         for col, t in zip(cols, types)]
                parts += [self.parser.format_field(None, "F")] * (8 - len(parts))
                file_obj.write("".join(parts) + "\n")

        # User-defined element cards
        card5 = self.cards.get("Card 5")
        if card5 is not None:
            cols  = ["NIPP", "NXDOF", "IUNF", "IHGF", "ITAJ", "LMC", "NHSV", "ILOC"]
            file_obj.write(self.parser.format_header(cols))
            file_obj.write("".join(
                self.parser.format_field(card5.get(col, [None])[0], "I") for col in cols
            ) + "\n")

            card51 = self.cards.get("Card 5.1")
            if card51 is not None:
                cols51 = ["XI", "ETA", "WGT"]
                file_obj.write(self.parser.format_header(cols51))
                nrows = len(card51["XI"])
                for i in range(nrows):
                    parts = [self.parser.format_field(card51[c][i], "F") for c in cols51]
                    parts += [self.parser.format_field(None, "F")] * 5
                    file_obj.write("".join(parts) + "\n")

            card52 = self.cards.get("Card 5.2")
            if card52 is not None:
                p_cols = sorted(card52.keys(), key=lambda k: int(k[1:]))
                all_p  = [card52[col][0] for col in p_cols]
                for i in range(0, len(all_p), 8):
                    chunk = all_p[i:i + 8]
                    file_obj.write(self.parser.format_header(p_cols[i:i + 8]))
                    chunk += [None] * (8 - len(chunk))
                    file_obj.write(
                        "".join(self.parser.format_field(p, "F") for p in chunk) + "\n")
