"""Implementation of the *ELEMENT_SHELL keyword."""

from typing import TextIO, List
import numpy as np
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.enums import KeywordType


class ElementShell(LSDynaKeyword):
    """
    Represents the *ELEMENT_SHELL keyword in an LS-DYNA keyword file.

    This class handles all variants of the *ELEMENT_SHELL keyword, including
    options like THICKNESS, BETA, MCID, OFFSET, DOF, COMPOSITE, and
    COMPOSITE_LONG.
    """

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        super().__init__(keyword_name, raw_lines)
        if self.keyword_type not in [KeywordType.ELEMENT_SHELL]:
            pass

    def _parse_raw_data(self, raw_lines: List[str]):
        """
        Parses the raw data for *ELEMENT_SHELL, handling various formats and options.
        """
        card_lines = [line for line in raw_lines[1:] if line.strip() and not line.strip().startswith('$')]
        if not card_lines:
            return

        opts = [o.upper() for o in self.options]
        has_thickness = "THICKNESS" in opts
        has_beta = "BETA" in opts
        has_mcid = "MCID" in opts
        has_offset = "OFFSET" in opts
        has_dof = "DOF" in opts
        has_composite = "COMPOSITE" in opts
        has_composite_long = "COMPOSITE_LONG" in opts

        parsed_elements = []
        i = 0
        while i < len(card_lines):
            line = card_lines[i]
            i += 1
            element_data = {}

            # Card 1: Main Element Definition
            card1_fields = self.parser.parse_line(line, ["I"] * 10, field_len=[8] * 10)
            eid, pid, n1, n2, n3, n4, n5, n6, n7, n8 = card1_fields

            element_data["Card 1"] = {"EID": eid, "PID": pid, "N1": n1, "N2": n2, "N3": n3, "N4": n4, "N5": n5, "N6": n6, "N7": n7, "N8": n8}
            has_midside_nodes = any(n is not None and n > 0 for n in [n5, n6, n7, n8])

            # Card 2: Thickness/Beta/MCID
            if has_thickness or has_beta or has_mcid:
                line = card_lines[i]
                i += 1
                card2_fields = self.parser.parse_line(line, ["F"] * 5, field_len=[10]*5)
                thic1, thic2, thic3, thic4, beta_mcid = card2_fields
                element_data["Card 2"] = {"THIC1": thic1, "THIC2": thic2, "THIC3": thic3, "THIC4": thic4}
                if has_beta:
                    element_data["Card 2"]["BETA"] = beta_mcid
                elif has_mcid:
                    element_data["Card 2"]["MCID"] = beta_mcid

            # Card 3: Mid-side Node Thickness
            if has_midside_nodes and has_thickness:
                line = card_lines[i]
                i += 1
                card3_fields = self.parser.parse_line(line, ["F"] * 4, field_len=[10]*4)
                thic5, thic6, thic7, thic8 = card3_fields
                element_data["Card 3"] = {"THIC5": thic5, "THIC6": thic6, "THIC7": thic7, "THIC8": thic8}

            # Card 4: Offset
            if has_offset:
                line = card_lines[i]
                i += 1
                offset = self.parser.parse_line(line, ["F"], field_len=[10])
                element_data["Card 4"] = {"OFFSET": offset[0]}

            # Card 5: Scalar Node
            if has_dof:
                line = card_lines[i]
                i += 1
                ns1, ns2, ns3, ns4 = self.parser.parse_line(line, ["I"] * 4, field_len=[10]*4)
                element_data["Card 5"] = {"NS1": ns1, "NS2": ns2, "NS3": ns3, "NS4": ns4}

            # Card 6+: Composite Integration Point
            if has_composite:
                composite_data = []
                while i < len(card_lines) and not card_lines[i].strip().startswith('*'):
                    line = card_lines[i]
                    mid1, thick1, b1, mid2, thick2, b2 = self.parser.parse_line(line, ["I", "F", "F", "I", "F", "F"], field_len=[10]*6)
                    if mid2 is None or mid2 == 0:
                        composite_data.append({"MID1": mid1, "THICK1": thick1, "B1": b1})
                    else:
                        composite_data.append({"MID1": mid1, "THICK1": thick1, "B1": b1, "MID2": mid2, "THICK2": thick2, "B2": b2})
                    i += 1
                element_data["Card 6"] = composite_data

            # Card 7+: Composite Long Integration Point
            if has_composite_long:
                composite_long_data = []
                while i < len(card_lines) and not card_lines[i].strip().startswith('*'):
                    line = card_lines[i]
                    mid1, thick1, b1, plyid1 = self.parser.parse_line(line, ["I", "F", "F", "I"], field_len=[10]*4)
                    if plyid1 is None or plyid1 == 0:
                        composite_long_data.append({"MID1": mid1, "THICK1": thick1, "B1": b1})
                    else:
                        composite_long_data.append({"MID1": mid1, "THICK1": thick1, "B1": b1, "PLYID1": plyid1})
                    i += 1
                element_data["Card 7"] = composite_long_data

            parsed_elements.append(element_data)

        if not parsed_elements:
            return

        all_card_keys = sorted(list(set(key for elem in parsed_elements for key in elem.keys())))

        for key in all_card_keys:
            self.cards[key] = [elem.get(key) for elem in parsed_elements]


    def write(self, file_obj: TextIO):
        """Writes the keyword and its data to a file object."""
        file_obj.write(self.full_keyword + "\n")

        if 'Card 1' not in self.cards:
            return

        num_elements = len(self.cards['Card 1'])

        for i in range(num_elements):
            # Card 1
            c1 = self.cards['Card 1'][i]
            if c1:
                card1_fields = [c1.get(f, 0) for f in ["EID", "PID", "N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8"]]
                card1_types = ['I'] * 10
                card1_line = "".join(
                    self.parser.format_field(val, typ, 8)
                    for val, typ in zip(card1_fields, card1_types)
                )
                file_obj.write(card1_line + "\n")

            # Card 2
            if 'Card 2' in self.cards and self.cards['Card 2'][i]:
                c2 = self.cards['Card 2'][i]
                beta_or_mcid = c2.get("BETA", c2.get("MCID", 0.0))
                card2_fields = [c2.get("THIC1", 0.0), c2.get("THIC2", 0.0), c2.get("THIC3", 0.0), c2.get("THIC4", 0.0), beta_or_mcid]
                card2_types = ['F'] * 5
                card2_line = "".join(
                    self.parser.format_field(val, typ, 10)
                    for val, typ in zip(card2_fields, card2_types)
                )
                file_obj.write(card2_line + "\n")

            # Card 3
            if 'Card 3' in self.cards and self.cards['Card 3'][i]:
                c3 = self.cards['Card 3'][i]
                card3_fields = [c3.get("THIC5", 0.0), c3.get("THIC6", 0.0), c3.get("THIC7", 0.0), c3.get("THIC8", 0.0)]
                card3_types = ['F'] * 4
                card3_line = "".join(
                    self.parser.format_field(val, typ, 10)
                    for val, typ in zip(card3_fields, card3_types)
                )
                file_obj.write(card3_line + "\n")

            # Card 4
            if 'Card 4' in self.cards and self.cards['Card 4'][i]:
                c4 = self.cards['Card 4'][i]
                card4_line = self.parser.format_field(c4.get("OFFSET", 0.0), 'F', 10)
                file_obj.write(card4_line + "\n")

            # Card 5
            if 'Card 5' in self.cards and self.cards['Card 5'][i]:
                c5 = self.cards['Card 5'][i]
                card5_fields = [c5.get("NS1", 0), c5.get("NS2", 0), c5.get("NS3", 0), c5.get("NS4", 0)]
                card5_types = ['I'] * 4
                card5_line = "".join(
                    self.parser.format_field(val, typ, 10)
                    for val, typ in zip(card5_fields, card5_types)
                )
                file_obj.write(card5_line + "\n")

            # Card 6
            if 'Card 6' in self.cards and self.cards['Card 6'][i]:
                for comp_data in self.cards['Card 6'][i]:
                    if "MID2" in comp_data:
                        card6_fields = [comp_data["MID1"], comp_data["THICK1"], comp_data["B1"], comp_data["MID2"], comp_data["THICK2"], comp_data["B2"]]
                        card6_types = ["I", "F", "F", "I", "F", "F"]
                    else:
                        card6_fields = [comp_data["MID1"], comp_data["THICK1"], comp_data["B1"]]
                        card6_types = ["I", "F", "F"]
                    card6_line = "".join(
                        self.parser.format_field(val, typ, 10)
                        for val, typ in zip(card6_fields, card6_types)
                    )
                    file_obj.write(card6_line + "\n")

            # Card 7
            if 'Card 7' in self.cards and self.cards['Card 7'][i]:
                for comp_long_data in self.cards['Card 7'][i]:
                    if "PLYID1" in comp_long_data:
                        card7_fields = [comp_long_data["MID1"], comp_long_data["THICK1"], comp_long_data["B1"], comp_long_data["PLYID1"]]
                        card7_types = ["I", "F", "F", "I"]
                    else:
                        card7_fields = [comp_long_data["MID1"], comp_long_data["THICK1"], comp_long_data["B1"]]
                        card7_types = ["I", "F", "F"]
                    card7_line = "".join(
                        self.parser.format_field(val, typ, 10)
                        for val, typ in zip(card7_fields, card7_types)
                    )
                    file_obj.write(card7_line + "\n")
