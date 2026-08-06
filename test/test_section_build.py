"""*SECTION_SHELL and *SECTION_SOLID: building a keyword from data.

Both classes declare ``builds_from_cards``, which makes ``describe_keyword``
report ``can_build`` even though they write themselves.  That flag is a claim;
this module is the evidence for it, across the option cards and the
user-defined element cards as well as the plain form.

Covers:
- Building each keyword from data and reading it back unchanged
- The composite angle card, including a stack that spans several lines
- The EFG, SPG, THERMAL, XFEM and MISC option cards
- The user-defined element cards (ELFORM 101-105)
- The count fields that a builder has to keep consistent
"""

import io
import numpy as np
import pytest
import sys
sys.path.append('.')

import dynakw
from dynakw.keywords.SECTION_SHELL import SectionShell
from dynakw.keywords.SECTION_SOLID import SectionSolid


def _a(v):
    return np.array([v], dtype=object)


def _i(v):
    return np.array([v], dtype=np.int32)


def _f(v):
    return np.array([v], dtype=np.float64)


def _build(cls, name, cards):
    kw = cls(name)
    kw.cards.update(cards)
    return kw


def _roundtrip(kw):
    buf = io.StringIO()
    kw.write(buf)
    lines = buf.getvalue().splitlines()
    return type(kw)(lines[0], lines)


def _assert_cards_survive(kw):
    """Every value written must read back equal, card for card."""
    back = _roundtrip(kw)
    for card_name, card in kw.cards.items():
        assert card_name in back.cards, f"{card_name} lost"
        got = back.cards[card_name]
        assert set(got) == set(card), (
            f"{card_name}: wrote {sorted(card)}, read {sorted(got)}")
        for field, values in card.items():
            for i, value in enumerate(values):
                actual = got[field][i]
                if isinstance(value, (int, float, np.number)):
                    assert float(actual) == float(value), \
                        f"{card_name}.{field}[{i}]: {value} -> {actual}"
                else:
                    assert str(actual) == str(value), \
                        f"{card_name}.{field}[{i}]: {value!r} -> {actual!r}"
    return back


# ---------------------------------------------------------------------------
# Card builders
# ---------------------------------------------------------------------------

def _shell_card1(**overrides):
    card = {"SECID": _a(3), "ELFORM": _i(2), "SHRF": _f(1.0), "NIP": _i(2),
            "PROPT": _f(1.0), "QR/IRID": _i(0), "ICOMP": _i(0), "SETYP": _i(1)}
    card.update(overrides)
    return card


def _shell_card2(**overrides):
    card = {"T1": _f(1.0), "T2": _f(1.0), "T3": _f(1.0), "T4": _f(1.0),
            "NLOC": _f(0.0), "MAREA": _f(0.0), "IDOF": _i(0), "EDGSET": _i(0)}
    card.update(overrides)
    return card


def _solid_card1(**overrides):
    card = {"SECID": _a(4), "ELFORM": _i(1), "AET": _i(0),
            "COHOFF": _f(0.0), "GASKETT": _f(0.0)}
    card.update(overrides)
    return card


# ---------------------------------------------------------------------------
# Introspection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("keyword", ["*SECTION_SHELL", "*SECTION_SOLID"])
def test_introspection_reports_the_section_keywords_as_buildable(keyword):
    spec = dynakw.describe_keyword(keyword)
    assert spec.can_build
    assert spec.custom_write          # ... despite writing themselves


# ---------------------------------------------------------------------------
# *SECTION_SHELL
# ---------------------------------------------------------------------------

def test_build_a_plain_section_shell():
    kw = _build(SectionShell, "*SECTION_SHELL", {
        "Card 1": _shell_card1(ELFORM=_i(16), NIP=_i(5)),
        "Card 2": _shell_card2(T1=_f(2.5), T2=_f(2.5), T3=_f(2.5), T4=_f(2.5)),
    })
    back = _assert_cards_survive(kw)

    assert back.cards["Card 1"]["ELFORM"][0] == 16
    assert back.cards["Card 1"]["NIP"][0] == 5
    assert back.cards["Card 2"]["T1"][0] == 2.5


def test_section_shell_secid_may_be_a_label():
    """SECID is an 'A' field, so a name survives as well as a number."""
    kw = _build(SectionShell, "*SECTION_SHELL", {
        "Card 1": _shell_card1(SECID=_a("shell_2mm")),
        "Card 2": _shell_card2(),
    })
    assert _roundtrip(kw).cards["Card 1"]["SECID"][0] == "shell_2mm"


