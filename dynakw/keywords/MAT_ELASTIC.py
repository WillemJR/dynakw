"""Implementation of the *MAT_ELASTIC keyword."""

from typing import List
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class MatElastic(LSDynaKeyword):
    """
    Represents a *MAT_ELASTIC keyword in an LS-DYNA input file.

    This keyword can appear as *MAT_ELASTIC or *MAT_001, with an
    optional _FLUID suffix for fluid material modeling.
    """

    keyword_string = "*MAT_ELASTIC"
    keyword_aliases = ["*MAT_001", "*MAT_ELASTIC_FLUID", "*MAT_001_FLUID"]

    # Every accepted name is registered above.  Without this, prefix matching
    # would also claim unrelated materials whose names start with
    # "*MAT_ELASTIC" -- *MAT_ELASTIC_PLASTIC_HYDRO (MAT_010),
    # *MAT_ELASTIC_PLASTIC_THERMAL (MAT_004), *MAT_ELASTIC_WITH_VISCOSITY
    # (MAT_060) -- and silently drop their extra cards.
    exact_match = True

    description = (
        "Isotropic hypoelastic material (MAT_001).  With the FLUID option the "
        "material behaves as a fluid defined by its bulk modulus, and the "
        "Young's modulus and Poisson's ratio fields are ignored."
    )
    manual_section = "Vol II, *MAT_001/*MAT_ELASTIC"

    card_schemas = [
        # Card 1 — solid variant (no _FLUID suffix)
        CardSchema("Card 1", [
            CardField("MID", "A", width=10,
                      description="Material ID; unique number or label",
                      required=True),
            CardField("RO", "F", width=10,
                      description="Mass density",
                      units="mass/volume", required=True),
            CardField("E", "F", width=10,
                      description="Young's modulus",
                      units="stress", required=True),
            CardField("PR", "F", width=10,
                      description="Poisson's ratio",
                      required=True),
            CardField("DA", "F", width=10,
                      description="Axial damping factor "
                                  "(Belytschko-Schwer beam, type 2, only)"),
            CardField("DB", "F", width=10,
                      description="Bending damping factor "
                                  "(Belytschko-Schwer beam, type 2, only)"),
            CardField("K", "F", width=10,
                      description="Bulk modulus; define for the FLUID option only",
                      units="stress"),
        ], condition=lambda kw: not kw.is_fluid, write_header=True,
           condition_doc="only without the FLUID option",
           description="Material properties for the solid (non-FLUID) variant."),

        # Card 1 — fluid variant (_FLUID suffix)
        CardSchema("Card 1", [
            CardField("MID", "A", width=10,
                      description="Material ID; unique number or label",
                      required=True),
            CardField("RO", "F", width=10,
                      description="Mass density",
                      units="mass/volume", required=True),
            CardField("K", "F", width=10,
                      description="Bulk modulus",
                      units="stress", required=True),
        ], condition=lambda kw: kw.is_fluid, write_header=True,
           condition_doc="only with the FLUID option",
           description="Material properties for the FLUID variant."),

        # Card 2 — fluid only
        CardSchema("Card 2", [
            CardField("VC", "F", width=10,
                      description="Tensor viscosity coefficient; "
                                  "values between 0.1 and 0.5 are reasonable"),
            CardField("CP", "F", width=10,
                      description="Cavitation pressure (default 1e20)",
                      units="stress"),
        ], condition=lambda kw: kw.is_fluid, write_header=True,
           condition_doc="only with the FLUID option",
           description="Viscosity and cavitation, FLUID variant only."),
    ]

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        self.is_fluid = "_FLUID" in keyword_name.upper()
        super().__init__(keyword_name, raw_lines)
