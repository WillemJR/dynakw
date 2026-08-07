"""Implementation of the *CONSTRAINED_JOINT keyword."""

from typing import List

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class ConstrainedJoint(LSDynaKeyword):
    """Implements the *CONSTRAINED_JOINT_TYPE family of keywords.

    The keyword is written as ``*CONSTRAINED_JOINT_TYPE_{OPTION}…`` where TYPE
    is one of fourteen joint variants and the options ID, LOCAL and FAILURE may
    follow in any order.  All fourteen types share one set of cards; TYPE only
    decides whether Card 2 is present.

    Four of the type names contain an underscore (TRANSLATIONAL_MOTOR,
    ROTATIONAL_MOTOR, RACK_AND_PINION, CONSTANT_VELOCITY) and the options may
    be interleaved after them, so the type cannot be taken as the first token
    of the suffix.  It is matched against the whole name instead, longest name
    first, so that TRANSLATIONAL_MOTOR is not read as TRANSLATIONAL.
    """

    # Longest first, so a type that contains another is matched first.
    _JOINT_TYPES = (
        "TRANSLATIONAL_MOTOR",
        "ROTATIONAL_MOTOR",
        "RACK_AND_PINION",
        "CONSTANT_VELOCITY",
        "TRANSLATIONAL",
        "CYLINDRICAL",
        "UNIVERSAL",
        "SPHERICAL",
        "REVOLUTE",
        "LOCKING",
        "PLANAR",
        "PULLEY",
        "GEARS",
        "SCREW",
    )

    # Joint types that carry the rotational properties card.
    _CARD2_TYPES = frozenset({
        "TRANSLATIONAL_MOTOR", "ROTATIONAL_MOTOR", "GEARS",
        "RACK_AND_PINION", "PULLEY", "SCREW",
    })

    # Each type is registered as its own name rather than registering the bare
    # "*CONSTRAINED_JOINT".  That prefix would also claim
    # *CONSTRAINED_JOINT_COOR, *CONSTRAINED_JOINT_STIFFNESS and
    # *CONSTRAINED_JOINT_USER_FORCE, which are separate keywords with their own
    # layouts.  A trailing option suffix still resolves by longest prefix, so
    # *CONSTRAINED_JOINT_SPHERICAL_ID reaches this class.
    keyword_string = "*CONSTRAINED_JOINT_SPHERICAL"
    keyword_aliases = [f"*CONSTRAINED_JOINT_{t}"
                       for t in _JOINT_TYPES if t != "SPHERICAL"]

    description = (
        "Defines a joint between two rigid bodies.  The joint variant is given "
        "by the keyword name -- spherical, revolute, cylindrical, planar, "
        "universal, translational, locking, the two motors, gears, rack and "
        "pinion, constant velocity, pulley or screw."
    )
    manual_section = "Vol I, *CONSTRAINED_JOINT"

    card_schemas = [
        CardSchema("Card ID", [
            CardField("JID", "I", width=10,
                      description="Joint ID; must be unique", required=True),
            CardField("HEADING", "A", width=70,
                      description="Joint descriptor"),
        ], write_header=True,
           condition=lambda kw: kw.has_option("ID"),
           condition_doc="only with the ID option",
           description="Joint ID and heading."),

        CardSchema("Card 1", [
            CardField("N1", "I", width=10,
                      description="Node 1, in rigid body A"),
            CardField("N2", "I", width=10,
                      description="Node 2, in rigid body B"),
            CardField("N3", "I", width=10,
                      description="Node 3, in rigid body A"),
            CardField("N4", "I", width=10,
                      description="Node 4, in rigid body B"),
            CardField("N5", "I", width=10,
                      description="Node 5, in rigid body A"),
            CardField("N6", "I", width=10,
                      description="Node 6, in rigid body B"),
            CardField("RPS", "F", width=10, default=1.0,
                      description="Relative penalty stiffness"),
            CardField("DAMP", "F", width=10, default=1.0,
                      description="Damping scale factor on the default "
                                  "damping value"),
        ], write_header=True,
           description="The nodes defining the joint.  Which of the six are "
                       "used depends on the joint type; the rest stay zero."),

        CardSchema("Card 2", [
            CardField("PARM", "F", width=10,
                      description="Parameter whose meaning depends on the "
                                  "joint type: a gear or pulley ratio, a rack "
                                  "and pinion pitch, or a screw pitch"),
            CardField("LCID", "I", width=10,
                      description="Load curve ID; see *DEFINE_CURVE"),
            CardField("TYPE", "I", width=10,
                      description="Motor type, for the motor joints",
                      choices={0: "translational or rotational velocity",
                               1: "displacement or angle",
                               2: "force or moment"}),
            CardField("R1", "F", width=10,
                      description="Optional maximum resisting force or moment"),
            CardField("H_ANGLE", "F", width=10,
                      description="Hinge angle in degrees, for the screw joint",
                      units="degrees"),
        ], write_header=True,
           condition=lambda kw: kw.joint_type in ConstrainedJoint._CARD2_TYPES,
           condition_doc="only for the TRANSLATIONAL_MOTOR, ROTATIONAL_MOTOR, "
                         "GEARS, RACK_AND_PINION, PULLEY and SCREW joint types",
           description="Rotational properties of the driven joint types."),

        CardSchema("Card 3", [
            CardField("RAID", "I", width=10,
                      description="Rigid body or accelerometer ID whose local "
                                  "system the force resultants are output in"),
            CardField("LST", "I", width=10,
                      description="Local system type",
                      choices={0: "rigid body", 1: "accelerometer"}),
        ], write_header=True,
           condition=lambda kw: kw.has_option("LOCAL"),
           condition_doc="only with the LOCAL option",
           description="Local system for the force output."),

        CardSchema("Card 4", [
            CardField("CID", "I", width=10,
                      description="Coordinate ID for the failure resultants; "
                                  "0 is the global system"),
            CardField("TFAIL", "F", width=10,
                      description="Time of joint failure; 0 never fails",
                      units="time"),
            CardField("COUPL", "F", width=10,
                      description="Coupling between the force and moment "
                                  "failure criteria"),
        ], write_header=True,
           condition=lambda kw: kw.has_option("FAILURE"),
           condition_doc="only with the FAILURE option",
           description="Failure coordinate system and time."),

        CardSchema("Card 5", [
            CardField("NXX", "F", width=10,
                      description="Axial force resultant at failure"),
            CardField("NYY", "F", width=10,
                      description="Local y force resultant at failure"),
            CardField("NZZ", "F", width=10,
                      description="Local z force resultant at failure"),
            CardField("MXX", "F", width=10,
                      description="Torsional moment resultant at failure"),
            CardField("MYY", "F", width=10,
                      description="Local y moment resultant at failure"),
            CardField("MZZ", "F", width=10,
                      description="Local z moment resultant at failure"),
        ], write_header=True,
           condition=lambda kw: kw.has_option("FAILURE"),
           condition_doc="only with the FAILURE option",
           description="Force and moment resultants at which the joint fails."),
    ]

    def __init__(self, keyword_name: str, raw_lines: List[str] = None,
                 start_line: int = None):
        # Set before super().__init__ — the Card 2 condition is evaluated while
        # the raw data is parsed.
        self.joint_type = self._parse_joint_type(keyword_name)
        super().__init__(keyword_name, raw_lines, start_line)

    @classmethod
    def _parse_joint_type(cls, keyword_name: str) -> str:
        """The joint variant named by *keyword_name*, or '' if there is none.

        Matched against the whole name rather than against a single option
        token, because four of the type names contain an underscore.  The names
        are tried longest first so that TRANSLATIONAL_MOTOR is not reported as
        TRANSLATIONAL.
        """
        suffix = keyword_name.strip().upper()
        for joint_type in cls._JOINT_TYPES:
            if f"_{joint_type}" in suffix:
                return joint_type
        return ""