def test_build_a_composite_section_shell():
    kw = _build(SectionShell, "*SECTION_SHELL", {
        "Card 1": _shell_card1(ICOMP=_i(1), NIP=_i(3)),
        "Card 2": _shell_card2(),
        "Card 3": {"B1": _f(0.0), "B2": _f(45.0), "B3": _f(90.0)},
    })
    back = _assert_cards_survive(kw)

    assert sorted(back.cards["Card 3"]) == ["B1", "B2", "B3"]
    assert back.cards["Card 3"]["B2"][0] == 45.0


def test_composite_angles_spanning_several_lines():
    """Eight angles per line, so NIP = 10 needs two."""
    angles = {f"B{i + 1}": _f(float(i * 10)) for i in range(10)}
    kw = _build(SectionShell, "*SECTION_SHELL", {
        "Card 1": _shell_card1(ICOMP=_i(1), NIP=_i(10)),
        "Card 2": _shell_card2(),
        "Card 3": angles,
    })
    back = _assert_cards_survive(kw)

    assert len(back.cards["Card 3"]) == 10
    assert back.cards["Card 3"]["B10"][0] == 90.0


def test_trailing_blanks_are_not_read_as_extra_angles():
    """A blank column parses as 0, so the angle count comes from NIP.

    Without that, NIP = 3 would come back as B1-B8 and write five spurious
    zeros on the next pass.
    """
    kw = _build(SectionShell, "*SECTION_SHELL", {
        "Card 1": _shell_card1(ICOMP=_i(1), NIP=_i(3)),
        "Card 2": _shell_card2(),
        "Card 3": {"B1": _f(0.0), "B2": _f(45.0), "B3": _f(90.0)},
    })
    text = io.StringIO()
    kw.write(text)
    lines = text.getvalue().splitlines()

    first = SectionShell(lines[0], lines)
    assert len(first.cards["Card 3"]) == 3

    # ... and stays that way however many times it is written and read.
    second = _roundtrip(first)
    assert len(second.cards["Card 3"]) == 3


@pytest.mark.parametrize("option,card_name,card", [
    ("EFG", "Card 4a", {"DX": _f(1.1), "DY": _f(1.2), "ISPLINE": _i(1),
                        "IDILA": _i(2), "IEBT": _i(3), "IDIM": _i(2)}),
    ("THERMAL", "Card 4b", {"ITHELFM": _i(1)}),
    ("XFEM", "Card 4c", {"CMID": _i(185), "BASELM": _i(16), "DOMINT": _i(0),
                         "FAILCR": _i(1), "PROPCR": _i(2), "FS": _f(0.5),
                         "LS/FS1": _f(1.0), "NC/CL": _f(2.0)}),
    ("MISC", "Card 4d", {"THKSCL": _f(0.9)}),
])
def test_build_section_shell_option_cards(option, card_name, card):
    kw = _build(SectionShell, f"*SECTION_SHELL_{option}", {
        "Card 1": _shell_card1(),
        "Card 2": _shell_card2(),
        card_name: card,
    })
    _assert_cards_survive(kw)


def test_build_a_user_defined_section_shell():
    kw = _build(SectionShell, "*SECTION_SHELL", {
        "Card 1": _shell_card1(ELFORM=_i(101)),
        "Card 2": _shell_card2(),
        "Card 5": {"NIPP": _i(2), "NXDOF": _i(0), "IUNF": _i(0), "IHGF": _i(0),
                   "ITAJ": _i(0), "LMC": _i(3), "NHSV": _i(0), "ILOC": _i(0)},
        "Card 5.1": {"XI": np.array([0.5, -0.5]),
                     "ETA": np.array([0.5, -0.5]),
                     "WGT": np.array([1.0, 1.0])},
        "Card 5.2": {"P1": _f(1.0), "P2": _f(2.0), "P3": _f(3.0)},
    })
    back = _assert_cards_survive(kw)

    assert len(back.cards["Card 5.1"]["XI"]) == 2      # NIPP rows
    assert len(back.cards["Card 5.2"]) == 3            # LMC constants


def test_section_shell_card_1_needs_every_declared_field():
    """Cards 1 and 2 are written through the base helper, which indexes directly."""
    kw = _build(SectionShell, "*SECTION_SHELL", {
        "Card 1": {k: v for k, v in _shell_card1().items() if k != "SETYP"},
        "Card 2": _shell_card2(),
    })
    with pytest.raises(KeyError):
        kw.write(io.StringIO())


