"""Implementation of the *MAT_RIGID keyword."""

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class MatRigid(LSDynaKeyword):
    """Implements the *MAT_RIGID keyword (material type 20).

    Card 2 has three forms in the manual -- 2a for CMO = 1.0, 2b for
    CMO = 0.0 and 2c for CMO = -1.0 -- which differ only in whether CON1 and
    CON2 carry a meaning.  All three put CMO in column 1 and leave CON1 and
    CON2 in columns 2 and 3, so one schema reads every form: when CMO is 0.0
    the two constraint columns are simply blank, and blank reads as 0.
    """

    keyword_string = "*MAT_RIGID"
    keyword_aliases = ["*MAT_020"]

    # Every accepted name is registered above.  Without this, prefix matching
    # would also claim *MAT_RIGID_DISCRETE, which is material type 220 with its
    # own card layout, not an option of this one.
    exact_match = True

    description = (
        "Rigid material (MAT_020).  Every part made from it belongs to a rigid "
        "body, one per part ID.  Optional constraints may be applied to the "
        "centre of mass, in global or local directions."
    )
    manual_section = "Vol II, *MAT_020/*MAT_RIGID"

    card_schemas = [
        CardSchema("Card 1", [
            CardField("MID", "A", width=10,
                      description="Material ID; unique number or label",
                      required=True),
            CardField("RO", "F", width=10,
                      description="Mass density",
                      units="mass/volume", required=True),
            CardField("E", "F", width=10,
                      description="Young's modulus; a reasonable value must be "
                                  "chosen for contact penalty stiffness",
                      units="stress", required=True),
            CardField("PR", "F", width=10,
                      description="Poisson's ratio; a reasonable value must be "
                                  "chosen for contact penalty stiffness",
                      required=True),
            CardField("N", "F", width=10,
                      description="MADYMO3D coupling flag"),
            CardField("COUPLE", "F", width=10,
                      description="Coupling option for VDA surfaces and for "
                                  "MADYMO/CAL3D"),
            CardField("M", "F", width=10,
                      description="MADYMO3D coupling flag"),
            CardField("ALIAS/RE", "A", width=10, header_name="alias/re",
                      description="VDA surface alias name, or the MADYMO "
                                  "external reference number.  The manual "
                                  "types this column C/F, so it holds either a "
                                  "name or a number"),
        ], write_header=True,
           description="Material properties and coupling flags."),

        CardSchema("Card 2", [
            CardField("CMO", "F", width=10,
                      description="Centre of mass constraint option",
                      choices={1.0: "constraints applied in global directions",
                               0.0: "no constraints",
                               -1.0: "constraints applied in local directions"}),
            CardField("CON1", "I", width=10,
                      description="Global translational constraint when "
                                  "CMO = 1.0, or the local coordinate system "
                                  "ID when CMO = -1.0.  Unused when CMO = 0.0"),
            CardField("CON2", "I", width=10,
                      description="Global rotational constraint when "
                                  "CMO = 1.0, or the local constraint code "
                                  "when CMO = -1.0.  Unused when CMO = 0.0"),
        ], write_header=True,
           condition_doc="always present.  The manual splits this card into "
                         "2a, 2b and 2c by the value of CMO; the three share "
                         "these columns, so they are read as one card",
           description="Centre of mass constraints."),

        CardSchema("Card 3", [
            CardField("LCO/A1", "F", width=10, header_name="lco/a1",
                      description="Local coordinate system ID for output, or "
                                  "the first component of vector a when the "
                                  "system is given as two vectors"),
            CardField("A2", "F", width=10,
                      description="Second component of vector a"),
            CardField("A3", "F", width=10,
                      description="Third component of vector a"),
            CardField("V1", "F", width=10,
                      description="First component of vector v"),
            CardField("V2", "F", width=10,
                      description="Second component of vector v"),
            CardField("V3", "F", width=10,
                      description="Third component of vector v"),
        ], write_header=True,
           condition_doc="must be present but may be left blank",
           description="Local system for output, given either as a coordinate "
                       "system ID in column 1 or as two vectors."),
    ]
