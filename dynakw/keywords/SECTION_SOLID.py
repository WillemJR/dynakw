"""Implementation of the *SECTION_SOLID keyword."""

import math
from typing import TextIO, List
import numpy as np

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


def _arr(value, dtype):
    """Wrap a single parsed value in a 1-element numpy array."""
    return np.array([value], dtype=dtype)


class SectionSolid(LSDynaKeyword):
    """Implements the *SECTION_SOLID keyword."""

    keyword_string = "*SECTION_SOLID"
    keyword_aliases = []

    description = (
        "Defines section properties for solid elements: the element "
        "formulation and, through options, element-free Galerkin (EFG), "
        "smoothed particle Galerkin (SPG) and cohesive parameters.  "
        "Referenced by a *PART through its SECID."
    )
    manual_section = "Vol I, *SECTION_SOLID"

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
                  description="Element formulation; 1 = constant stress solid "
                              "(default), 2 = 8 point hexahedron, "
                              "10 = tetrahedron.  See the manual for the full "
                              "list",
                  required=True),
        CardField("AET", "I", width=10,
                  description="Ambient element type; applies to ELFORM 7, 11 "
                              "and 12"),
        CardField("UNUSED4", "F", width=10, stored=False,
                  description="Unused column"),
        CardField("UNUSED5", "F", width=10, stored=False,
                  description="Unused column"),
        CardField("UNUSED6", "F", width=10, stored=False,
                  description="Unused column"),
        CardField("COHOFF", "F", width=10,
                  description="Offset of the cohesive element mid-surface; "
                              "applies to cohesive elements 20 and 22"),
        CardField("GASKETT", "F", width=10,
                  description="Gasket thickness, for converting ELFORM 19-22 "
                              "to gasket elements",
                  units="length"),
    ], write_header=True,
       description="Section ID and element formulation.")

    _CARD2A1_SCHEMA = CardSchema("Card 2a.1", [
        CardField("DX", "F", width=10,
                  description="Normalized dilation parameter in the x direction"),
        CardField("DY", "F", width=10,
                  description="Normalized dilation parameter in the y direction"),
        CardField("DZ", "F", width=10,
                  description="Normalized dilation parameter in the z direction"),
        CardField("ISPLINE", "I", width=10,
                  description="EFG kernel function, overriding *CONTROL_EFG"),
        CardField("IDILA", "I", width=10,
                  description="Normalized dilation parameter definition, "
                              "overriding *CONTROL_EFG"),
        CardField("IEBT", "I", width=10,
                  description="Essential boundary condition treatment"),
        CardField("IDIM", "I", width=10,
                  description="Domain integration method"),
        CardField("TOLDEF", "F", width=10,
                  description="Deformation tolerance activating adaptive EFG "
                              "semi-Lagrangian kernels"),
    ], write_header=True,
       condition=lambda kw: "EFG" in SectionSolid._opts(kw),
       condition_doc="only with the EFG option",
       description="Element-free Galerkin parameters.")

    _CARD2A2_SCHEMA = CardSchema("Card 2a.2", [
        CardField("IPS", "I", width=10,
                  description="Pressure smoothing flag"),
        CardField("STIME", "F", width=10,
                  description="Time to switch from stabilized EFG to the "
                              "standard EFG formulation",
                  units="time"),
        CardField("IKEN", "I", width=10,
                  description="Approximation type for the kernel"),
        CardField("SF", "I", width=10,
                  description="Failure strain condition"),
        CardField("CMID", "I", width=10,
                  description="Cohesive material ID for EFG fracture analysis"),
        CardField("IBR", "I", width=10,
                  description="Crack branching flag"),
        CardField("DS", "F", width=10,
                  description="Normalized support for computing the "
                              "displacement jump"),
        CardField("ECUT", "F", width=10,
                  description="Minimum distance from a node that a crack "
                              "surface may approach",
                  units="length"),
    ], write_header=True,
       condition=lambda kw: "EFG" in SectionSolid._opts(kw),
       condition_doc="only with the EFG option, and only when the line is "
                     "present in the file",
       description="Element-free Galerkin fracture parameters.")

    _CARD2B1_SCHEMA = CardSchema("Card 2b.1", [
        CardField("DX", "F", width=10,
                  description="Normalized support size in the x direction"),
        CardField("DY", "F", width=10,
                  description="Normalized support size in the y direction"),
        CardField("DZ", "F", width=10,
                  description="Normalized support size in the z direction"),
        CardField("ISPLINE", "I", width=10,
                  description="Type of kernel function"),
        CardField("KERNEL", "I", width=10,
                  description="Type of kernel support update scheme"),
        CardField("UNUSED6", "F", width=10, stored=False,
                  description="Unused column"),
        CardField("SMSTEP", "I", width=10,
                  description="Interval of time steps between displacement "
                              "smoothing passes"),
        CardField("MSC", "F", width=10,
                  description="Smoothing scheme for momentum consistent SPG "
                              "(ITB = 3 only)"),
    ], write_header=True,
       condition=lambda kw: "SPG" in SectionSolid._opts(kw),
       condition_doc="only with the SPG option",
       description="Smoothed particle Galerkin kernel parameters.")

    _CARD2B2_SCHEMA = CardSchema("Card 2b.2", [
        CardField("IDAM", "I", width=10,
                  description="Bond failure mechanism"),
        CardField("FS", "F", width=10,
                  description="Critical value of the quantity given by IDAM "
                              "that triggers bond failure"),
        CardField("STRETCH", "F", width=10,
                  description="Critical relative deformation (stretch or "
                              "compression ratio)"),
        CardField("ITB", "I", width=10,
                  description="Stabilization option"),
        CardField("MSFAC", "F", width=10,
                  description="Quadrature scale factor for momentum "
                              "consistent SPG (ITB = 3 only)"),
        CardField("ISC", "I", width=10,
                  description="Self-contact indicator"),
        CardField("BOXID", "I", width=10,
                  description="ID of a box defining the active SPG region"),
        CardField("PDAMP", "F", width=10,
                  description="Particle-to-particle damping coefficient"),
    ], write_header=True,
       condition=lambda kw: "SPG" in SectionSolid._opts(kw),
       condition_doc="only with the SPG option, and only when the line is "
                     "present in the file",
       description="Smoothed particle Galerkin bond failure parameters.")

    _CARD2C_SCHEMA = CardSchema("Card 2c", [
        CardField("COHTHK", "F", width=10,
                  description="Cohesive thickness, superseding the THICK value "
                              "from the material card",
                  units="length"),
    ], write_header=True,
       condition=lambda kw: "MISC" in SectionSolid._opts(kw),
       condition_doc="only with the MISC option",
       description="Cohesive element thickness.")

    _CARD3_SCHEMA = CardSchema("Card 3", [
        CardField("NIP", "I", width=10,
                  description="Number of integration points (0 if resultant)"),
        CardField("NXDOF", "I", width=10,
                  description="Number of extra degrees of freedom per node"),
        CardField("IHGF", "I", width=10,
                  description="Flag for hourglass stabilization (NIP > 0)"),
        CardField("ITAJ", "I", width=10,
                  description="Flag for the user-defined Jacobian computation"),
        CardField("LMC", "I", width=10,
                  description="Number of user-defined material constants "
                              "given on Card 5"),
        CardField("NHSV", "I", width=10,
                  description="Number of history variables"),
        CardField("XNOD", "I", width=10,
                  description="Flag for extra nodes"),
    ], write_header=True,
       condition_doc="only when ELFORM is 101-105 (user-defined element)",
       description="User-defined element parameters.")

    _CARD4_SCHEMA = CardSchema("Card 4", [
        CardField("XI", "F", width=10,
                  description="First parametric coordinate of the integration "
                              "point"),
        CardField("ETA", "F", width=10,
                  description="Second parametric coordinate of the integration "
                              "point"),
        CardField("ZETA", "F", width=10,
                  description="Third parametric coordinate of the integration "
                              "point"),
        CardField("WGT", "F", width=10,
                  description="Integration weight"),
    ], repeating=True, write_header=True,
       condition_doc="only when ELFORM is 101-105; NIP lines, one per "
                     "integration point",
       description="Integration point locations and weights.")

    _CARD5_SCHEMA = CardSchema("Card 5", [
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
        _CARD1_SCHEMA,
        _CARD2A1_SCHEMA, _CARD2A2_SCHEMA,
        _CARD2B1_SCHEMA, _CARD2B2_SCHEMA, _CARD2C_SCHEMA,
        _CARD3_SCHEMA, _CARD4_SCHEMA, _CARD5_SCHEMA,
    ]

    def _parse_raw_data(self, raw_lines: List[str]):
        card_lines = [line for line in raw_lines[1:]
                      if line.strip() and not line.startswith('$')]
        if not card_lines:
            return

        # Card 1 (always required)
        # Columns: SECID ELFORM AET [skip skip skip] COHOFF GASKETT
        # Positions 3-5 (indices 3,4,5) are unnamed/reserved — parsed but not stored.
        cols  = ["SECID", "ELFORM", "AET", None, None, None, "COHOFF", "GASKETT"]
        types = ["A",     "I",      "I",   None, None, None, "F",      "F"]
        data  = self.parser.parse_line(card_lines[0], types)

        dtypes = {"SECID": object, "ELFORM": np.int32, "AET": np.int32,
                  "COHOFF": np.float64, "GASKETT": np.float64}
        self.cards["Card 1"] = {
            col: _arr(val, dtypes[col])
            for col, val in zip(cols, data) if col
        }

        elform  = int(self.cards["Card 1"]["ELFORM"][0])
        options = [o.upper() for o in self.options]
        line_idx = 1

        # Option-based cards
        if "EFG" in options:
            if line_idx < len(card_lines):
                cols2  = ["DX", "DY", "DZ", "ISPLINE", "IDILA", "IEBT", "IDIM", "TOLDEF"]
                types2 = ["F",  "F",  "F",  "I",       "I",     "I",    "I",    "F"]
                data2  = self.parser.parse_line(card_lines[line_idx], types2)
                self.cards["Card 2a.1"] = {
                    col: _arr(v, np.int32 if t == 'I' else np.float64)
                    for col, t, v in zip(cols2, types2, data2)
                }
                line_idx += 1
            if line_idx < len(card_lines):
                cols2b  = ["IPS", "STIME", "IKEN", "SF", "CMID", "IBR", "DS", "ECUT"]
                types2b = ["I",   "F",     "I",    "I",  "I",    "I",   "F",  "F"]
                data2b  = self.parser.parse_line(card_lines[line_idx], types2b)
                if any(x is not None for x in data2b):
                    self.cards["Card 2a.2"] = {
                        col: _arr(v, np.int32 if t == 'I' else np.float64)
                        for col, t, v in zip(cols2b, types2b, data2b)
                    }
                    line_idx += 1

        elif "SPG" in options:
            if line_idx < len(card_lines):
                cols2  = ["DX", "DY", "DZ", "ISPLINE", "KERNEL", None, "SMSTEP", "MSC"]
                types2 = ["F",  "F",  "F",  "I",       "I",      None, "I",      "F"]
                data2  = self.parser.parse_line(card_lines[line_idx], types2)
                self.cards["Card 2b.1"] = {
                    col: _arr(v, np.int32 if t == 'I' else np.float64)
                    for col, t, v in zip(cols2, types2, data2) if col
                }
                line_idx += 1
            if line_idx < len(card_lines):
                cols2b  = ["IDAM", "FS", "STRETCH", "ITB", "MSFAC", "ISC", "BOXID", "PDAMP"]
                types2b = ["I",    "F",  "F",       "I",   "F",     "I",   "I",     "F"]
                data2b  = self.parser.parse_line(card_lines[line_idx], types2b)
                if any(x is not None for x in data2b):
                    self.cards["Card 2b.2"] = {
                        col: _arr(v, np.int32 if t == 'I' else np.float64)
                        for col, t, v in zip(cols2b, types2b, data2b)
                    }
                    line_idx += 1

        elif "MISC" in options and line_idx < len(card_lines):
            data2c = self.parser.parse_line(card_lines[line_idx], ["F"])
            if any(x is not None for x in data2c):
                self.cards["Card 2c"] = {"COHTHK": _arr(data2c[0], np.float64)}
                line_idx += 1

        # User-defined element cards (ELFORM 101-105)
        if elform in [101, 102, 103, 104, 105] and line_idx < len(card_lines):
            cols3  = ["NIP", "NXDOF", "IHGF", "ITAJ", "LMC", "NHSV", "XNOD"]
            types3 = ["I"] * 7
            data3  = self.parser.parse_line(card_lines[line_idx], types3 + [None])
            self.cards["Card 3"] = {
                col: _arr(v, np.int32) for col, v in zip(cols3, data3)
            }
            line_idx += 1
            nip = int(data3[0]) if data3[0] is not None else 0
            lmc = int(data3[4]) if data3[4] is not None else 0

            if nip > 0:
                card4_data = []
                for _ in range(nip):
                    if line_idx >= len(card_lines):
                        break
                    card4_data.append(
                        self.parser.parse_line(
                            card_lines[line_idx], ["F", "F", "F", "F", None, None, None, None]))
                    line_idx += 1
                if card4_data:
                    arr = np.array([[r[i] for i in range(4)] for r in card4_data],
                                   dtype=np.float64)
                    self.cards["Card 4"] = {
                        col: arr[:, i] for i, col in enumerate(["XI", "ETA", "ZETA", "WGT"])
                    }

            if lmc > 0:
                all_p = []
                for _ in range(math.ceil(lmc / 8)):
                    if line_idx >= len(card_lines):
                        break
                    all_p.extend(d for d in self.parser.parse_line(
                        card_lines[line_idx], ["F"] * 8) if d is not None)
                    line_idx += 1
                p_vals = all_p[:lmc]
                if p_vals:
                    self.cards["Card 5"] = {
                        f"P{i+1}": _arr(v, np.float64) for i, v in enumerate(p_vals)
                    }

    def write(self, file_obj: TextIO):
        file_obj.write(f"{self.full_keyword}\n")

        card1 = self.cards.get("Card 1")
        if card1 is None or len(next(iter(card1.values()), [])) == 0:
            return

        cols  = ["SECID", "ELFORM", "AET", None, None, None, "COHOFF", "GASKETT"]
        types = ["A",     "I",      "I",   None, None, None, "F",      "F"]
        file_obj.write(self.parser.format_header(cols))
        line_parts = [
            self.parser.format_field(card1.get(col, [None])[0] if col else None, t)
            for col, t in zip(cols, types)
        ]
        file_obj.write("".join(line_parts) + "\n")

        options = [o.upper() for o in self.options]

        if "EFG" in options:
            for card_name, cols2, types2 in [
                ("Card 2a.1",
                 ["DX", "DY", "DZ", "ISPLINE", "IDILA", "IEBT", "IDIM", "TOLDEF"],
                 ["F",  "F",  "F",  "I",       "I",     "I",    "I",    "F"]),
                ("Card 2a.2",
                 ["IPS", "STIME", "IKEN", "SF", "CMID", "IBR", "DS", "ECUT"],
                 ["I",   "F",     "I",    "I",  "I",    "I",   "F",  "F"]),
            ]:
                card = self.cards.get(card_name)
                if card is not None and len(next(iter(card.values()), [])) > 0:
                    file_obj.write(self.parser.format_header(cols2))
                    file_obj.write("".join(
                        self.parser.format_field(card.get(col, [None])[0], t)
                        for col, t in zip(cols2, types2)
                    ) + "\n")

        elif "SPG" in options:
            card2b1 = self.cards.get("Card 2b.1")
            if card2b1 is not None and len(next(iter(card2b1.values()), [])) > 0:
                cols2 = ["DX", "DY", "DZ", "ISPLINE", "KERNEL", None, "SMSTEP", "MSC"]
                types2 = ["F", "F", "F", "I", "I", None, "I", "F"]
                file_obj.write(self.parser.format_header(cols2))
                file_obj.write("".join(
                    self.parser.format_field(
                        card2b1.get(col, [None])[0] if col else None, t)
                    for col, t in zip(cols2, types2)
                ) + "\n")
            card2b2 = self.cards.get("Card 2b.2")
            if card2b2 is not None and len(next(iter(card2b2.values()), [])) > 0:
                cols2 = ["IDAM", "FS", "STRETCH", "ITB", "MSFAC", "ISC", "BOXID", "PDAMP"]
                types2 = ["I", "F", "F", "I", "F", "I", "I", "F"]
                file_obj.write(self.parser.format_header(cols2))
                file_obj.write("".join(
                    self.parser.format_field(card2b2.get(col, [None])[0], t)
                    for col, t in zip(cols2, types2)
                ) + "\n")

        elif "MISC" in options:
            card2c = self.cards.get("Card 2c")
            if card2c is not None and len(next(iter(card2c.values()), [])) > 0:
                cols2 = ["COHTHK", None, None, None, None, None, None, None]
                types2 = ["F", None, None, None, None, None, None, None]
                file_obj.write(self.parser.format_header(cols2))
                file_obj.write("".join(
                    self.parser.format_field(
                        card2c.get(col, [None])[0] if col else None, t)
                    for col, t in zip(cols2, types2)
                ) + "\n")

        card3 = self.cards.get("Card 3")
        if card3 is not None and len(next(iter(card3.values()), [])) > 0:
            cols3  = ["NIP", "NXDOF", "IHGF", "ITAJ", "LMC", "NHSV", "XNOD", None]
            types3 = ["I",   "I",     "I",    "I",    "I",   "I",    "I",    None]
            file_obj.write(self.parser.format_header(cols3))
            file_obj.write("".join(
                self.parser.format_field(card3.get(col, [None])[0] if col else None, t)
                for col, t in zip(cols3, types3)
            ) + "\n")

            card4 = self.cards.get("Card 4")
            if card4 is not None and len(next(iter(card4.values()), [])) > 0:
                cols4  = ["XI", "ETA", "ZETA", "WGT", None, None, None, None]
                types4 = ["F",  "F",   "F",    "F",   None, None, None, None]
                file_obj.write(self.parser.format_header(cols4))
                nrows = len(card4["XI"])
                for i in range(nrows):
                    file_obj.write("".join(
                        self.parser.format_field(
                            card4.get(col, [None] * nrows)[i] if col else None, t)
                        for col, t in zip(cols4, types4)
                    ) + "\n")

            card5 = self.cards.get("Card 5")
            if card5 is not None and len(card5) > 0:
                p_cols = sorted(card5.keys(), key=lambda k: int(k[1:]))
                all_p  = [card5[col][0] for col in p_cols]
                for i in range(0, len(all_p), 8):
                    file_obj.write(self.parser.format_header(p_cols[i:i + 8]))
                    chunk = all_p[i:i + 8] + [None] * (8 - len(all_p[i:i + 8]))
                    file_obj.write(
                        "".join(self.parser.format_field(p, "F") for p in chunk) + "\n")