def test_nip_must_match_the_number_of_angles():
    """NIP on Card 1 decides how many angles are read back.

    Declaring more integration points than angles supplied pads the rest with
    zeros rather than failing, so a builder has to keep the two consistent.
    """
    kw = _build(SectionShell, "*SECTION_SHELL", {
        "Card 1": _shell_card1(ICOMP=_i(1), NIP=_i(5)),
        "Card 2": _shell_card2(),
        "Card 3": {"B1": _f(0.0), "B2": _f(45.0)},      # only two
    })
    back = _roundtrip(kw)
    assert sorted(back.cards["Card 3"]) == ["B1", "B2", "B3", "B4", "B5"]


# ---------------------------------------------------------------------------
# *SECTION_SOLID
# ---------------------------------------------------------------------------

def test_build_a_plain_section_solid():
    kw = _build(SectionSolid, "*SECTION_SOLID", {"Card 1": _solid_card1()})
    back = _assert_cards_survive(kw)
    assert back.cards["Card 1"]["ELFORM"][0] == 1


def test_section_solid_reserved_columns_stay_blank():
    """Card 1 has three unused columns, declared with stored=False."""
    kw = _build(SectionSolid, "*SECTION_SOLID",
                {"Card 1": _solid_card1(ELFORM=_i(2), COHOFF=_f(0.5))})
    buf = io.StringIO()
    kw.write(buf)
    data = [l for l in buf.getvalue().splitlines()
            if l and not l.startswith(("$", "*"))][0]

    assert data[30:60].strip() == ""               # columns 4, 5 and 6
    assert _roundtrip(kw).cards["Card 1"]["COHOFF"][0] == 0.5

    spec = dynakw.describe_keyword("*SECTION_SOLID")
    assert not any(n.startswith("UNUSED") for n in spec.field_names())


@pytest.mark.parametrize("option,card_name,card", [
    ("EFG", "Card 2a.1", {"DX": _f(1.0), "DY": _f(1.0), "DZ": _f(1.0),
                          "ISPLINE": _i(1), "IDILA": _i(0), "IEBT": _i(1),
                          "IDIM": _i(2), "TOLDEF": _f(0.1)}),
    ("SPG", "Card 2b.1", {"DX": _f(1.5), "DY": _f(1.5), "DZ": _f(1.5),
                          "ISPLINE": _i(0), "KERNEL": _i(1), "SMSTEP": _i(15),
                          "MSC": _f(0.0)}),
    ("MISC", "Card 2c", {"COHTHK": _f(0.25)}),
])
def test_build_section_solid_option_cards(option, card_name, card):
    kw = _build(SectionSolid, f"*SECTION_SOLID_{option}", {
        "Card 1": _solid_card1(ELFORM=_i(20)),
        card_name: card,
    })
    _assert_cards_survive(kw)


def test_build_a_user_defined_section_solid():
    kw = _build(SectionSolid, "*SECTION_SOLID", {
        "Card 1": _solid_card1(ELFORM=_i(101)),
        "Card 3": {"NIP": _i(1), "NXDOF": _i(0), "IHGF": _i(0), "ITAJ": _i(0),
                   "LMC": _i(2), "NHSV": _i(0), "XNOD": _i(0)},
        "Card 4": {"XI": np.array([0.0]), "ETA": np.array([0.0]),
                   "ZETA": np.array([0.0]), "WGT": np.array([8.0])},
        "Card 5": {"P1": _f(1.5), "P2": _f(2.5)},
    })
    back = _assert_cards_survive(kw)

    assert len(back.cards["Card 4"]["XI"]) == 1        # NIP rows
    assert back.cards["Card 5"]["P2"][0] == 2.5


def test_built_sections_survive_the_reader(tmp_path):
    shell = _build(SectionShell, "*SECTION_SHELL", {
        "Card 1": _shell_card1(SECID=_a(3)), "Card 2": _shell_card2(T1=_f(2.0)),
    })
    solid = _build(SectionSolid, "*SECTION_SOLID",
                   {"Card 1": _solid_card1(SECID=_a(4))})

    path = tmp_path / "sections.k"
    with open(path, "w") as fh:
        shell.write(fh)
        solid.write(fh)

    parsed = list(dynakw.DynaKeywordReader(str(path)).keywords())
    assert len(parsed) == 2
    assert parsed[0].cards["Card 2"]["T1"][0] == 2.0
    assert parsed[1].cards["Card 1"]["SECID"][0] == "4"
