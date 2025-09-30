"""Implementation of the *SECTION_SHELL keyword."""

from typing import TextIO, List
import math
import numpy as np

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword


class SectionShell(LSDynaKeyword):
    """
    Implements the *SECTION_SHELL keyword.
    """
    keyword_string = "*SECTION_SHELL"

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        super().__init__(keyword_name, raw_lines)

    def _parse_raw_data(self, raw_lines: List[str]):
        """
        Parses the raw data for *SECTION_SHELL.
        """
        card_lines = [line for line in raw_lines[1:]
                      if line.strip() and not line.startswith('$')]
        if not card_lines:
            return

        line_idx = 0

        # Card 1 (Required)
        if line_idx >= len(card_lines):
            return
        card1_columns = ["SECID", "ELFORM", "SHRF",
                         "NIP", "PROPT", "QR/IRID", "ICOMP", "SETYP"]
        card1_types_read = ["A", "F", "F", "F", "F", "F", "F", "F"]
        card1_data = self.parser.parse_line(
            card_lines[line_idx], card1_types_read)

        # Convert to correct types
        card1_data[1] = int(
            card1_data[1]) if card1_data[1] is not None else None  # ELFORM
        card1_data[3] = int(
            card1_data[3]) if card1_data[3] is not None else None  # NIP
        card1_data[5] = int(
            card1_data[5]) if card1_data[5] is not None else None  # QR/IRID
        card1_data[6] = int(
            card1_data[6]) if card1_data[6] is not None else None  # ICOMP
        card1_data[7] = int(
            card1_data[7]) if card1_data[7] is not None else None  # SETYP

        self.cards["Card 1"] = {col: np.array(
            [val], dtype=object) for col, val in zip(card1_columns, card1_data)}
        line_idx += 1

        elform = card1_data[1]
        nip = card1_data[3]
        icomp = card1_data[6]

        # Card 2 (Required)
        if line_idx >= len(card_lines):
            return
        card2_columns = ["T1", "T2", "T3", "T4",
                         "NLOC", "MAREA", "IDOF", "EDGSET"]
        card2_types_read = ["F", "F", "F", "F", "F", "F", "F", "F"]
        card2_data = self.parser.parse_line(
            card_lines[line_idx], card2_types_read)

        # Convert to correct types
        card2_data[6] = int(
            card2_data[6]) if card2_data[6] is not None else None  # IDOF
        card2_data[7] = int(
            card2_data[7]) if card2_data[7] is not None else None  # EDGSET

        self.cards["Card 2"] = {col: np.array(
            [val], dtype=object) for col, val in zip(card2_columns, card2_data)}
        line_idx += 1

        # Card 3 (Conditional)
        if icomp == 1 and nip is not None and nip > 0:
            num_card3 = math.ceil(nip / 8)
            all_b_values = []
            for _ in range(num_card3):
                if line_idx >= len(card_lines):
                    break
                data = self.parser.parse_line(card_lines[line_idx], ["F"] * 8)
                all_b_values.extend(d for d in data if d is not None)
                line_idx += 1
            b_cols = [f"B{i+1}" for i in range(len(all_b_values))]
            if all_b_values:
                self.cards["Card 3"] = {col: np.array(
                    [val], dtype=object) for col, val in zip(b_cols, all_b_values)}

        # Keyword Options
        options = [o.upper() for o in self.options]
        if "EFG" in options:
            if line_idx < len(card_lines):
                card4a_cols = ["DX", "DY", "ISPLINE", "IDILA", "IEBT", "IDIM"]
                card4a_types_read = ["F", "F", "F", "F", "F", "F"]
                card4a_data = self.parser.parse_line(
                    card_lines[line_idx], card4a_types_read)
                # Convert
                card4a_data[2] = int(
                    card4a_data[2]) if card4a_data[2] is not None else None
                card4a_data[3] = int(
                    card4a_data[3]) if card4a_data[3] is not None else None
                card4a_data[4] = int(
                    card4a_data[4]) if card4a_data[4] is not None else None
                card4a_data[5] = int(
                    card4a_data[5]) if card4a_data[5] is not None else None
                self.cards["Card 4a"] = {col: np.array(
                    [val], dtype=object) for col, val in zip(card4a_cols, card4a_data)}
                line_idx += 1
        if "THERMAL" in options:
            if line_idx < len(card_lines):
                card4b_cols = ["ITHELFM"]
                card4b_types_read = ["F"]
                card4b_data = self.parser.parse_line(
                    card_lines[line_idx], card4b_types_read)
                # Convert
                card4b_data[0] = int(
                    card4b_data[0]) if card4b_data[0] is not None else None
                self.cards["Card 4b"] = {col: np.array(
                    [val], dtype=object) for col, val in zip(card4b_cols, card4b_data)}
                line_idx += 1
        if "XFEM" in options:
            if line_idx < len(card_lines):
                card4c_cols = ["CMID", "BASELM", "DOMINT",
                               "FAILCR", "PROPCR", "FS", "LS/FS1", "NC/CL"]
                card4c_types_read = ["F"] * 8
                card4c_data = self.parser.parse_line(
                    card_lines[line_idx], card4c_types_read)
                # Convert
                card4c_data[0] = int(
                    card4c_data[0]) if card4c_data[0] is not None else None
                card4c_data[1] = int(
                    card4c_data[1]) if card4c_data[1] is not None else None
                card4c_data[2] = int(
                    card4c_data[2]) if card4c_data[2] is not None else None
                card4c_data[3] = int(
                    card4c_data[3]) if card4c_data[3] is not None else None
                card4c_data[4] = int(
                    card4c_data[4]) if card4c_data[4] is not None else None
                self.cards["Card 4c"] = {col: np.array(
                    [val], dtype=object) for col, val in zip(card4c_cols, card4c_data)}
                line_idx += 1
        if "MISC" in options:
            if line_idx < len(card_lines):
                card4d_cols = ["THKSCL"]
                card4d_types = ["F"]
                card4d_data = self.parser.parse_line(
                    card_lines[line_idx], card4d_types)
                self.cards["Card 4d"] = {col: np.array(
                    [val], dtype=object) for col, val in zip(card4d_cols, card4d_data)}
                line_idx += 1

        # User Defined Elements
        if elform in [101, 102, 103, 104, 105]:
            # Card 5
            if line_idx < len(card_lines):
                card5_cols = ["NIPP", "NXDOF", "IUNF",
                              "IHGF", "ITAJ", "LMC", "NHSV", "ILOC"]
                card5_types_read = ["F"] * 8
                card5_data = self.parser.parse_line(
                    card_lines[line_idx], card5_types_read)
                # Convert all to int
                for i in range(len(card5_data)):
                    card5_data[i] = int(
                        card5_data[i]) if card5_data[i] is not None else None
                self.cards["Card 5"] = {col: np.array(
                    [val], dtype=object) for col, val in zip(card5_cols, card5_data)}
                line_idx += 1
                nipp = card5_data[0]
                lmc = card5_data[5]

                # Card 5.1
                if nipp is not None and nipp > 0:
                    card51_cols = ["XI", "ETA", "WGT"]
                    card51_types = ["F"] * 3
                    card51_data = []
                    for _ in range(nipp):
                        if line_idx >= len(card_lines):
                            break
                        data = self.parser.parse_line(
                            card_lines[line_idx], card51_types)
                        card51_data.append(data)
                        line_idx += 1
                    if card51_data:
                        arr = np.array(card51_data, dtype=object)
                        self.cards["Card 5.1"] = {col: arr[:, i]
                                                  for i, col in enumerate(card51_cols)}

                # Card 5.2
                if lmc is not None and lmc > 0:
                    num_card52 = math.ceil(lmc / 8)
                    all_p_values = []
                    for _ in range(num_card52):
                        if line_idx >= len(card_lines):
                            break
                        data = self.parser.parse_line(
                            card_lines[line_idx], ["F"] * 8)
                        all_p_values.extend(d for d in data if d is not None)
                        line_idx += 1
                    p_values_truncated = all_p_values[:lmc]
                    p_cols = [
                        f"P{i+1}" for i in range(len(p_values_truncated))]
                    if p_values_truncated:
                        self.cards["Card 5.2"] = {col: np.array(
                            [val], dtype=object) for col, val in zip(p_cols, p_values_truncated)}

    def write(self, file_obj: TextIO):
        """Writes the *SECTION_SHELL keyword to a file."""
        file_obj.write(f"{self.full_keyword}\n")

        # Card 1
        card1 = self.cards.get("Card 1")
        if card1 is not None:
            cols = ["SECID", "ELFORM", "SHRF", "NIP",
                    "PROPT", "QR/IRID", "ICOMP", "SETYP"]
            types = ["I/A", "I", "F", "I", "F", "I", "I", "I"]
            file_obj.write(
                "$#" + "".join([f"{col.lower():>10}" for col in cols]) + "\n")
            line_parts = [self.parser.format_field(
                card1.get(col, [None])[0], typ) for col, typ in zip(cols, types)]
            file_obj.write("".join(line_parts) + "\n")

        # Card 2
        card2 = self.cards.get("Card 2")
        if card2 is not None:
            cols = ["T1", "T2", "T3", "T4", "NLOC", "MAREA", "IDOF", "EDGSET"]
            types = ["F", "F", "F", "F", "F", "F", "I", "I"]
            file_obj.write(
                "$#" + "".join([f"{col.lower():>10}" for col in cols]) + "\n")
            line_parts = [self.parser.format_field(
                card2.get(col, [None])[0], typ) for col, typ in zip(cols, types)]
            file_obj.write("".join(line_parts) + "\n")

        # Card 3
        card3 = self.cards.get("Card 3")
        if card3 is not None:
            b_values = [card3[f"B{i+1}"][0] for i in range(len(card3))]
            file_obj.write(
                "$#" + "".join([f"{f'b{i+1}':>10}" for i in range(8)]) + "\n")
            for i in range(0, len(b_values), 8):
                chunk = b_values[i:i + 8]
                chunk.extend([None] * (8 - len(chunk)))
                line_parts = [self.parser.format_field(b, "F") for b in chunk]
                file_obj.write("".join(line_parts) + "\n")

        # Keyword Options
        for card_name, cols, types, num_fields in [
            ("Card 4a", ["DX", "DY", "ISPLINE", "IDILA", "IEBT",
             "IDIM"], ["F", "F", "I", "I", "I", "I"], 8),
            ("Card 4b", ["ITHELFM"], ["I"], 8),
            ("Card 4c", ["CMID", "BASELM", "DOMINT", "FAILCR", "PROPCR", "FS",
             "LS/FS1", "NC/CL"], ["I", "I", "I", "I", "I", "F", "F", "F"], 8),
            ("Card 4d", ["THKSCL"], ["F"], 8)
        ]:
            card = self.cards.get(card_name)
            if card is not None:
                file_obj.write(
                    "$#" + "".join([f"{col.lower():>10}" for col in cols]) + "\n")
                line_parts = [self.parser.format_field(
                    card.get(col, [None])[0], typ) for col, typ in zip(cols, types)]
                line_parts.extend([self.parser.format_field(
                    None, "F")] * (num_fields - len(line_parts)))
                file_obj.write("".join(line_parts) + "\n")

        # User Defined Elements
        card5 = self.cards.get("Card 5")
        if card5 is not None:
            cols = ["NIPP", "NXDOF", "IUNF", "IHGF",
                    "ITAJ", "LMC", "NHSV", "ILOC"]
            types = ["I"] * 8
            file_obj.write(
                "$#" + "".join([f"{col.lower():>10}" for col in cols]) + "\n")
            line_parts = [self.parser.format_field(
                card5.get(col, [None])[0], typ) for col, typ in zip(cols, types)]
            file_obj.write("".join(line_parts) + "\n")

            # Card 5.1
            card51 = self.cards.get("Card 5.1")
            if card51 is not None:
                cols = ["XI", "ETA", "WGT"]
                types = ["F"] * 3
                file_obj.write(
                    "$#" + "".join([f"{col.lower():>10}" for col in cols]) + "\n")
                nrows = len(card51[cols[0]])
                for i in range(nrows):
                    line_parts = [self.parser.format_field(card51.get(
                        col, [None] * nrows)[i], typ) for col, typ in zip(cols, types)]
                    line_parts.extend(
                        [self.parser.format_field(None, "F")] * 5)
                    file_obj.write("".join(line_parts) + "\n")

            # Card 5.2
            card52 = self.cards.get("Card 5.2")
            if card52 is not None:
                p_cols = [col for col in card52]
                file_obj.write(
                    "$#" + "".join([f"{col.lower():>10}" for col in p_cols]) + "\n")
                all_p_values = [card52[col][0] for col in p_cols]
                for i in range(0, len(all_p_values), 8):
                    chunk = all_p_values[i:i + 8]
                    chunk.extend([None] * (8 - len(chunk)))
                    line_parts = [self.parser.format_field(
                        p, "F") for p in chunk]
                    file_obj.write("".join(line_parts) + "\n")
