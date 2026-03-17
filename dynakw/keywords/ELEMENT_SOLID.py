"""Implementation of the *ELEMENT_SOLID keyword."""

from typing import TextIO, List
import numpy as np
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class ElementSolid(LSDynaKeyword):
    """
    Implements the *ELEMENT_SOLID keyword.
    Supports standard, legacy, and option-based formats.
    """
    keyword_string = "*ELEMENT_SOLID"

    # Schemas for the common standard format (8-node hex, 1 node card, no ORTHO/DOF).
    # Used by _parse_grouped_lines and _write_grouped_schemas.
    _STANDARD_SCHEMAS = [
        CardSchema("Card 1", [
            CardField("EID", "I", width=8),
            CardField("PID", "I", width=8),
        ], write_header=True),
        CardSchema("nodes", [
            CardField(f"N{i+1}", "I", width=8) for i in range(10)
        ], write_header=True),
    ]

    def _parse_raw_data(self, raw_lines: List[str]):
        card_lines = [line for line in raw_lines[1:] if line.strip()]
        if not card_lines:
            return

        # Detect legacy (single-line) vs standard (multi-line) format.
        first_fields = self.parser.parse_line(
            card_lines[0], ["I"] * 10, field_len=[8] * 10)
        if sum(first_fields[2:]) > 0:
            self.is_legacy = True
            self._parse_legacy_format(card_lines)
        else:
            self.is_legacy = False
            data_lines = [l for l in card_lines if not l.strip().startswith('$')]
            if self._is_complex():
                self._parse_standard_format(data_lines)
            else:
                self._parse_grouped_lines(data_lines, self._STANDARD_SCHEMAS)

    def _is_complex(self) -> bool:
        """True when the keyword uses options that need more than 1 node card,
        or ORTHO/DOF cards — i.e. cases not covered by _STANDARD_SCHEMAS."""
        opts = {o.upper() for o in self.options}
        return bool(opts & {"H64", "H8TOH64", "P40", "H27", "H8TOH27", "P21",
                            "H20", "H8TOH20", "T20", "T15", "TET4TOTET10",
                            "ORTHO", "DOF"})

    def write(self, file_obj: TextIO):
        file_obj.write(f"{self.full_keyword}\n")

        card_main = self.cards.get("Card 1")
        if card_main is None or len(card_main["EID"]) == 0:
            return

        if self._is_complex():
            self._write_complex(file_obj)
        else:
            self._write_grouped_schemas(file_obj, self._STANDARD_SCHEMAS)

    # ------------------------------------------------------------------
    # Legacy format
    # ------------------------------------------------------------------

    def _parse_legacy_format(self, card_lines: List[str]):
        """Parses the obsolete single-card format."""
        field_types = ["I"] * 10
        flen = [8] * 10
        parsed_data = []
        for line in card_lines:
            parsed_fields = self.parser.parse_line(line, field_types, field_len=flen)
            if any(field is not None for field in parsed_fields):
                parsed_data.append(parsed_fields)

        if parsed_data:
            arr = np.array(parsed_data, dtype=object)
            self.cards["Card 1"] = {
                "EID": arr[:, 0].astype(np.int32),
                "PID": arr[:, 1].astype(np.int32),
            }
            node_cols = ["EID"] + [f"N{i+1}" for i in range(8)]
            node_data = np.hstack([arr[:, 0:1], arr[:, 2:10]])
            self.cards["nodes"] = {
                col: node_data[:, i].astype(np.int32)
                for i, col in enumerate(node_cols)
            }
        else:
            self.cards["Card 1"] = {col: np.array([], dtype=np.int32) for col in ["EID", "PID"]}
            self.cards["nodes"] = {
                col: np.array([], dtype=np.int32)
                for col in ["EID"] + [f"N{i+1}" for i in range(8)]
            }

    # ------------------------------------------------------------------
    # Complex standard format (ORTHO, DOF, multi-node-card variants)
    # ------------------------------------------------------------------

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
        """Parses the standard multi-card format for complex option combinations."""
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

            eid, pid = self.parser.parse_line(next(it), ["I", "I"], field_len=None)
            main_data.append([eid, pid])

            nodes = []
            for _ in range(num_node_cards):
                try:
                    nodes.extend(self.parser.parse_line(
                        next(it), ["I"] * 10, field_len=[8] * 10))
                except StopIteration:
                    nodes.extend([None] * 10)

            node_data.append([eid] + nodes)

            if has_ortho:
                a1, a2, a3 = self.parser.parse_line(
                    next(it), ["F", "F", "F"], field_len=[16, 16, 16])
                d1, d2, d3 = self.parser.parse_line(
                    next(it), ["F", "F", "F"], field_len=[16, 16, 16])
                ortho_data.append([eid, a1, a2, a3, d1, d2, d3])

            if has_dof:
                dof_nodes = self.parser.parse_line(
                    next(it), ["I"] * 8, field_len=[8] * 10)
                dof_data.append([eid] + list(dof_nodes))

        if main_data:
            arr = np.array(main_data, dtype=object)
            self.cards["Card 1"] = {
                "EID": arr[:, 0].astype(np.int32),
                "PID": arr[:, 1].astype(np.int32),
            }
        else:
            self.cards["Card 1"] = {col: np.array([], dtype=np.int32) for col in ["EID", "PID"]}

        node_cols = ["EID"] + [f"N{i+1}" for i in range(num_node_cards * 10)]
        if node_data:
            arr = np.array(node_data, dtype=object)
            self.cards["nodes"] = {
                col: arr[:, i].astype(np.int32) for i, col in enumerate(node_cols)
            }
        else:
            self.cards["nodes"] = {col: np.array([], dtype=np.int32) for col in node_cols}

        if ortho_data:
            arr = np.array(ortho_data, dtype=object)
            self.cards["ortho"] = {
                "EID":     arr[:, 0].astype(np.int32),
                "A1_BETA": arr[:, 1].astype(np.float64),
                "A2":      arr[:, 2].astype(np.float64),
                "A3":      arr[:, 3].astype(np.float64),
                "D1":      arr[:, 4].astype(np.float64),
                "D2":      arr[:, 5].astype(np.float64),
                "D3":      arr[:, 6].astype(np.float64),
            }
        if dof_data:
            dof_cols = ["EID"] + [f"NS{i+1}" for i in range(8)]
            arr = np.array(dof_data, dtype=object)
            self.cards["dof"] = {
                col: arr[:, i].astype(np.int32) for i, col in enumerate(dof_cols)
            }

    def _write_complex(self, file_obj: TextIO):
        """Write for complex option combinations (ORTHO, DOF, multi-node-card)."""
        card_main = self.cards.get("Card 1")
        card_nodes = self.cards.get("nodes")
        card_ortho = self.cards.get("ortho")
        card_dof = self.cards.get("dof")

        num_node_cards = self._get_num_node_cards()
        main_length = len(card_main["EID"])

        file_obj.write(self.parser.format_header(['eid', 'pid'], field_len=8))
        if card_nodes is not None and num_node_cards > 0:
            file_obj.write(self.parser.format_header(
                [f"n{i+1}" for i in range(10)], field_len=8))
        if card_ortho is not None:
            file_obj.write(self.parser.format_header(["a1_beta", "a2", "a3"], field_len=16))
            file_obj.write(self.parser.format_header(["d1", "d2", "d3"], field_len=16))
        if card_dof is not None:
            file_obj.write(self.parser.format_header(
                [f"ns{i+1}" for i in range(8)], field_len=8))

        for idx in range(main_length):
            eid = card_main["EID"][idx]
            pid = card_main["PID"][idx]
            file_obj.write(
                self.parser.format_field(eid, "I", field_len=8) +
                self.parser.format_field(pid, "I", field_len=8) + "\n"
            )

            if card_nodes is not None:
                all_nodes = [
                    card_nodes.get(f"N{i+1}", [None] * main_length)[idx]
                    for i in range(num_node_cards * 10)
                ]
                for i in range(num_node_cards):
                    parts = [
                        self.parser.format_field(n, "I", field_len=8)
                        for n in all_nodes[i * 10: (i + 1) * 10]
                    ]
                    file_obj.write("".join(parts) + "\n")

            if card_ortho is not None and idx < len(card_ortho["EID"]):
                file_obj.write("".join(
                    self.parser.format_field(card_ortho[c][idx], "F")
                    for c in ["A1_BETA", "A2", "A3"]
                ) + "\n")
                file_obj.write("".join(
                    self.parser.format_field(card_ortho[c][idx], "F")
                    for c in ["D1", "D2", "D3"]
                ) + "\n")

            if card_dof is not None and idx < len(card_dof["EID"]):
                file_obj.write("".join(
                    self.parser.format_field(card_dof.get(f"NS{i+1}", [None] * main_length)[idx], "I")
                    for i in range(8)
                ) + "\n")
