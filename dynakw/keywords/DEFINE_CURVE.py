"""Implementation of the *DEFINE_CURVE keyword."""

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class DefineCurve(LSDynaKeyword):
    """Implements the *DEFINE_CURVE keyword.

    The point cards are written as ``2E20.0``, so their two columns are twenty
    characters wide rather than the usual ten.
    """

    keyword_string = "*DEFINE_CURVE"
    keyword_aliases = ["*DEFINE_CURVE_3858", "*DEFINE_CURVE_5434A"]

    # Every accepted name is registered above.  Without this, prefix matching
    # would also claim the many unrelated keywords that begin with
    # "*DEFINE_CURVE" -- *DEFINE_CURVE_FUNCTION, *DEFINE_CURVE_SMOOTH,
    # *DEFINE_CURVE_TRIM, *DEFINE_CURVE_ENTITY, *DEFINE_CURVE_DUPLICATE and
    # others -- all of which have their own card layouts.
    exact_match = True

    description = (
        "Defines a curve, for example a load as a function of time, given as a "
        "list of abscissa/ordinate pairs.  The 3858 and 5434A options select "
        "older rediscretization algorithms and do not change the layout."
    )
    manual_section = "Vol I, *DEFINE_CURVE"

    card_schemas = [
        CardSchema("Card 1", [
            CardField("LCID", "A", width=10,
                      description="Load curve ID; a unique number or a label "
                                  "not containing '.'",
                      required=True),
            CardField("SIDR", "I", width=10,
                      description="Controls use of the curve during dynamic "
                                  "relaxation",
                      choices={0: "normal analysis phase only",
                               1: "dynamic relaxation phase only",
                               2: "both phases"}),
            CardField("SFA", "F", width=10, default=1.0,
                      description="Scale factor for the abscissa values"),
            CardField("SFO", "F", width=10, default=1.0,
                      description="Scale factor for the ordinate values"),
            CardField("OFFA", "F", width=10,
                      description="Offset for the abscissa values"),
            CardField("OFFO", "F", width=10,
                      description="Offset for the ordinate values"),
            CardField("DATTYP", "I", width=10,
                      description="Data type, for curves whose meaning depends "
                                  "on it"),
            CardField("LCINT", "I", width=10,
                      description="Number of points the curve is "
                                  "rediscretized to; 0 uses the default"),
        ], write_header=True,
           description="Curve ID, scale factors and offsets."),

        CardSchema("Card 2", [
            CardField("A1", "F", width=20,
                      description="Abscissa value of the point"),
            CardField("O1", "F", width=20,
                      description="Ordinate value of the point"),
        ], repeating=True, write_header=True,
           description="One abscissa/ordinate pair per line, in twenty "
                       "character fields.  The number of points is however "
                       "many lines are given; the input ends at the next "
                       "keyword."),
    ]
