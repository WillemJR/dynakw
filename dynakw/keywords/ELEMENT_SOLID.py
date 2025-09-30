"""Implementation of the *ELEMENT_SOLID keyword."""

from typing import TextIO, List
import numpy as np
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword


class ElementSolid(LSDynaKeyword):
    """
    Implements the *ELEMENT_SOLID keyword.
    Supports standard, legacy, and option-based formats.
    """
    keyword_string = "*ELEMENT_SOLID"

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        super().__init__(keyword_name, raw_lines)
        # self.is_legacy = False # set in super call

    def _parse_raw_data(self, raw_lines: List[str]):
        """
        Parses the raw data for *ELEMENT_SOLID, dispatching to the
        correct parser based on format detection.
        """
        card_lines = [line for line in raw_lines[1:] if line.strip()]
        if not card_lines:
            return

        # Check for legacy single-line format.
        # A standard format first card has 2 fields. A legacy has up to 10.
        # We check if there's content beyond the second field.
        first_line_fields = self.parser.parse_line(
            card_lines[0], ["I"] * 10, field_len=None)
        if sum(x is not None for x in first_line_fields[2:]) > 0:
            self.is_legacy = True
            self._parse_legacy_format(card_lines)
        else:
            self.is_legacy = False
            self._parse_standard_format(card_lines)

    def _parse_legacy_format(self, card_lines: List[str]):
        """Parses the obsolete single-card format."""
        columns = ["EID", "PID", "N1", "N2",
                   "N3", "N4", "N5", "N6", "N7", "N8"]
        field_types = ["I"] * 10
        flen = [8] * 10
        parsed_data = []
        for line in card_lines:
            parsed_fields = self.parser.parse_line(
                line, field_types, field_len=flen)
            if any(field is not None for field in parsed_fields):
                parsed_data.append(parsed_fields)

        # Save as dict of numpy arrays
        if parsed_data:
            arr = np.array(parsed_data, dtype=object)
            self.cards["main"] = {col: arr[:, i]
                                  for i, col in enumerate(columns)}
        else:
            self.cards["main"] = {col: np.array(
                [], dtype=object) for col in columns}

    def _get_num_node_cards(self) -> int:
        """Determines how many node cards to expect based on keyword options."""
        opts = [o.upper() for o in self.options]
        if any(opt in opts for opt in ["H64", "H8TOH64"]):
            return 7
        if any(opt in opts for opt in ["P40"]):
            return 4
        if any(opt in opts for opt in ["H27", "H8TOH27", "P21"]):
            return 3
        if any(opt in opts for opt in ["H20", "H8TOH20", "T20", "T15", "TET4TOTET10"]):
            return 2
        return 1

    def _parse_standard_format(self, card_lines: List[str]):
        """Parses the standard multi-card format."""
        has_ortho = "ORTHO" in [o.upper() for o in self.options]
        has_dof = "DOF" in [o.upper() for o in self.options]
        num_node_cards = self._get_num_node_cards()

        lines_per_element = 1 + num_node_cards
        if has_ortho:
            lines_per_element += 2
        if has_dof:
            lines_per_element += 1

        main_data, node_data, ortho_data, dof_data = [], [], [], []

        for i in range(0, len(card_lines), lines_per_element):
            chunk = card_lines[i: i + lines_per_element]
            if not chunk or not chunk[0].strip():
                continue

            it = iter(chunk)

            eid, pid = self.parser.parse_line(
                next(it), ["I", "I"], field_len=None)
            main_data.append([eid, pid])

            nodes = []
            for _ in range(num_node_cards):
                try:
                    nodes.extend(self.parser.parse_line(
                        next(it), ["I"] * 10, field_len=[8] * 10))
                except StopIteration:
                    nodes.extend([None] * 10)

            node_row = [eid] + nodes
            node_data.append(node_row)

            if has_ortho:
                a1, a2, a3 = self.parser.parse_line(
                    next(it), ["F", "F", "F"], field_len=[16, 16, 16])
                d1, d2, d3 = self.parser.parse_line(
                    next(it), ["F", "F", "F"], field_len=[16, 16, 16])
                ortho_data.append(
                    [eid, a1, a2, a3, d1, d2, d3]
                )

            if has_dof:
                dof_nodes = self.parser.parse_line(
                    next(it), ["I"] * 8, field_len=[8] * 10)
                dof_row = [eid] + list(dof_nodes)
                dof_data.append(dof_row)

        # Convert to dict of numpy arrays
        main_cols = ["EID", "PID"]
        if main_data:
            arr = np.array(main_data, dtype=object)
            self.cards["main"] = {col: arr[:, i]
                                  for i, col in enumerate(main_cols)}
        else:
            self.cards["main"] = {col: np.array(
                [], dtype=object) for col in main_cols}

        node_cols = ["EID"] + [f"N{i+1}" for i in range(num_node_cards * 10)]
        if node_data:
            arr = np.array(node_data, dtype=object)
            self.cards["nodes"] = {col: arr[:, i]
                                   for i, col in enumerate(node_cols)}
        else:
            self.cards["nodes"] = {col: np.array(
                [], dtype=object) for col in node_cols}

        if ortho_data:
            ortho_cols = ["EID", "A1_BETA", "A2", "A3", "D1", "D2", "D3"]
            arr = np.array(ortho_data, dtype=object)
            self.cards["ortho"] = {col: arr[:, i]
                                   for i, col in enumerate(ortho_cols)}
        if dof_data:
            dof_cols = ["EID"] + [f"NS{i+1}" for i in range(8)]
            arr = np.array(dof_data, dtype=object)
            self.cards["dof"] = {col: arr[:, i]
                                 for i, col in enumerate(dof_cols)}

    def write(self, file_obj: TextIO):
        """Writes the *ELEMENT_SOLID keyword to a file."""
        file_obj.write(f"{self.full_keyword}\n")

        if self.is_legacy:
            card = self.cards.get("main")
            if card is None or not card or len(next(iter(card.values()))) == 0:
                return

            cols = ["EID", "PID", "N1", "N2",
                    "N3", "N4", "N5", "N6", "N7", "N8"]
            header = "$#" + "".join([f"{name.lower():>8}" for name in cols])
            file_obj.write(header + "\n")
            data_length = len(card["EID"])
            for idx in range(data_length):
                line_parts = [
                    self.parser.format_field(card[col][idx], "I") for col in cols
                ]
                file_obj.write("".join(line_parts) + "\n")
            return

        card_main = self.cards.get("main")
        if card_main is None or not card_main or len(next(iter(card_main.values()))) == 0:
            return

        card_nodes = self.cards.get("nodes")
        card_ortho = self.cards.get("ortho")
        card_dof = self.cards.get("dof")

        num_node_cards = self._get_num_node_cards()
        main_length = len(card_main["EID"])

        # Write headers
        file_obj.write("$#" + f"{'eid':>10}{'pid':>10}\n")
        if card_nodes is not None and num_node_cards > 0:
            node_cols = [f"n{i+1}" for i in range(10)]
            file_obj.write(
                "$#" + "".join([f"{name:>8}" for name in node_cols]) + "\n")
        if card_ortho is not None:
            ortho_cols1 = ["a1_beta", "a2", "a3"]
            file_obj.write(
                "$#" + "".join([f"{name:>16}" for name in ortho_cols1]) + "\n")
            ortho_cols2 = ["d1", "d2", "d3"]
            file_obj.write(
                "$#" + "".join([f"{name:>16}" for name in ortho_cols2]) + "\n")
        if card_dof is not None:
            dof_cols = [f"ns{i+1}" for i in range(8)]
            file_obj.write(
                "$#" + "".join([f"{name:>8}" for name in dof_cols]) + "\n")

        for idx in range(main_length):
            eid = card_main["EID"][idx]
            pid = card_main["PID"][idx]
            line = self.parser.format_field(
                eid, "I") + self.parser.format_field(pid, "I")
            file_obj.write(f"{line}\n")

            if card_nodes is not None and "EID" in card_nodes and idx < len(card_nodes["EID"]):
                all_nodes = [card_nodes.get(
                    f"N{i+1}", [None] * main_length)[idx] for i in range(num_node_cards * 10)]
                for i in range(num_node_cards):
                    node_chunk = all_nodes[i * 10: (i + 1) * 10]
                    line_parts = [self.parser.format_field(
                        n, "I") for n in node_chunk]
                    file_obj.write("".join(line_parts) + "\n")

            if card_ortho is not None and "EID" in card_ortho and idx < len(card_ortho["EID"]):
                line1_parts = [
                    self.parser.format_field(card_ortho.get(
                        c, [None] * main_length)[idx], "F")
                    for c in ["A1_BETA", "A2", "A3"]
                ]
                file_obj.write("".join(line1_parts) + "\n")
                line2_parts = [
                    self.parser.format_field(card_ortho.get(
                        c, [None] * main_length)[idx], "F")
                    for c in ["D1", "D2", "D3"]
                ]
                file_obj.write("".join(line2_parts) + "\n")

            if card_dof is not None and "EID" in card_dof and idx < len(card_dof["EID"]):
                line_parts = [
                    self.parser.format_field(card_dof.get(
                        f"NS{i+1}", [None] * main_length)[idx], "I")
                    for i in range(8)
                ]
                file_obj.write("".join(line_parts) + "\n")
