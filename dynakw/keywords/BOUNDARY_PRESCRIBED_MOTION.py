"Implementation of the *BOUNDARY_PRESCRIBED_MOTION keyword."

from typing import TextIO, List
import numpy as np

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword


class BoundaryPrescribedMotion(LSDynaKeyword):
    """
    Implements the *BOUNDARY_PRESCRIBED_MOTION keyword.
    """
    keyword_string = "*BOUNDARY_PRESCRIBED_MOTION"

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        super().__init__(keyword_name, raw_lines)

    def _parse_raw_data(self, raw_lines: List[str]):
        """
        Parses the raw data for *BOUNDARY_PRESCRIBED_MOTION.
        """
        card_lines = [line for line in raw_lines[1:]
                      if line.strip() and not line.startswith('$')]
        if not card_lines:
            return

        line_idx = 0
        options = [o.upper() for o in self.options]

        # Card ID (Optional)
        if "ID" in options:
            card_id_cols = ["ID", "HEADING"]
            card_id_types = ["I", "A7"]
            card_id_data = self.parser.parse_line(
                card_lines[line_idx], card_id_types)
            self.cards["Card ID"] = {col: np.array(
                [val], dtype=object) for col, val in zip(card_id_cols, card_id_data)}
            line_idx += 1

        # Card 2 (Conditional)
        if "SET_BOX" in options:
            card2_cols = ["BOXID", "TOFFSET", "LCBCHK"]
            card2_types = ["I", "I", "I"]
            card2_data = self.parser.parse_line(
                card_lines[line_idx], card2_types)
            self.cards["Card 2"] = {col: np.array(
                [val], dtype=object) for col, val in zip(card2_cols, card2_data)}
            line_idx += 1

        # Card 4 (Conditional)
        if "SET_LINE" in options:
            card4_cols = ["NBEG", "NEND"]
            card4_types = ["I", "I"]
            card4_data = self.parser.parse_line(
                card_lines[line_idx], card4_types)
            self.cards["Card 4"] = {col: np.array(
                [val], dtype=object) for col, val in zip(card4_cols, card4_data)}
            line_idx += 1

        # Card 5 (Conditional)
        if "BNDOUT2DYNAIN" in options:
            card5_cols = ["PRMR"]
            card5_types = ["A"]
            card5_data = self.parser.parse_line(
                card_lines[line_idx], card5_types)
            self.cards["Card 5"] = {col: np.array(
                [val], dtype=object) for col, val in zip(card5_cols, card5_data)}
            line_idx += 1

        # Card 6 (Conditional)
        card6_options = ["POINT_UVW", "EDGE_UVW", "FACE_XYZ",
                         "SET_POINT_UVW", "SET_EDGE_UVW", "SET_FACE_XYZ"]
        if any(opt in options for opt in card6_options):
            card6_cols = ["FORM", "SFD"]
            card6_types = ["I", "F"]
            card6_data = self.parser.parse_line(
                card_lines[line_idx], card6_types)
            self.cards["Card 6"] = {col: np.array(
                [val], dtype=object) for col, val in zip(card6_cols, card6_data)}
            line_idx += 1

        # Card 1 and Card 3 (Main data)
        card1_data = []
        card3_data = []
        card1_cols = ["TYPEID", "DOF", "VAD",
                      "LCID", "SF", "VID", "DEATH", "BIRTH"]
        card1_types = ["I", "I", "I", "I", "F", "I", "F", "F"]
        card3_cols = ["OFFSET1", "OFFSET2", "LRB", "NODE1", "NODE2"]
        card3_types = ["F", "F", "I", "I", "I"]

        while line_idx < len(card_lines):
            # Card 1
            c1_data = self.parser.parse_line(
                card_lines[line_idx], card1_types)
            card1_data.append(c1_data)
            line_idx += 1

            dof = c1_data[1]
            vad = c1_data[2]

            # Card 3 (Conditional)
            if (dof is not None and abs(dof) in [9, 10, 11]) or vad == 4:
                if line_idx < len(card_lines):
                    c3_data = self.parser.parse_line(
                        card_lines[line_idx], card3_types)
                    card3_data.append(c3_data)
                    line_idx += 1
                else:
                    # Expected but not found
                    card3_data.append([None] * len(card3_cols))
            else:
                card3_data.append([None] * len(card3_cols))

        if card1_data:
            card1_arr = np.array(card1_data, dtype=object)
            self.cards["Card 1"] = {
                col: card1_arr[:, i] for i, col in enumerate(card1_cols)}

        if any(any(d is not None for d in row) for row in card3_data):
            card3_arr = np.array(card3_data, dtype=object)
            self.cards["Card 3"] = {
                col: card3_arr[:, i] for i, col in enumerate(card3_cols)}

    def write(self, file_obj: TextIO):
        """Writes the *BOUNDARY_PRESCRIBED_MOTION keyword to a file."""
        file_obj.write(f"{self.full_keyword}\n")

        # Optional single cards
        for card_name, cols, types, header in [
            ("Card ID", ["ID", "HEADING"], ["I", "A7"], ["id", "heading"]),
            ("Card 2", ["BOXID", "TOFFSET", "LCBCHK"], [
             "I", "I", "I"], ["boxid", "toffset", "lcbchk"]),
            ("Card 4", ["NBEG", "NEND"], ["I", "I"], ["nbeg", "nend"]),
            ("Card 5", ["PRMR"], ["A"], ["prmr"]),
            ("Card 6", ["FORM", "SFD"], ["I", "F"], ["form", "sfd"])
        ]:
            card = self.cards.get(card_name)
            if card is not None and len(next(iter(card.values()))) > 0:
                file_obj.write(
                    "$#" + "".join([f"{h:<10}" for h in header]) + "\n")
                line_parts = [self.parser.format_field(
                    card.get(col, [None])[0], typ) for col, typ in zip(cols, types)]
                file_obj.write("".join(line_parts) + "\n")

        # Main data cards (Card 1 and Card 3)
        card1 = self.cards.get("Card 1")
        if card1 is None or len(next(iter(card1.values()))) == 0:
            return

        card1_cols = ["TYPEID", "DOF", "VAD",
                      "LCID", "SF", "VID", "DEATH", "BIRTH"]
        card1_header = ["nid/sid", "dof", "vad",
                        "lcid", "sf", "vid", "death", "birth"]
        card3_cols = ["OFFSET1", "OFFSET2", "LRB", "NODE1", "NODE2"]
        card3_header = ["offset1", "offset2", "lrb", "node1", "node2"]

        file_obj.write("$#" + "".join([f"{h:<10}" for h in card1_header]) + "\n")

        card3 = self.cards.get("Card 3")
        num_rows = len(card1["TYPEID"])

        card1_types = ["I", "I", "I", "I", "F", "I", "F", "F"]
        card3_types = ["F", "F", "I", "I", "I"]

        for i in range(num_rows):
            # Write Card 1
            line_parts_1 = [self.parser.format_field(
                card1.get(col, [None]*num_rows)[i], typ)
                for col, typ in zip(card1_cols, card1_types)]
            file_obj.write("".join(line_parts_1) + "\n")

            # Write Card 3 if it exists for this row
            if card3 is not None:
                # Check if the row for card3 has any data
                if any(card3.get(col, [None]*num_rows)[i] is not None for col in card3_cols):
                    if i == 0: # Write header only once
                        file_obj.write("$#" + "".join([f"{h:<10}" for h in card3_header]) + "\n")
                    line_parts_3 = [self.parser.format_field(
                        card3.get(col, [None]*num_rows)[i], typ)
                        for col, typ in zip(card3_cols, card3_types)]
                    file_obj.write("".join(line_parts_3) + "\n")
