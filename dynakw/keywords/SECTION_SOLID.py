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
        card1_columns = ["SECID", "ELFORM", "AET", "COHOFF", "GASKETT"]
        card1_types = ["I/A", "I", "I", "F", "F"]
        card1_data = self.parser.parse_line(card_lines[0], card1_types)
        self.cards["Card 1"] = {col: np.array(
            [val], dtype=object) for col, val in zip(card1_columns, card1_data)}

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
            card2b1_cols = ["DX", "DY", "DZ",
                            "ISPLINE", "KERNEL", "SMSTEP", "MSC"]
            card2b1_types = ["F", "F", "F", "I", "I", "I", "F"]
            card2b1_data = self.parser.parse_line(
                card_lines[line_idx], card2b1_types)
            self.cards["Card 2b.1"] = {col: np.array(
                [val], dtype=object) for col, val in zip(card2b1_cols, card2b1_data)}
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
                card2c_cols = ["COHTHK"]
                card2c_types = ["F"]
                card2c_data = self.parser.parse_line(
                    card_lines[line_idx], card2c_types)
                if any(x is not None for x in card2c_data):
                    self.cards["Card 2c"] = {col: np.array(
                        [val], dtype=object) for col, val in zip(card2c_cols, card2c_data)}
                    line_idx += 1

        # User-Defined Elements
        if elform in [101, 102, 103, 104, 105]:
            # Card 3
            card3_cols = ["NIP", "NXDOF", "IHGF",
                          "ITAJ", "LMC", "NHSV", "XNOD"]
            card3_types = ["I", "I", "I", "I", "I", "I", "I"]
            card3_data = self.parser.parse_line(
                card_lines[line_idx], card3_types)
            self.cards["Card 3"] = {col: np.array(
                [val], dtype=object) for col, val in zip(card3_cols, card3_data)}
            line_idx += 1
            nip = card3_data[0] or 0
            lmc = card3_data[4] or 0

            # Card 4 (NIP times)
            if nip > 0:
                card4_cols = ["XI", "ETA", "ZETA", "WGT"]
                card4_types = ["F", "F", "F", "F"]
                card4_data = []
                for _ in range(nip):
                    data = self.parser.parse_line(
                        card_lines[line_idx], card4_types)
                    card4_data.append(data)
                    line_idx += 1
                arr = np.array(card4_data, dtype=object)
                self.cards["Card 4"] = {col: arr[:, i]
                                        for i, col in enumerate(card4_cols)}

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
        if card1 is not None and len(next(iter(card1.values()))) > 0:
            cols = ["SECID", "ELFORM", "AET", "COHOFF", "GASKETT"]
            types = ["I/A", "I", "I", "F", "F"]
            file_obj.write(
                "$#" + "".join([f"{col.lower():>10}" for col in cols]) + "\n")
            line_parts = [self.parser.format_field(
                card1.get(col, [None])[0], typ) for col, typ in zip(cols, types)]
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
                if card is not None and len(next(iter(card.values()))) > 0:
                    file_obj.write(
                        "$#" + "".join([f"{col.lower():>10}" for col in cols]) + "\n")
                    line_parts = [self.parser.format_field(
                        card.get(col, [None])[0], typ) for col, typ in zip(cols, types)]
                    file_obj.write("".join(line_parts) + "\n")
        elif "SPG" in options:
            for card_name, cols, types in [
                ("Card 2b.1", ["DX", "DY", "DZ", "ISPLINE", "KERNEL", "SMSTEP", "MSC"], [
                 "F", "F", "F", "I", "I", "I", "F"]),
                ("Card 2b.2", ["IDAM", "FS", "STRETCH", "ITB", "MSFAC", "ISC", "BOXID", "PDAMP"], [
                 "I", "F", "F", "I", "F", "I", "I", "F"]),
            ]:
                card = self.cards.get(card_name)
                if card is not None and len(next(iter(card.values()))) > 0:
                    file_obj.write(
                        "$#" + "".join([f"{col.lower():>10}" for col in cols]) + "\n")
                    line_parts = [self.parser.format_field(
                        card.get(col, [None])[0], typ) for col, typ in zip(cols, types)]
                    file_obj.write("".join(line_parts) + "\n")
        elif "MISC" in options:
            card = self.cards.get("Card 2c")
            if card is not None and len(next(iter(card.values()))) > 0:
                file_obj.write("$#" + f"{'cohthk':>10}\n")
                line_parts = [self.parser.format_field(
                    card.get("COHTHK", [None])[0], "F")]
                file_obj.write("".join(line_parts) + "\n")

        # User-Defined Elements
        card3 = self.cards.get("Card 3")
        if card3 is not None and len(next(iter(card3.values()))) > 0:
            cols = ["NIP", "NXDOF", "IHGF", "ITAJ", "LMC", "NHSV", "XNOD"]
            types = ["I", "I", "I", "I", "I", "I", "I"]
            file_obj.write(
                "$#" + "".join([f"{col.lower():>10}" for col in cols]) + "\n")
            line_parts = [self.parser.format_field(
                card3.get(col, [None])[0], typ) for col, typ in zip(cols, types)]
            file_obj.write("".join(line_parts) + "\n")

            # Card 4
            card4 = self.cards.get("Card 4")
            if card4 is not None and len(next(iter(card4.values()))) > 0:
                cols = ["XI", "ETA", "ZETA", "WGT"]
                types = ["F", "F", "F", "F"]
                file_obj.write(
                    "$#" + "".join([f"{col.lower():>10}" for col in cols]) + "\n")
                nrows = len(card4[cols[0]])
                for i in range(nrows):
                    line_parts = [self.parser.format_field(
                        card4.get(col, [None] * nrows)[i], typ) for col, typ in zip(cols, types)]
                    file_obj.write("".join(line_parts) + "\n")

            # Card 5
            card5 = self.cards.get("Card 5")
            if card5 is not None and len(card5) > 0:
                # All P values are in single-row arrays
                p_cols = [col for col in card5]
                file_obj.write(
                    "$#" + "".join([f"{col.lower():>10}" for col in p_cols]) + "\n")
                all_p_values = [card5[col][0] for col in p_cols]
                for i in range(0, len(all_p_values), 8):
                    chunk = all_p_values[i:i + 8]
                    chunk.extend([None] * (8 - len(chunk)))  # Pad to 8 fields
                    line_parts = [self.parser.format_field(
                        p, "F") for p in chunk]
                    file_obj.write("".join(line_parts) + "\n")
