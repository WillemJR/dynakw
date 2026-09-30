"""Implementation of the *CONTACT_AUTOMATIC_SURFACE_TO_SURFACE keyword."""

import logging
import math
from itertools import product
from typing import List, TextIO

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema
from dynakw.core.parameter_ref import ParameterRef


logger = logging.getLogger(__name__)

_NAME = "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE"


def _names() -> List[str]:
    """Every accepted keyword name, options in the manual's order.

    The name is ``_NAME{_OPTION2}{_ID}{_MPP}{_ORTHO_FRICTION}``; OPTION4 (the
    offsets) applies only to tied contact types.
    """
    return [_NAME + "".join(parts) for parts in product(
        ("", "_THERMAL", "_THERMAL_FRICTION"),
        ("", "_ID"),
        ("", "_MPP"),
        ("", "_ORTHO_FRICTION"),
    )]


def _f(name, type_, description, default=0, **kwargs) -> CardField:
    if type_ == "F" and default == 0:
        default = 0.0
    return CardField(name, type_, width=10, default=default,
                     description=description, **kwargs)


def _unused(name) -> CardField:
    return CardField(name, "A", width=10, default=None, stored=False,
                     header_name="", description="Unused column")


def _ortho(sb: bool, n: int) -> CardSchema:
    """One of the four ORTHO_FRICTION cards: surface A or B, direction n."""
    side, surf = ("SB", "SURFB") if sb else ("SA", "SURFA")
    fields = [
        _f(f"FS{n}_{side}", "F",
           f"Static friction coefficient in local direction {n}, {surf}"),
        _f(f"FD{n}_{side}", "F",
           f"Dynamic friction coefficient in local direction {n}, {surf}"),
        _f(f"DC{n}_{side}", "F",
           f"Exponential decay coefficient in local direction {n}, {surf}"),
        _f(f"VC{n}_{side}", "F",
           f"Viscous friction coefficient in local direction {n}, {surf}"),
        _f(f"LC{n}_{side}", "I",
           f"Table ID giving the friction coefficient in local direction {n} "
           f"as a function of relative velocity and pressure, {surf}"),
    ]
    if n == 1:
        fields += [
            _f(f"OACS_{side}", "I",
               f"Whether friction directions follow the segment's local "
               f"directions (0) or an alternative system (1), {surf}"),
            _f(f"LCF{side}", "I",
               f"Load curve of friction coefficient against direction of "
               f"relative motion in degrees, {surf}"),
            _f(f"LCP{side}", "I",
               f"Load curve of friction scale factor against interface "
               f"pressure, {surf}; used only with LCF{side}"),
        ]
    number = (2 if sb else 0) + n
    return CardSchema(f"ORFR {number}", fields, write_header=True,
                      condition=lambda kw: kw.has_option("ORTHO_FRICTION"),
                      condition_doc="only with the ORTHO_FRICTION option",
                      description=f"Orthotropic friction for {surf}, "
                                  f"direction {n}.")


def _optional(letter: str, fields: List[CardField], description: str) -> CardSchema:
    earlier = "ABCDEF"[:"ABCDEF".index(letter)]
    rule = ("optional" if not earlier else
            f"optional; only when Optional Card{'s' if len(earlier) > 1 else ''} "
            f"{', '.join(earlier)} {'are' if len(earlier) > 1 else 'is'} "
            f"present, possibly as blank lines")
    return CardSchema(f"Card {letter}", fields, write_header=True,
                      condition_doc=rule, description=description)


