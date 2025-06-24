"""Implementation of the *ELEMENT_SOLID keyword."""

from typing import TextIO, List
import pandas as pd
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.enums import KeywordType


class ElementSolid(LSDynaKeyword):
    """
    Implements the *ELEMENT_SOLID keyword.
    Supports standard, legacy, and option-based formats.
    """

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        super().__init__(keyword_name, raw_lines)
        if self.keyword_type not in [KeywordType.ELEMENT_SOLID]:
            pass
        #self.is_legacy = False # set in super call

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
        first_line_fields = self.parser.parse_line(card_lines[0], ["I"] * 10, field_len=None)
        if sum(x is not None for x in first_line_fields[2:]) > 0:
            self.is_legacy = True
            self._parse_legacy_format(card_lines)
        else:
            self.is_legacy = False
            self._parse_standard_format(card_lines)

    def _parse_legacy_format(self, card_lines: List[str]):
        """Parses the obsolete single-card format."""
        columns = ["EID", "PID", "N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8"]
        field_types = ["I"] * 10
        flen = [8] * 10
        parsed_data = []
        for line in card_lines:
            parsed_fields = self.parser.parse_line(line, field_types, field_len=flen)
            if any(field is not None for field in parsed_fields):
                parsed_data.append(dict(zip(columns, parsed_fields)))

        self.cards["main"] = pd.DataFrame(parsed_data)

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
            chunk = card_lines[i : i + lines_per_element]
            if not chunk or not chunk[0].strip():
                continue

            it = iter(chunk)

            eid, pid = self.parser.parse_line(next(it), ["I", "I"], field_len=None)
            main_data.append({"EID": eid, "PID": pid})

            nodes = []
            for _ in range(num_node_cards):
                try:
                    nodes.extend(self.parser.parse_line(next(it), ["I"] * 10, field_len=[8]*10))
                except StopIteration:
                    nodes.extend([None] * 10)

            node_row = {"EID": eid}
            for j, node_id in enumerate(nodes):
                node_row[f"N{j+1}"] = node_id
            node_data.append(node_row)

            if has_ortho:
                a1, a2, a3 = self.parser.parse_line(next(it), ["F", "F", "F"], field_len=[16,16,16])
                d1, d2, d3 = self.parser.parse_line(next(it), ["F", "F", "F"], field_len=[16,16,16])
                ortho_data.append(
                    {
                        "EID": eid,
                        "A1_BETA": a1,
                        "A2": a2,
                        "A3": a3,
                        "D1": d1,
                        "D2": d2,
                        "D3": d3,
                    }
                )

            if has_dof:
                dof_nodes = self.parser.parse_line(next(it), ["I"] * 8, field_len=[8]*10)
                dof_row = {"EID": eid}
                for j, node_id in enumerate(dof_nodes):
                    dof_row[f"NS{j+1}"] = node_id
                dof_data.append(dof_row)

        self.cards["main"] = pd.DataFrame(main_data).set_index("EID")
        self.cards["nodes"] = pd.DataFrame(node_data).set_index("EID")
        if ortho_data:
            self.cards["ortho"] = pd.DataFrame(ortho_data).set_index("EID")
        if dof_data:
            self.cards["dof"] = pd.DataFrame(dof_data).set_index("EID")

    def write(self, file_obj: TextIO):
        """Writes the *ELEMENT_SOLID keyword to a file."""
        file_obj.write(f"{self.full_keyword}\n")

        if self.is_legacy:
            df = self.cards.get("main")
            if df is None or df.empty:
                return

            cols = ["EID", "PID", "N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8"]
            for _, row in df.iterrows():
                line_parts = [
                    self.parser.format_field(row.get(col), "I") for col in cols
                ]
                file_obj.write("".join(line_parts) + "\n")
            return

        main_df = self.cards.get("main")
        if main_df is None or main_df.empty:
            return

        nodes_df = self.cards.get("nodes")
        ortho_df = self.cards.get("ortho")
        dof_df = self.cards.get("dof")

        num_node_cards = self._get_num_node_cards()

        for eid, row in main_df.iterrows():
            line = self.parser.format_field(eid, "I") + self.parser.format_field(
                row["PID"], "I"
            )
            file_obj.write(f"{line}\n")

            if nodes_df is not None and eid in nodes_df.index:
                node_row = nodes_df.loc[eid]
                all_nodes = [
                    node_row.get(f"N{i+1}") for i in range(num_node_cards * 10)
                ]
                for i in range(num_node_cards):
                    node_chunk = all_nodes[i * 10 : (i + 1) * 10]
                    line_parts = [self.parser.format_field(n, "I") for n in node_chunk]
                    file_obj.write("".join(line_parts) + "\n")

            if ortho_df is not None and eid in ortho_df.index:
                ortho_row = ortho_df.loc[eid]
                line1_parts = [
                    self.parser.format_field(ortho_row.get(c), "F")
                    for c in ["A1_BETA", "A2", "A3"]
                ]
                file_obj.write("".join(line1_parts) + "\n")
                line2_parts = [
                    self.parser.format_field(ortho_row.get(c), "F")
                    for c in ["D1", "D2", "D3"]
                ]
                file_obj.write("".join(line2_parts) + "\n")

            if dof_df is not None and eid in dof_df.index:
                dof_row = dof_df.loc[eid]
                line_parts = [
                    self.parser.format_field(dof_row.get(f"NS{i+1}"), "I")
                    for i in range(8)
                ]
                file_obj.write("".join(line_parts) + "\n")
