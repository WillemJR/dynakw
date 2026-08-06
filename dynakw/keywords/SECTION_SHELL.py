"""Implementation of the *SECTION_SHELL keyword."""

import math
from typing import TextIO, List
import numpy as np

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class SectionShell(LSDynaKeyword):
    """Implements the *SECTION_SHELL keyword."""

    keyword_string = "*SECTION_SHELL"

    description = (
        "Defines section properties for shell elements: the element "
        "formulation, through-thickness integration and nodal thicknesses, "
        "referenced by a *PART through its SECID."
    )
    manual_section = "Vol I, *SECTION_SHELL"

    # This class writes from `cards` alone, so a hand-built *SECTION_SHELL
    # renders correctly even though `write` is custom.  Three requirements when
    # building one, all verified by test_section_build.py:
    #
    #   * Cards 1 and 2 go through the base write helper, which indexes each
    #     declared field directly, so every field must be present.
    #   * NIP on Card 1 must equal the number of B values on Card 3.  It is NIP
    #     that decides how many angles are read back, so too few are padded
    #     with zeros rather than rejected.
    #   * Likewise NIPP and LMC on Card 5 must match the row count of Card 5.1
    #     and the number of P values on Card 5.2.
    builds_from_cards = True

    @staticmethod
    def _opts(kw) -> set:
        """The keyword's option suffixes, upper-cased."""
        return {o.upper() for o in kw.options}

    _CARD1_SCHEMA = CardSchema("Card 1", [
        CardField("SECID", "A", width=10,
                  description="Section ID referenced on the *PART card; "
                              "unique number or label",
                  required=True),
        CardField("ELFORM", "I", width=10,
                  description="Element formulation; 1 = Hughes-Liu, "
                              "2 = Belytschko-Tsay (default), "
                              "16 = fully integrated.  See the manual for the "
                              "full list",
                  required=True),
        CardField("SHRF", "F", width=10,
                  description="Shear correction factor scaling the transverse "
                              "shear stress"),
        CardField("NIP", "I", width=10,
                  description="Number of through-thickness integration points"),
        CardField("PROPT", "F", width=10,
                  description="Printout option (not active)"),
        CardField("QR/IRID", "I", width=10,
                  description="Quadrature rule, or integration rule ID; see "
                              "*INTEGRATION_SHELL"),
        CardField("ICOMP", "I", width=10,
                  description="Flag for an orthotropic/anisotropic layered "
                              "composite material model",
                  choices={0: "not a layered composite",
                           1: "layered composite; Card 3 gives the layer angles"}),
        CardField("SETYP", "I", width=10,
                  description="Not used (obsolete)"),
    ], write_header=True,
       description="Section ID, element formulation and integration rule.")

    _CARD2_SCHEMA = CardSchema("Card 2", [
        CardField("T1", "F", width=10,
                  description="Shell thickness at node 1, unless the thickness "
                              "is given on the *ELEMENT_SHELL card",
                  units="length"),
        CardField("T2", "F", width=10,
                  description="Shell thickness at node 2 (defaults to T1)",
                  units="length"),
        CardField("T3", "F", width=10,
                  description="Shell thickness at node 3 (defaults to T1)",
                  units="length"),
        CardField("T4", "F", width=10,
                  description="Shell thickness at node 4 (defaults to T1)",
                  units="length"),
        CardField("NLOC", "F", width=10,
                  description="Location of the reference surface",
                  choices={1.0: "nodes at the top surface",
                           0.0: "nodes at mid-thickness (default)",
                           -1.0: "nodes at the bottom surface"}),
        CardField("MAREA", "F", width=10,
                  description="Non-structural mass per unit area",
                  units="mass/area"),
        CardField("IDOF", "I", width=10,
                  description="Treatment of through-thickness strain"),
        CardField("EDGSET", "I", width=10,
                  description="Edge node set required for shell type seatbelts"),
    ], write_header=True,
       description="Nodal thicknesses and reference surface location.")

    _CARD3_SCHEMA = CardSchema("Card 3", [
        CardField(f"B{i}", "F", width=10,
                  description=f"Material angle at integration point {i}",
                  units="degrees")
        for i in range(1, 9)
    ], dynamic=True, write_header=True,
       condition_doc="only when ICOMP = 1 and NIP > 0 on Card 1.  NIP angles "
                     "are given, eight per line, and stored as B1…B{NIP}",
       description="Material angle at each through-thickness integration "
                   "point of a layered composite.")

    _CARD4A_SCHEMA = CardSchema("Card 4a", [
        CardField("DX", "F", width=10,
                  description="Normalized dilation parameter in the x direction"),
        CardField("DY", "F", width=10,
                  description="Normalized dilation parameter in the y direction"),
        CardField("ISPLINE", "I", width=10,
                  description="EFG kernel function, overriding *CONTROL_EFG"),
        CardField("IDILA", "I", width=10,
                  description="Normalized dilation parameter definition, "
                              "overriding *CONTROL_EFG"),
        CardField("IEBT", "I", width=10,
                  description="Essential boundary condition treatment"),
        CardField("IDIM", "I", width=10,
                  description="Domain integration method for the mesh-free "
                              "shell local approach (ELFORM 41)"),
    ], write_header=True,
       condition=lambda kw: "EFG" in SectionShell._opts(kw),
       condition_doc="only with the EFG option",
       description="Element-free Galerkin parameters.")

    _CARD4B_SCHEMA = CardSchema("Card 4b", [
        CardField("ITHELFM", "I", width=10,
                  description="Thermal shell formulation",
                  choices={0: "governed by THSHEL on *CONTROL_SHELL",
                           1: "thick thermal shell",
                           2: "thin thermal shell"}),
    ], write_header=True,
       condition=lambda kw: "THERMAL" in SectionShell._opts(kw),
       condition_doc="only with the THERMAL option",
       description="Thermal shell formulation.")

    _CARD4C_SCHEMA = CardSchema("Card 4c", [
        CardField("CMID", "I", width=10,
                  description="Cohesive material ID for the XFEM crack"),
        CardField("BASELM", "I", width=10,
                  description="Base element type for XFEM"),
        CardField("DOMINT", "I", width=10,
                  description="Domain integration option",
                  choices={0: "phantom element integration (default)",
                           1: "subdomain integration"}),
        CardField("FAILCR", "I", width=10,
                  description="Failure criterion selection"),
        CardField("PROPCR", "I", width=10,
                  description="Crack propagation option, interpreted "
                              "digit-wise"),
        CardField("FS", "F", width=10,
                  description="Failure stress or strain, per FAILCR"),
        CardField("LS/FS1", "F", width=10,
                  description="Characteristic length, or second failure value"),
        CardField("NC/CL", "F", width=10,
                  description="Number of elements ahead of the crack tip, or "
                              "crack length"),
    ], write_header=True,
       condition=lambda kw: "XFEM" in SectionShell._opts(kw),
       condition_doc="only with the XFEM option",
       description="Extended finite element (XFEM) crack parameters.")

    _CARD4D_SCHEMA = CardSchema("Card 4d", [
        CardField("THKSCL", "F", width=10,
                  description="Scale factor applied to the shell thickness"),
    ], write_header=True,
       condition=lambda kw: "MISC" in SectionShell._opts(kw),
       condition_doc="only with the MISC option",
       description="Miscellaneous section parameters.")

    _CARD5_SCHEMA = CardSchema("Card 5", [
        CardField("NIPP", "I", width=10,
                  description="Number of in-plane integration points "
                              "(0 if resultant)"),
        CardField("NXDOF", "I", width=10,
                  description="Number of extra degrees of freedom per node"),
        CardField("IUNF", "I", width=10,
                  description="Flag for the user-defined nodal force routine"),
        CardField("IHGF", "I", width=10,
                  description="Flag for hourglass stabilization"),
        CardField("ITAJ", "I", width=10,
                  description="Flag for the user-defined Jacobian computation"),
        CardField("LMC", "I", width=10,
                  description="Number of user-defined material constants "
                              "given on Card 5.2"),
        CardField("NHSV", "I", width=10,
                  description="Number of history variables"),
        CardField("ILOC", "I", width=10,
                  description="Flag for the local coordinate system"),
    ], write_header=True,
       condition_doc="only when ELFORM is 101-105 (user-defined element)",
       description="User-defined element parameters.")

    _CARD51_SCHEMA = CardSchema("Card 5.1", [
        CardField("XI", "F", width=10,
                  description="First parametric coordinate of the integration "
                              "point"),
        CardField("ETA", "F", width=10,
                  description="Second parametric coordinate of the integration "
                              "point"),
        CardField("WGT", "F", width=10,
                  description="Integration weight"),
    ], repeating=True, write_header=True,
       condition_doc="only when ELFORM is 101-105; NIPP lines, one per "
                     "in-plane integration point",
       description="Integration point locations and weights.")

    _CARD52_SCHEMA = CardSchema("Card 5.2", [
        CardField(f"P{i}", "F", width=10,
                  description=f"User-defined material constant {i}")
        for i in range(1, 9)
    ], dynamic=True, write_header=True,
       condition_doc="only when ELFORM is 101-105.  LMC constants are given, "
                     "eight per line, and stored as P1…P{LMC}",
       description="User-defined material constants.")

    # Declared for introspection only: _parse_raw_data and write are both
    # overridden, so the base class never consults this list.
    card_schemas = [
        _CARD1_SCHEMA, _CARD2_SCHEMA, _CARD3_SCHEMA,
        _CARD4A_SCHEMA, _CARD4B_SCHEMA, _CARD4C_SCHEMA, _CARD4D_SCHEMA,
        _CARD5_SCHEMA, _CARD51_SCHEMA, _CARD52_SCHEMA,
    ]

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
            # One angle per integration point.  A blank column parses as 0
            # rather than None, so the trailing blanks of the last line would
            # otherwise be stored as extra angles -- NIP = 3 would come back as
            # B1-B8, and write out five spurious zeros.  Card 5.2 below, and
            # *SECTION_SOLID, truncate the same way.
            all_b_values = all_b_values[:nip]
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