class ContactAutomaticSurfaceToSurface(LSDynaKeyword):
    """Implements the *CONTACT_AUTOMATIC_SURFACE_TO_SURFACE keyword.

    AUTOMATIC_SURFACE_TO_SURFACE is one value of OPTION1 on
    *CONTACT_OPTION1_{OPTION2}_{OPTION3}_{OPTION4}_{OPTION5}_{OPTION6}.  The
    options add cards to a fixed sequence:

    ================  ================================================
    Card ID           ID option
    MPP 1, MPP 2      MPP option; MPP 2 only if its line starts with '&'
    Card 1, 2, 3      always
    THRM 1            THERMAL or THERMAL_FRICTION option
    THRM 2, THRM 2.1  THERMAL_FRICTION option; THRM 2.1 when FORMULA < 0
    ORFR 1 - 4        ORTHO_FRICTION option
    Card A - F        optional, positional
    ================  ================================================

    The optional cards are positional: each may be present only if every one
    before it is, and any of them may be a blank line meaning all defaults.
    """

    # Every accepted name is registered rather than the bare stem.  The stem
    # is a prefix of other contact types with other layouts --- _SMOOTH,
    # _MORTAR, _TIEBREAK, _TIEBREAK_USER, _TIED_WELD, _COMPOSITE and
    # _LUBRICATION, several of which add a Card 4 --- and a prefix match would
    # read those as this keyword.
    keyword_string = _NAME
    keyword_aliases = _names()[1:]
    exact_match = True

    description = (
        "Two-way (symmetric) automatic penalty contact between surface A and "
        "surface B.  Penetration is checked in both directions and on both "
        "sides of shells."
    )
    manual_section = "Vol I, *CONTACT"

    # Several fields have a non-zero default, and for some an explicit 0 is
    # not the default: INITITR = 0 means no iterations, IGAP = 0 is not
    # IGAP = 1.  Fields whose default depends on the contact type or the
    # SOFT option (BSORT, DEPTH, MAXPAR, PENMAX) are declared with 0 so that
    # LS-DYNA still chooses.
    blank_means_default = True

    _CARD_ID = CardSchema("Card ID", [
        CardField("CID", "I", width=10,
                  description="Contact interface ID; must be unique",
                  required=True),
        CardField("HEADING", "A", width=70, default="",
                  description="Interface descriptor"),
    ], write_header=True,
       condition=lambda kw: kw.has_option("ID"),
       condition_doc="only with the ID option",
       description="Contact interface ID and heading.")

    _MPP_1 = CardSchema("MPP 1", [
        _f("IGNORE", "I", "Set to 1 to track initial penetrations",
           choices={0: "off", 1: "on"}),
        _f("BCKT", "I", "Bucket sort frequency", default=200),
        _f("LCBCKT", "I", "Load curve for the bucket sort frequency"),
        _f("NS2TRK", "I", "Number of potential contacts tracked per tracked "
                          "node", default=3),
        _f("INITITR", "I", "Iterations to eliminate initial penetrations; an "
                           "explicit 0 means none", default=2),
        _f("PARMAX", "F", "Parametric extension distance of contact segments",
           default=1.0005),
        _unused("UNUSED7"),
        _f("CPARM8", "I", "Beam contact flags for AUTOMATIC_GENERAL contact"),
    ], write_header=True,
       condition=lambda kw: kw.has_option("MPP"),
       condition_doc="only with the MPP option",
       description="MPP contact settings.")

    _MPP_2 = CardSchema("MPP 2", [
        CardField("AMP", "A", width=10, default=None, stored=False,
                  header_name="&",
                  description="An ampersand in the first column marks the "
                              "card; it carries no value"),
        _f("CHKSEGS", "I", "Nonzero removes inverted segments from contact at "
                           "time 0"),
        _f("PENSF", "F", "Scale factor on the IGNORE penetration distance",
           default=1.0),
        _f("GRPABLE", "I", "Set to 1 for the groupable MPP communication "
                           "algorithm", choices={0: "off", 1: "on"}),
    ], write_header=True,
       condition=lambda kw: kw.has_option("MPP"),
       condition_doc="only with the MPP option, and only when the line after "
                     "MPP 1 starts with an ampersand",
       description="Further MPP contact settings.")

    _CARD_1 = CardSchema("Card 1", [
        _f("SURFA", "I", "Surface A: segment set, node set, part set, part, "
                         "shell set or branch ID, per SURFATYP", required=True),
        _f("SURFB", "I", "Surface B: segment set, part set, part, shell set or "
                         "branch ID, per SURFBTYP", required=True),
        _f("SURFATYP", "I", "ID type of SURFA", required=True,
           choices={0: "segment set", 1: "shell element set", 2: "part set",
                    3: "part", 4: "node set", 5: "include all",
                    6: "part set of exempted parts", 7: "branch ID"}),
        _f("SURFBTYP", "I", "ID type of SURFB", required=True,
           choices={0: "segment set", 1: "shell element set", 2: "part set",
                    3: "part", 5: "include all",
                    6: "part set of exempted parts", 7: "branch ID"}),
        _f("SABOXID", "I", "Box ID limiting SURFA; negative for a contact "
                           "volume ID"),
        _f("SBBOXID", "I", "Box ID limiting SURFB; negative for a contact "
                           "volume ID"),
        _f("SAPR", "I", "Include SURFA in the interface force files",
           choices={0: "no", 1: "yes", 2: "yes, and wear to dynain"}),
        _f("SBPR", "I", "Include SURFB in the interface force files",
           choices={0: "no", 1: "yes", 2: "yes, and wear to dynain"}),
    ], write_header=True,
       description="The two surfaces of the contact interface.")

    _CARD_2 = CardSchema("Card 2", [
        _f("FS", "F", "Static coefficient of friction; -1, 2 and -2 select "
                      "part-based friction or a friction table"),
        _f("FD", "F", "Dynamic coefficient of friction, or a table ID for "
                      "some values of FS"),
        _f("DC", "F", "Exponential decay coefficient"),
        _f("VC", "F", "Coefficient for viscous friction", units="stress"),
        _f("VDC", "F", "Viscous damping coefficient in percent of critical"),
        _f("PENCHK", "I", "Small penetration in contact search option"),
        _f("BT", "F", "Birth time; a curve or table ID when DT = -9999",
           units="time"),
        _f("DT", "F", "Death time; 0 means 1e20", default=1.0e20,
           units="time"),
    ], write_header=True,
       description="Friction, damping, birth and death time.")

    _CARD_3 = CardSchema("Card 3", [
        _f("SFSA", "F", "Scale factor on the SURFA penalty stiffness",
           default=1.0),
        _f("SFSB", "F", "Scale factor on the SURFB penalty stiffness",
           default=1.0),
        _f("SAST", "F", "Contact thickness for SURFA; 0 uses the element "
                        "thickness", units="length"),
        _f("SBST", "F", "Contact thickness for SURFB; 0 uses the element "
                        "thickness", units="length"),
        _f("SFSAT", "F", "Scale factor on the SURFA contact thickness",
           default=1.0),
        _f("SFSBT", "F", "Scale factor on the SURFB contact thickness",
           default=1.0),
        _f("FSF", "F", "Coulomb friction scale factor", default=1.0),
        _f("VSF", "F", "Viscous friction scale factor", default=1.0),
    ], write_header=True,
       description="Stiffness, thickness and friction scale factors.")

    _THRM_1 = CardSchema("THRM 1", [
        _f("K", "F", "Thermal conductivity of the fluid between the contact "
                     "surfaces", required=True),
        _f("FRAD", "F", "Radiation factor between the contact surfaces",
           required=True),
        _f("H0", "F", "Heat transfer conductance for closed gaps",
           required=True),
        _f("LMIN", "F", "Minimum gap; H0 is used below it", units="length",
           required=True),
        _f("LMAX", "F", "No thermal contact for gaps greater than this",
           units="length", required=True),
        _f("FTOSA", "F", "Fraction of sliding friction energy given to SURFA",
           default=0.5),
        _f("BC_FLG", "I", "Thermal boundary condition flag"),
        _f("ALGO", "I", "Thermal contact algorithm type; 0 is two-way"),
    ], write_header=True,
       condition=lambda kw: kw.has_option("THERMAL"),
       condition_doc="only with the THERMAL or THERMAL_FRICTION option",
       description="Thermal contact properties.")

    _THRM_2 = CardSchema("THRM 2", [
        _f("LCFST", "I", "Load curve scaling FS as a function of temperature"),
        _f("LCFDT", "I", "Load curve scaling FD as a function of temperature"),
        _f("FORMULA", "I", "Formula for the contact heat conductance; "
                           "negative selects a user subroutine with |FORMULA| "
                           "parameters on THRM 2.1"),
        _f("A", "I", "Load curve for coefficient a of the formula"),
        _f("B", "I", "Load curve for coefficient b of the formula"),
        _f("C", "I", "Load curve for coefficient c of the formula"),
        _f("D", "I", "Load curve for coefficient d of the formula"),
        _f("LCH", "I", "Curve or function ID for the heat transfer "
                       "coefficient; takes precedence when defined"),
    ], write_header=True,
       condition=lambda kw: kw.has_option("THERMAL_FRICTION"),
       condition_doc="only with the THERMAL_FRICTION option",
       description="Temperature-dependent friction and heat conductance.")

    _THRM_2_1 = CardSchema("THRM 2.1", [
        _f(f"UC{i}", "F", f"User parameter {i} of the line") for i in range(1, 9)
    ], repeating=True, dynamic=True, write_header=True,
       condition_doc="only with the THERMAL_FRICTION option and FORMULA < 0 "
                     "on THRM 2; |FORMULA| parameters, eight per line.  Row r "
                     "holds parameters 8r+1 to 8r+8",
       description="User subroutine parameters for the heat conductance.")

    _ORFR = [_ortho(False, 1), _ortho(False, 2),
             _ortho(True, 1), _ortho(True, 2)]

    _OPTIONAL = [
        _optional("A", [
            _f("SOFT", "I", "Contact formulation; 0 standard penalty, 1 soft "
                            "constraint, 2 segment-based.  See the manual for "
                            "others"),
            _f("SOFSCL", "F", "Scale factor for the SOFT = 1 constraint "
                              "forces", default=0.1),
            _f("LCIDAB", "I", "Load curve of airbag thickness; airbag contact "
                              "only"),
            _f("MAXPAR", "F", "Maximum parametric coordinate in segment "
                              "search; 0 uses the type's default"),
            _f("SBOPT", "I", "Segment-based (SOFT = 2) contact options",
               default=2),
            _f("DEPTH", "I", "Search depth for nodal penetration; 0 uses the "
                             "default"),
            _f("BSORT", "I", "Cycles between bucket sorts; 0 lets LS-DYNA "
                             "choose"),
            _f("FRCFRQ", "I", "Cycles between contact force updates",
               default=1),
        ], "Contact formulation and search parameters."),
        _optional("B", [
            _f("PENMAX", "F", "Maximum penetration distance; 0 uses the "
                              "type's default", units="length"),
            _f("THKOPT", "I", "Thickness option"),
            _f("SHLTHK", "I", "Whether shell thickness offsets are considered; "
                              "only with THKOPT = 1"),
            _f("SNLOG", "I", "Disables the shooting node logic"),
            _f("ISYM", "I", "Symmetry plane option"),
            _f("I2D3D", "I", "Segment searching option"),
            _f("SLDTHK", "F", "Optional solid element thickness",
               units="length"),
            _f("SLDSTF", "F", "Optional solid element stiffness",
               units="stress"),
        ], "Penetration, thickness and symmetry options."),
        _optional("C", [
            _f("IGAP", "I", "Implicit convergence and Mortar stiffness "
                            "option", default=1),
            _f("IGNORE", "I", "Initial penetration handling"),
            _f("DPRFAC", "F", "Depth of penetration reduction factor for "
                              "SOFT = 2; MPAR1 for Mortar contact"),
            _f("DTSTIF", "F", "Time step used in the stiffness calculation for "
                              "SOFT = 1 and 2; MPAR2 for Mortar contact",
               units="time"),
            _f("EDGEK", "F", "Scale factor for edge-to-edge penalty "
                             "stiffness"),
            _unused("UNUSED6"),
            _f("FLANGL", "F", "Angle tolerance in radians for feature lines "
                              "in smooth contact"),
            _f("CID_RCF", "I", "Coordinate system for the rcforc and ncforc "
                               "force output"),
        ], "Implicit and initial penetration options."),
        _optional("D", [
            _f("Q2TRI", "I", "Split quadrilateral segments into triangles; "
                             "SOFT = 2 only"),
            _f("DTPCHK", "F", "Time interval between shell penetration "
                              "reports; SOFT = 2 only", units="time"),
            _f("SFNBR", "F", "Scale factor for neighbour segment contact; "
                             "SOFT = 2 only"),
            _f("FNLSCL", "F", "Scale factor for nonlinear force scaling"),
            _f("DNLSCL", "F", "Distance for nonlinear force scaling",
               units="length"),
            _f("TCSO", "I", "Consider only contact segments when computing "
                            "the contact thickness"),
            _f("TIEDID", "I", "Incremental displacement update for tied "
                              "contacts"),
            _f("SHLEDG", "I", "Edge shape assumed for shells; SOFT = 2 only"),
        ], "Segment-based contact options."),
        _optional("E", [
            _f("SHAREC", "I", "Shared constraint flag; SOFT = 2 only"),
            _f("CPARM8", "I", "Beam contact flags"),
            _f("IPBACK", "I", "Nonzero creates a backup penalty tied "
                              "contact"),
            _f("SRNDE", "I", "Non-extended exterior shell edge flag"),
            _f("FRICSF", "F", "Scale factor for frictional stiffness; "
                              "SOFT = 2 only", default=1.0),
            _f("ICOR", "I", "Nonzero makes VDC the coefficient of "
                            "restitution in percent"),
            _f("FTORQ", "I", "Transmittal of moments across the interface"),
            _f("REGION", "I", "*DEFINE_REGION delimiting where the contact is "
                              "active"),
        ], "Shell edge, friction and moment options."),
        _optional("F", [
            _f("PSTIFF", "I", "Method for the penalty stiffness"),
            _f("IGNROFF", "I", "Ignore the shell thickness offset"),
            _unused("UNUSED3"),
            _f("FSTOL", "F", "Tolerance in degrees for flat segments with the "
                             "SMOOTH option", default=2.0),
            _f("2DBINR", "I", "2D belts initially inside retractors are "
                              "involved"),
            _f("SSFTYP", "I", "Which segment's shell thickness scale factor is "
                              "used"),
            _f("SWTPR", "I", "Constant thickness option for tied weld "
                             "segments"),
            _f("TETFAC", "F", "Scale factor on tetrahedron volume for the "
                              "SOFT = 2 mass calculation"),
        ], "Further penalty stiffness and thickness options."),
    ]

    # _parse_raw_data and write are both overridden: MPP 2 is recognised by
    # its first character, and the number of THRM 2.1 lines is read from
    # THRM 2.  Declared for introspection, in file order.
    card_schemas = [
        _CARD_ID, _MPP_1, _MPP_2, _CARD_1, _CARD_2, _CARD_3,
        _THRM_1, _THRM_2, _THRM_2_1, *_ORFR, *_OPTIONAL,
    ]

    # The cards that must be present once their option is on the keyword
    # line.  MPP 2, THRM 2.1 and Optional Cards A-F depend on the data.
    _MANDATORY = [_CARD_ID, _MPP_1, _CARD_1, _CARD_2, _CARD_3,
                  _THRM_1, _THRM_2, *_ORFR]

    @staticmethod
    def _is_mpp2(line: str) -> bool:
        """Whether *line* is MPP 2: an ampersand in the first column.

        An ampersand followed by a name is a parameter reference, which can
        open Card 1 in comma-separated input, so the marker must stand alone.
        """
        return line.startswith('&') and (len(line) == 1 or line[1] in ' \t,')

    def _thrm_2_1_lines(self) -> int:
        """How many THRM 2.1 lines follow THRM 2."""
        thrm2 = self.cards.get("THRM 2")
        if thrm2 is None:
            return 0
        formula = thrm2["FORMULA"][0]
        # A parameter reference cannot be resolved here, so its lines would be
        # misread as the cards that follow; that is left to the caller to see.
        if isinstance(formula, ParameterRef) or formula >= 0:
            return 0
        return math.ceil(-int(formula) / 8)

    def _parse_raw_data(self, raw_lines: List[str]):
        lines = [l for l in raw_lines[1:] if not l.strip().startswith('$')]
        # Trailing blank lines only separate this keyword from the next; a
        # blank card there means all defaults, which is also what an absent
        # card means.  Interior blank lines are cards.
        while lines and not lines[-1].strip():
            lines.pop()
        if not lines:
            return

        idx = 0

        def take(schema: CardSchema) -> bool:
            nonlocal idx
            if idx >= len(lines):
                return False
            self.cards[schema.name] = self._parse_single_card(lines[idx], schema)
            idx += 1
            return True

        if self.has_option("ID"):
            take(self._CARD_ID)
        if self.has_option("MPP"):
            take(self._MPP_1)
            if idx < len(lines) and self._is_mpp2(lines[idx]):
                take(self._MPP_2)
        take(self._CARD_1)
        take(self._CARD_2)
        take(self._CARD_3)
        if self.has_option("THERMAL"):
            take(self._THRM_1)
        if self.has_option("THERMAL_FRICTION"):
            take(self._THRM_2)
            n = self._thrm_2_1_lines()
            if n:
                self.cards["THRM 2.1"] = self._parse_repeating_card(
                    lines[idx:idx + n], self._THRM_2_1)
                idx += n
        if self.has_option("ORTHO_FRICTION"):
            for schema in self._ORFR:
                take(schema)
        for schema in self._OPTIONAL:
            if not take(schema):
                break

        if idx < len(lines):
            logger.warning(
                f"{self.full_keyword}: {len(lines) - idx} data line(s) after "
                f"Optional Card F were ignored")

        # A mandatory card missing at the end of the block was a blank line
        # taken off with the trailing ones; restore it with its defaults.
        for schema in self._MANDATORY:
            if schema.condition is not None and not schema.condition(self):
                continue
            if schema.name not in self.cards:
                self.cards[schema.name] = self._parse_single_card("", schema)

    def write(self, file_obj: TextIO):
        self._write_keyword_line(file_obj)
        for schema in self.card_schemas:
            if schema.condition is not None and not schema.condition(self):
                continue
            card = self.cards.get(schema.name)
            if card is None:
                continue
            if schema is self._MPP_2:
                self._write_mpp_2(file_obj, card)
            else:
                self._write_card(file_obj, card, schema)

    def _write_mpp_2(self, file_obj: TextIO, card):
        """Write MPP 2 with its ampersand in the first column."""
        schema = self._MPP_2
        file_obj.write(self.parser.format_header(
            [f.header_name or f.name for f in schema.fields],
            field_len=[f.width for f in schema.fields]))
        parts = [self.parser.format_field(
                     card[f.name][0] if f.stored else None,
                     f.type, field_len=f.width)
                 for f in schema.fields]
        file_obj.write('&' + ''.join(parts)[1:] + '\n')
