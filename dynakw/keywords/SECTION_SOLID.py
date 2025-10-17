"""Implementation of the *SECTION_SOLID keyword."""

from typing import TextIO, List
import math
import numpy as np

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword


class SectionSolid(LSDynaKeyword):
    """
    Implements the *SECTION_SOLID keyword.
    """
    keyword_string = "*SECTION_SOLID"
    keyword_aliases = []

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        super().__init__(keyword_name, raw_lines)

    def _parse_raw_data(self, raw_lines: List[str]):
        """
        Parses the raw data for *SECTION_SOLID.
        """
        card_lines = [line for line in raw_lines[1:]
                      if line.strip() and not line.startswith('$')]
        if not card_lines:
            return

        # Card 1 (Always Required)
        card1_columns = ["SECID", "ELFORM", "AET", None, None, None, "COHOFF", "GASKETT"]
        card1_types = ["I/A", "I", "I", None, None, None, "F", "F"]
        card1_data = self.parser.parse_line(card_lines[0], card1_types)
        self.cards["Card 1"] = {col: np.array(
            [val], dtype=object) for col, val in zip(card1_columns, card1_data) if col}

        elform = card1_data[1]
        options = [o.upper() for o in self.options]
        line_idx = 1

        # Option-based cards
        if "EFG" in options:
            # Card 2a.1
            card2a1_cols = ["DX", "DY", "DZ", "ISPLINE",
                            "IDILA", "IEBT", "IDIM", "TOLDEF"]
            card2a1_types = ["F", "F", "F", "I", "I", "I", "I", "F"]
            card2a1_data = self.parser.parse_line(
                card_lines[line_idx], card2a1_types)
            self.cards["Card 2a.1"] = {col: np.array(
                [val], dtype=object) for col, val in zip(card2a1_cols, card2a1_data)}
            line_idx += 1
            # Card 2a.2 (Optional)
            if line_idx < len(card_lines):
                card2a2_cols = ["IPS", "STIME", "IKEN",
                                "SF", "CMID", "IBR", "DS", "ECUT"]
                card2a2_types = ["I", "F", "I", "I", "I", "I", "F", "F"]
                card2a2_data = self.parser.parse_line(
                    card_lines[line_idx], card2a2_types)
                if any(x is not None for x in card2a2_data):
                    self.cards["Card 2a.2"] = {col: np.array(
                        [val], dtype=object) for col, val in zip(card2a2_cols, card2a2_data)}
                    line_idx += 1
        elif "SPG" in options:
            # Card 2b.1
            card2b1_cols = ["DX", "DY", "DZ", "ISPLINE", "KERNEL", None, "SMSTEP", "MSC"]
            card2b1_types = ["F", "F", "F", "I", "I", None, "I", "F"]
            card2b1_data = self.parser.parse_line(
                card_lines[line_idx], card2b1_types)
            self.cards["Card 2b.1"] = {col: np.array(
                [val], dtype=object) for col, val in zip(card2b1_cols, card2b1_data) if col}
            line_idx += 1
            # Card 2b.2 (Optional)
            if line_idx < len(card_lines):
                card2b2_cols = ["IDAM", "FS", "STRETCH",
                                "ITB", "MSFAC", "ISC", "BOXID", "PDAMP"]
                card2b2_types = ["I", "F", "F", "I", "F", "I", "I", "F"]
                card2b2_data = self.parser.parse_line(
                    card_lines[line_idx], card2b2_types)
                if any(x is not None for x in card2b2_data):
                    self.cards["Card 2b.2"] = {col: np.array(
                        [val], dtype=object) for col, val in zip(card2b2_cols, card2b2_data)}
                    line_idx += 1
        elif "MISC" in options:
            # Card 2c (Optional)
            if line_idx < len(card_lines):
                card2c_cols = ["COHTHK", None, None, None, None, None, None, None]
                card2c_types = ["F", None, None, None, None, None, None, None]
                card2c_data = self.parser.parse_line(
                    card_lines[line_idx], card2c_types)
                if any(x is not None for x in card2c_data):
                    self.cards["Card 2c"] = {col: np.array(
                        [val], dtype=object) for col, val in zip(card2c_cols, card2c_data) if col}
                    line_idx += 1

        # User-Defined Elements
        if elform in [101, 102, 103, 104, 105]:
            # Card 3
            card3_cols = ["NIP", "NXDOF", "IHGF", "ITAJ", "LMC", "NHSV", "XNOD", None]
            card3_types = ["I", "I", "I", "I", "I", "I", "I", None]
            card3_data = self.parser.parse_line(
                card_lines[line_idx], card3_types)
            self.cards["Card 3"] = {col: np.array(
                [val], dtype=object) for col, val in zip(card3_cols, card3_data) if col}
            line_idx += 1
            nip = card3_data[0] or 0
            lmc = card3_data[4] or 0

            # Card 4 (NIP times)
            if nip > 0:
                card4_cols = ["XI", "ETA", "ZETA", "WGT", None, None, None, None]
                card4_types = ["F", "F", "F", "F", None, None, None, None]
                card4_data = []
                for _ in range(nip):
                    data = self.parser.parse_line(
                        card_lines[line_idx], card4_types)
                    card4_data.append(data)
                    line_idx += 1
                arr = np.array(card4_data, dtype=object)
                self.cards["Card 4"] = {col: arr[:, i]
                                        for i, col in enumerate(card4_cols) if col}

            # Card 5 (ceil(LMC/8) times)
            if lmc > 0:
                num_card5 = math.ceil(lmc / 8)
                all_p_values = []
                for _ in range(num_card5):
                    # Each card has 8 fields
                    data = self.parser.parse_line(
                        card_lines[line_idx], ["F"] * 8)
                    all_p_values.extend(d for d in data if d is not None)
                    line_idx += 1

                # Create a single-row dict with P1, P2, ..., P(lmc) columns
                p_values_truncated = all_p_values[:lmc]
                p_cols = [f"P{i+1}" for i in range(len(p_values_truncated))]
                if p_values_truncated:
                    self.cards["Card 5"] = {col: np.array(
                        [val], dtype=object) for col, val in zip(p_cols, p_values_truncated)}

    def write(self, file_obj: TextIO):
        """Writes the *SECTION_SOLID keyword to a file."""
        file_obj.write(f"{self.full_keyword}\n")

        # Card 1
        card1 = self.cards.get("Card 1")
        if card1 is not None and len(next(iter(card1.values()), [])) > 0:
            cols = ["SECID", "ELFORM", "AET", None, None, None, "COHOFF", "GASKETT"]
            types = ["I/A", "I", "I", None, None, None, "F", "F"]
            file_obj.write(self.parser.format_header(cols))
            line_parts = [self.parser.format_field(
                card1.get(col, [None])[0] if col else None, typ) for col, typ in zip(cols, types)]
            file_obj.write("".join(line_parts) + "\n")

        # Option-based cards
        options = [o.upper() for o in self.options]
        if "EFG" in options:
            for card_name, cols, types in [
                ("Card 2a.1", ["DX", "DY", "DZ", "ISPLINE", "IDILA", "IEBT", "IDIM", "TOLDEF"], [
                 "F", "F", "F", "I", "I", "I", "I", "F"]),
                ("Card 2a.2", ["IPS", "STIME", "IKEN", "SF", "CMID", "IBR", "DS", "ECUT"], [
                 "I", "F", "I", "I", "I", "I", "F", "F"]),
            ]:
                card = self.cards.get(card_name)
                if card is not None and len(next(iter(card.values()), [])) > 0:
                    file_obj.write(self.parser.format_header(cols))
                    line_parts = [self.parser.format_field(
                        card.get(col, [None])[0], typ) for col, typ in zip(cols, types)]
                    file_obj.write("".join(line_parts) + "\n")
        elif "SPG" in options:
            card2b1 = self.cards.get("Card 2b.1")
            if card2b1 is not None and len(next(iter(card2b1.values()), [])) > 0:
                cols = ["DX", "DY", "DZ", "ISPLINE", "KERNEL", None, "SMSTEP", "MSC"]
                types = ["F", "F", "F", "I", "I", None, "I", "F"]
                file_obj.write(self.parser.format_header(cols))
                line_parts = [self.parser.format_field(
                    card2b1.get(col, [None])[0] if col else None, typ) for col, typ in zip(cols, types)]
                file_obj.write("".join(line_parts) + "\n")

            card2b2 = self.cards.get("Card 2b.2")
            if card2b2 is not None and len(next(iter(card2b2.values()), [])) > 0:
                cols = ["IDAM", "FS", "STRETCH", "ITB", "MSFAC", "ISC", "BOXID", "PDAMP"]
                types = ["I", "F", "F", "I", "F", "I", "I", "F"]
                file_obj.write(self.parser.format_header(cols))
                line_parts = [self.parser.format_field(
                    card2b2.get(col, [None])[0], typ) for col, typ in zip(cols, types)]
                file_obj.write("".join(line_parts) + "\n")
        elif "MISC" in options:
            card = self.cards.get("Card 2c")
            if card is not None and len(next(iter(card.values()), [])) > 0:
                cols = ["COHTHK", None, None, None, None, None, None, None]
                types = ["F", None, None, None, None, None, None, None]
                file_obj.write(self.parser.format_header(cols))
                line_parts = [self.parser.format_field(
                    card.get(col, [None])[0] if col else None, typ) for col, typ in zip(cols, types)]
                file_obj.write("".join(line_parts) + "\n")

        # User-Defined Elements
        card3 = self.cards.get("Card 3")
        if card3 is not None and len(next(iter(card3.values()), [])) > 0:
            cols = ["NIP", "NXDOF", "IHGF", "ITAJ", "LMC", "NHSV", "XNOD", None]
            types = ["I", "I", "I", "I", "I", "I", "I", None]
            file_obj.write(self.parser.format_header(cols))
            line_parts = [self.parser.format_field(
                card3.get(col, [None])[0] if col else None, typ) for col, typ in zip(cols, types)]
            file_obj.write("".join(line_parts) + "\n")

            # Card 4
            card4 = self.cards.get("Card 4")
            if card4 is not None and len(next(iter(card4.values()), [])) > 0:
                cols = ["XI", "ETA", "ZETA", "WGT", None, None, None, None]
                types = ["F", "F", "F", "F", None, None, None, None]
                file_obj.write(self.parser.format_header(cols))
                nrows = len(card4[[c for c in cols if c][0]])
                for i in range(nrows):
                    line_parts = [self.parser.format_field(
                        card4.get(col, [None] * nrows)[i] if col else None, typ) for col, typ in zip(cols, types)]
                    file_obj.write("".join(line_parts) + "\n")

            # Card 5
            card5 = self.cards.get("Card 5")
            if card5 is not None and len(card5) > 0:
                # Sort P-values by their number (P1, P2, ...)
                p_cols = sorted(card5.keys(), key=lambda k: int(k[1:]))
                all_p_values = [card5[col][0] for col in p_cols]

                # Write header and data in chunks of 8
                for i in range(0, len(all_p_values), 8):
                    header_chunk = p_cols[i:i+8]
                    file_obj.write(self.parser.format_header(header_chunk))

                    data_chunk = all_p_values[i:i+8]
                    data_chunk.extend([None] * (8 - len(data_chunk)))
                    line_parts = [self.parser.format_field(
                        p, "F") for p in data_chunk]
                    file_obj.write("".join(line_parts) + "\n")
