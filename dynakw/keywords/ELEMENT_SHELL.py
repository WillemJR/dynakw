"""Implementation of the *ELEMENT_SHELL keyword."""

from typing import TextIO, List, Dict, Any
import numpy as np
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword


class ElementShell(LSDynaKeyword):
    """
    Represents the *ELEMENT_SHELL keyword in an LS-DYNA keyword file.

    This class handles all variants of the *ELEMENT_SHELL keyword, including
    options like THICKNESS, BETA, MCID, OFFSET, DOF, COMPOSITE, and
    COMPOSITE_LONG.
    """
    keyword_string = "*ELEMENT_SHELL"

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        super().__init__(keyword_name, raw_lines)

    def _parse_raw_data(self, raw_lines: List[str]):
        """
        Parses the raw data for *ELEMENT_SHELL, handling various formats and options.
        """
        card_lines = [line for line in raw_lines[1:]
                      if line.strip() and not line.strip().startswith('$')]
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
            card1_fields = self.parser.parse_line(
                line, ["I"] * 10, field_len=[8] * 10)
            eid, pid, n1, n2, n3, n4, n5, n6, n7, n8 = card1_fields

            element_data["Card 1"] = {"EID": eid, "PID": pid, "N1": n1, "N2": n2,
                                      "N3": n3, "N4": n4, "N5": n5, "N6": n6, "N7": n7, "N8": n8}
            has_midside_nodes = any(
                n is not None and n > 0 for n in [n5, n6, n7, n8])

            # Card 2: Thickness/Beta/MCID
            if has_thickness or has_beta or has_mcid:
                line = card_lines[i]
                i += 1
                card2_fields = self.parser.parse_line(
                    line, ["F"] * 5, field_len=[16] * 5)
                thic1, thic2, thic3, thic4, beta_mcid = card2_fields
                element_data["Card 2"] = {
                    "THIC1": thic1, "THIC2": thic2, "THIC3": thic3, "THIC4": thic4}
                if has_beta:
                    element_data["Card 2"]["BETA"] = beta_mcid
                elif has_mcid:
                    element_data["Card 2"]["MCID"] = beta_mcid

            # Card 3: Mid-side Node Thickness
            if has_midside_nodes and has_thickness:
                line = card_lines[i]
                i += 1
                card3_fields = self.parser.parse_line(
                    line, ["F"] * 4, field_len=[16] * 4)
                thic5, thic6, thic7, thic8 = card3_fields
                element_data["Card 3"] = {
                    "THIC5": thic5, "THIC6": thic6, "THIC7": thic7, "THIC8": thic8}

            # Card 4: Offset
            if has_offset:
                line = card_lines[i]
                i += 1
                offset = self.parser.parse_line(line, ["F"], field_len=[16])
                element_data["Card 4"] = {"OFFSET": offset[0]}

            # Card 5: Scalar Node
            if has_dof:
                line = card_lines[i]
                i += 1
                ns1, ns2, ns3, ns4 = self.parser.parse_line(
                    line, ["I"] * 4, field_len=[8] * 4)
                element_data["Card 5"] = {"NS1": ns1,
                                          "NS2": ns2, "NS3": ns3, "NS4": ns4}

            # Card 6+: Composite Integration Point
            if has_composite:
                composite_data = []
                while i < len(card_lines) and not card_lines[i].strip().startswith('*'):
                    line = card_lines[i]
                    mid1, thick1, b1, mid2, thick2, b2 = self.parser.parse_line(
                        line, ["I", "F", "F", "I", "F", "F"], field_len=[10] * 6)
                    if mid2 is None or mid2 == 0:
                        composite_data.append(
                            {"MID1": mid1, "THICK1": thick1, "B1": b1})
                    else:
                        composite_data.append(
                            {"MID1": mid1, "THICK1": thick1, "B1": b1, "MID2": mid2, "THICK2": thick2, "B2": b2})
                    i += 1
                element_data["Card 6"] = composite_data

            # Card 7+: Composite Long Integration Point
            if has_composite_long:
                composite_long_data = []
                while i < len(card_lines) and not card_lines[i].strip().startswith('*'):
                    line = card_lines[i]
                    mid1, thick1, b1, plyid1 = self.parser.parse_line(
                        line, ["I", "F", "F", "I"], field_len=[10] * 4)
                    if plyid1 is None or plyid1 == 0:
                        composite_long_data.append(
                            {"MID1": mid1, "THICK1": thick1, "B1": b1})
                    else:
                        composite_long_data.append(
                            {"MID1": mid1, "THICK1": thick1, "B1": b1, "PLYID1": plyid1})
                    i += 1
                element_data["Card 7"] = composite_long_data

            parsed_elements.append(element_data)

        if not parsed_elements:
            return

        # Convert to the new nested dictionary structure with numpy arrays
        self._convert_to_numpy_structure(parsed_elements)

    def _convert_to_numpy_structure(self, parsed_elements: List[Dict[str, Any]]):
        """
        Converts the parsed elements to the new nested dictionary structure with numpy arrays.
        """
        # Initialize the cards dictionary
        self.cards = {}

        # Get all card keys that exist in any element
        all_card_keys = set()
        for elem in parsed_elements:
            all_card_keys.update(elem.keys())

        # Process each card type
        for card_key in sorted(all_card_keys):
            self.cards[card_key] = {}

            # Handle composite cards differently as they contain lists
            if card_key in ["Card 6", "Card 7"]:
                self._process_composite_cards(parsed_elements, card_key)
            else:
                # Get all field keys for this card type
                field_keys = set()
                for elem in parsed_elements:
                    if card_key in elem and elem[card_key] is not None:
                        field_keys.update(elem[card_key].keys())

                # Create numpy arrays for each field
                for field_key in sorted(field_keys):
                    values = []

                    # Determine appropriate dtype and default value based on field name
                    if field_key in ["EID", "PID", "N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8",
                                     "NS1", "NS2", "NS3", "NS4", "MCID"]:
                        dtype = np.int32
                        default_value = 0
                    else:
                        dtype = np.float64
                        default_value = 0.0

                    for elem in parsed_elements:
                        if card_key in elem and elem[card_key] is not None:
                            value = elem[card_key].get(
                                field_key, default_value)
                            # Convert None to default value
                            if value is None:
                                value = default_value
                            values.append(value)
                        else:
                            values.append(default_value)

                    self.cards[card_key][field_key] = np.array(
                        values, dtype=dtype)

    def _process_composite_cards(self, parsed_elements: List[Dict[str, Any]], card_key: str):
        """
        Process composite cards (Card 6 and Card 7) which contain lists of integration points.
        """
        # For composite cards, we need to handle the nested structure differently
        # We'll store each integration point as a separate entry

        max_layers = 0
        # Find the maximum number of layers across all elements
        for elem in parsed_elements:
            if card_key in elem and elem[card_key] is not None:
                max_layers = max(max_layers, len(elem[card_key]))

        if max_layers == 0:
            return

        # Get all possible field keys from composite data
        field_keys = set()
        for elem in parsed_elements:
            if card_key in elem and elem[card_key] is not None:
                for comp_data in elem[card_key]:
                    field_keys.update(comp_data.keys())

        # Create arrays for each layer and field combination
        for layer_idx in range(max_layers):
            layer_key = f"Layer_{layer_idx + 1}"
            self.cards[card_key][layer_key] = {}

            for field_key in sorted(field_keys):
                values = []

                # Determine appropriate dtype and default value
                if field_key in ["MID1", "MID2", "PLYID1"]:
                    dtype = np.int32
                    default_value = 0
                else:
                    dtype = np.float64
                    default_value = 0.0

                for elem in parsed_elements:
                    if (card_key in elem and elem[card_key] is not None
                        and layer_idx < len(elem[card_key])
                            and field_key in elem[card_key][layer_idx]):
                        value = elem[card_key][layer_idx][field_key]
                        # Convert None to default value
                        if value is None:
                            value = default_value
                        values.append(value)
                    else:
                        values.append(default_value)

                self.cards[card_key][layer_key][field_key] = np.array(
                    values, dtype=dtype)

    def write(self, file_obj: TextIO):
        """Writes the keyword and its data to a file object."""
        file_obj.write(self.full_keyword + "\n")

        # Determine which optional cards are present
        opts = [o.upper() for o in self.options]
        has_thickness = "THICKNESS" in opts
        has_beta = "BETA" in opts
        has_mcid = "MCID" in opts
        has_offset = "OFFSET" in opts
        has_dof = "DOF" in opts
        has_composite = "COMPOSITE" in opts
        has_composite_long = "COMPOSITE_LONG" in opts

        # Write card headings
        card1_header = "$#" + \
            "".join([f"{name:>8}" for name in ["eid", "pid", "n1",
                    "n2", "n3", "n4", "n5", "n6", "n7", "n8"]])
        file_obj.write(card1_header + "\n")

        if has_thickness or has_beta or has_mcid:
            card2_fields = ["thic1", "thic2", "thic3", "thic4"]
            if has_beta:
                card2_fields.append("beta")
            elif has_mcid:
                card2_fields.append("mcid")
            else:
                card2_fields.append("")  # placeholder
            card2_header = "$#" + \
                "".join([f"{name:>16}" for name in card2_fields])
            file_obj.write(card2_header + "\n")

        has_midside_nodes = 'Card 3' in self.cards
        if has_midside_nodes and has_thickness:
            card3_header = "$#" + \
                "".join([f"{name:>16}" for name in [
                        "thic5", "thic6", "thic7", "thic8"]])
            file_obj.write(card3_header + "\n")

        if has_offset:
            file_obj.write("$#" + f"{'offset':>16}\n")

        if has_dof:
            card5_header = "$#" + \
                "".join([f"{name:>8}" for name in [
                        "ns1", "ns2", "ns3", "ns4"]])
            file_obj.write(card5_header + "\n")

        if has_composite:
            card6_header = "$#" + \
                "".join([f"{name:>10}" for name in [
                        "mid1", "thick1", "b1", "mid2", "thick2", "b2"]])
            file_obj.write(card6_header + "\n")

        if has_composite_long:
            card7_header = "$#" + \
                "".join([f"{name:>10}" for name in [
                        "mid1", "thick1", "b1", "plyid1"]])
            file_obj.write(card7_header + "\n")

        if 'Card 1' not in self.cards:
            return

        num_elements = len(self.cards['Card 1']['EID'])

        for i in range(num_elements):
            # Card 1
            card1_fields = []
            for field in ["EID", "PID", "N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8"]:
                if field in self.cards['Card 1']:
                    card1_fields.append(self.cards['Card 1'][field][i])
                else:
                    card1_fields.append(0)

            card1_types = ['I'] * 10
            # breakpoint()
            card1_line = "".join(
                self.parser.format_field(val, typ, field_len=8)
                for val, typ in zip(card1_fields, card1_types)
            )
            file_obj.write(card1_line + "\n")

            # Card 2
            if 'Card 2' in self.cards:
                card2_fields = []
                for field in ["THIC1", "THIC2", "THIC3", "THIC4"]:
                    if field in self.cards['Card 2']:
                        card2_fields.append(self.cards['Card 2'][field][i])
                    else:
                        card2_fields.append(0.0)

                # Add BETA or MCID
                if "BETA" in self.cards['Card 2']:
                    card2_fields.append(self.cards['Card 2']["BETA"][i])
                elif "MCID" in self.cards['Card 2']:
                    card2_fields.append(self.cards['Card 2']["MCID"][i])
                else:
                    card2_fields.append(0.0)

                card2_types = ['F'] * 5
                card2_line = "".join(
                    self.parser.format_field(val, typ, field_len=16)
                    for val, typ in zip(card2_fields, card2_types)
                )
                file_obj.write(card2_line + "\n")

            # Card 3
            if 'Card 3' in self.cards:
                card3_fields = []
                for field in ["THIC5", "THIC6", "THIC7", "THIC8"]:
                    if field in self.cards['Card 3']:
                        card3_fields.append(self.cards['Card 3'][field][i])
                    else:
                        card3_fields.append(0.0)

                card3_types = ['F'] * 4
                card3_line = "".join(
                    self.parser.format_field(val, typ, field_len=16)
                    for val, typ in zip(card3_fields, card3_types)
                )
                file_obj.write(card3_line + "\n")

            # Card 4
            if 'Card 4' in self.cards and 'OFFSET' in self.cards['Card 4']:
                card4_line = self.parser.format_field(
                    self.cards['Card 4']['OFFSET'][i], 'F', field_len=16)
                file_obj.write(card4_line + "\n")

            # Card 5
            if 'Card 5' in self.cards:
                card5_fields = []
                for field in ["NS1", "NS2", "NS3", "NS4"]:
                    if field in self.cards['Card 5']:
                        card5_fields.append(self.cards['Card 5'][field][i])
                    else:
                        card5_fields.append(0)

                card5_types = ['I'] * 4
                card5_line = "".join(
                    self.parser.format_field(val, typ, field_len=8)
                    for val, typ in zip(card5_fields, card5_types)
                )
                file_obj.write(card5_line + "\n")

            # Card 6 (Composite)
            if 'Card 6' in self.cards:
                layer_keys = [
                    k for k in self.cards['Card 6'].keys() if k.startswith('Layer_')]
                for layer_key in sorted(layer_keys):
                    layer_data = self.cards['Card 6'][layer_key]

                    # Check if this element has data for this layer
                    has_data = False
                    for field in layer_data:
                        if layer_data[field][i] != 0:
                            has_data = True
                            break

                    if has_data:
                        card6_fields = []
                        card6_types = []

                        # Always include MID1, THICK1, B1
                        for field, dtype in [("MID1", "I"), ("THICK1", "F"), ("B1", "F")]:
                            if field in layer_data:
                                card6_fields.append(layer_data[field][i])
                                card6_types.append(dtype)

                        # Include MID2, THICK2, B2 if MID2 is present and non-zero
                        if "MID2" in layer_data and layer_data["MID2"][i] != 0:
                            for field, dtype in [("MID2", "I"), ("THICK2", "F"), ("B2", "F")]:
                                if field in layer_data:
                                    card6_fields.append(layer_data[field][i])
                                    card6_types.append(dtype)

                        card6_line = "".join(
                            self.parser.format_field(val, typ)
                            for val, typ in zip(card6_fields, card6_types)
                        )
                        file_obj.write(card6_line + "\n")

            # Card 7 (Composite Long)
            if 'Card 7' in self.cards:
                layer_keys = [
                    k for k in self.cards['Card 7'].keys() if k.startswith('Layer_')]
                for layer_key in sorted(layer_keys):
                    layer_data = self.cards['Card 7'][layer_key]

                    # Check if this element has data for this layer
                    has_data = False
                    for field in layer_data:
                        if layer_data[field][i] != 0:
                            has_data = True
                            break

                    if has_data:
                        card7_fields = []
                        card7_types = []

                        # Always include MID1, THICK1, B1
                        for field, dtype in [("MID1", "I"), ("THICK1", "F"), ("B1", "F")]:
                            if field in layer_data:
                                card7_fields.append(layer_data[field][i])
                                card7_types.append(dtype)

                        # Include PLYID1 if present and non-zero
                        if "PLYID1" in layer_data and layer_data["PLYID1"][i] != 0:
                            card7_fields.append(layer_data["PLYID1"][i])
                            card7_types.append("I")

                        card7_line = "".join(
                            self.parser.format_field(val, typ)
                            for val, typ in zip(card7_fields, card7_types)
                        )
                        file_obj.write(card7_line + "\n")
