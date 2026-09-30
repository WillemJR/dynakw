"""Implementation of the *LOAD_BODY keyword."""

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class LoadBody(LSDynaKeyword):
    """Implements the *LOAD_BODY_OPTION keyword.

    The option is mandatory and selects the cards:

    ====================================  ==========================
    OPTION                                Cards
    ====================================  ==========================
    X, Y, Z (base acceleration)           Card 1a.1
    RX, RY, RZ (angular velocity)         Card 1a.1
    VECTOR                                Card 1a.1, Card 1a.2
    PARTS                                 Card 1b
    ====================================  ==========================

    Each block holds one definition; the cards occur once.
    """

    _LOAD_OPTIONS = ("X", "Y", "Z", "RX", "RY", "RZ", "VECTOR")

    # Each option is registered as its own name rather than registering the
    # bare "*LOAD_BODY".  That prefix would also claim *LOAD_BODY_GENERALIZED
    # (and its _SET_NODE / _SET_PART variants) and *LOAD_BODY_POROUS, which
    # are separate keywords with their own layouts.
    keyword_string = "*LOAD_BODY_X"
    keyword_aliases = [f"*LOAD_BODY_{o}" for o in _LOAD_OPTIONS[1:]] + \
        ["*LOAD_BODY_PARTS"]
    exact_match = True

    description = (
        "Applies body force loads from a prescribed base acceleration (X, Y, "
        "Z), an angular velocity (RX, RY, RZ) or an acceleration along a "
        "vector (VECTOR).  The loads act on every node in the model unless "
        "*LOAD_BODY_PARTS restricts them to a part set."
    )
    manual_section = "Vol I, *LOAD_BODY"

    # SF defaults to 1.0; without this a blank SF would be written back as 0.
    blank_means_default = True

    card_schemas = [
        CardSchema("Card 1a.1", [
            CardField("LCID", "I", width=10,
                      description="Load curve ID giving the loading as a "
                                  "function of time; see *DEFINE_CURVE",
                      required=True),
            CardField("SF", "F", width=10, default=1.0,
                      description="Load curve scale factor; applies to both "
                                  "LCID and LCIDDR"),
            CardField("LCIDDR", "I", width=10,
                      description="Load curve ID used during dynamic "
                                  "relaxation; 0 applies none"),
            CardField("XC", "F", width=10, default=0.0,
                      description="x-center of rotation; for angular "
                                  "velocities only",
                      units="length"),
            CardField("YC", "F", width=10, default=0.0,
                      description="y-center of rotation; for angular "
                                  "velocities only",
                      units="length"),
            CardField("ZC", "F", width=10, default=0.0,
                      description="z-center of rotation; for angular "
                                  "velocities only",
                      units="length"),
            CardField("CID", "I", width=10,
                      description="Coordinate system the acceleration is "
                                  "given in; 0 is the global system"),
        ], write_header=True,
           condition=lambda kw: not kw.has_option("PARTS"),
           condition_doc="with the X, Y, Z, RX, RY, RZ and VECTOR options",
           description="Load curve, scale factor, center of rotation and "
                       "coordinate system."),

        CardSchema("Card 1a.2", [
            CardField("V1", "F", width=10, default=0.0,
                      description="x component of the vector; the body force "
                                  "acts opposite to it"),
            CardField("V2", "F", width=10, default=0.0,
                      description="y component of the vector"),
            CardField("V3", "F", width=10, default=0.0,
                      description="z component of the vector"),
        ], write_header=True,
           condition=lambda kw: kw.has_option("VECTOR"),
           condition_doc="only with the VECTOR option",
           description="Direction of the body force."),

        CardSchema("Card 1b", [
            CardField("PSID", "I", width=10,
                      description="Part set ID the body loads are restricted "
                                  "to", required=True),
        ], write_header=True,
           condition=lambda kw: kw.has_option("PARTS"),
           condition_doc="only with the PARTS option",
           description="Part set subjected to the body loads."),
    ]
