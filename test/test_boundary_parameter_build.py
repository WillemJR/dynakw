"""*BOUNDARY_PRESCRIBED_MOTION and *PARAMETER: building from data.

Both classes declare ``builds_from_cards``; this module is the evidence.

Covers:
- Building each keyword from data and reading it back unchanged
- The ID, SET_BOX and SET_LINE option cards, which hold one row per definition
- Card 3, which is present only for the Card 1 rows whose DOF or VAD calls for
  it, and holds None elsewhere
- Parameter names keeping the type prefix that selects their value's format
"""

import io
import numpy as np
import pytest
import sys
sys.path.append('.')

import dynakw
from dynakw.keywords.BOUNDARY_PRESCRIBED_MOTION import BoundaryPrescribedMotion
from dynakw.keywords.PARAMETER import Parameter


def _i(*values):
    return np.array(values, dtype=np.int32)


def _f(*values):
    return np.array(values, dtype=np.float64)


def _o(*values):
    return np.array(values, dtype=object)


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
    back = _roundtrip(kw)
    for card_name, card in kw.cards.items():
        assert card_name in back.cards, f"{card_name} lost"
        got = back.cards[card_name]
        assert set(got) == set(card), (
            f"{card_name}: wrote {sorted(card)}, read {sorted(got)}")
        for field, values in card.items():
            a = np.asarray(values, dtype=object)
            b = np.asarray(got[field], dtype=object)
            assert a.shape == b.shape, \
                f"{card_name}.{field}: {a.shape} -> {b.shape}"
            assert bool((a == b).all()), \
                f"{card_name}.{field}: {a.tolist()} -> {b.tolist()}"
    return back


def _motion_card1(n=1, dof=None, vad=None):
    dof = dof or [1] * n
    vad = vad or [0] * n
    return {"TYPEID": _i(*range(7, 7 + n)), "DOF": _i(*dof), "VAD": _i(*vad),
            "LCID": _i(*[12 + i for i in range(n)]), "SF": _f(*([1.0] * n)),
            "VID": _i(*([0] * n)), "DEATH": _f(*([0.0] * n)),
            "BIRTH": _f(*([0.0] * n))}


# ---------------------------------------------------------------------------
# Introspection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("keyword",
                         ["*BOUNDARY_PRESCRIBED_MOTION", "*PARAMETER"])
def test_introspection_reports_them_as_buildable(keyword):
    spec = dynakw.describe_keyword(keyword)
    assert spec.can_build
    assert spec.custom_write


def test_every_supported_keyword_is_now_buildable():
    """The Phase 3 checklist is empty."""
    not_buildable = [s.keyword for s in dynakw.supported_keywords()
                     if not s.can_build]
    assert not_buildable == []


# ---------------------------------------------------------------------------
# *BOUNDARY_PRESCRIBED_MOTION
# ---------------------------------------------------------------------------

def test_build_a_plain_prescribed_motion():
    kw = _build(BoundaryPrescribedMotion, "*BOUNDARY_PRESCRIBED_MOTION_NODE",
                {"Card 1": _motion_card1(2, dof=[1, 2])})
    back = _assert_cards_survive(kw)
    assert list(back.cards["Card 1"]["TYPEID"]) == [7, 8]
    assert list(back.cards["Card 1"]["LCID"]) == [12, 13]


def test_build_with_the_id_card():
    kw = _build(BoundaryPrescribedMotion, "*BOUNDARY_PRESCRIBED_MOTION_SET_ID", {
        "Card ID": {"ID": _i(3), "HEADING": _o("crush plate")},
        "Card 1": _motion_card1(1),
    })
    back = _assert_cards_survive(kw)
    assert back.cards["Card ID"]["ID"][0] == 3


def test_build_with_the_set_box_card():
    kw = _build(BoundaryPrescribedMotion, "*BOUNDARY_PRESCRIBED_MOTION_SET_BOX", {
        "Card 1": _motion_card1(2, dof=[1, 2]),
        "Card 2": {"BOXID": _i(5, 6), "TOFFSET": _i(1, 0), "LCBCHK": _i(0, 0)},
    })
    back = _assert_cards_survive(kw)
    assert list(back.cards["Card 2"]["BOXID"]) == [5, 6]


def test_build_with_the_set_line_card():
    kw = _build(BoundaryPrescribedMotion, "*BOUNDARY_PRESCRIBED_MOTION_SET_LINE", {
        "Card 1": _motion_card1(1),
        "Card 4": {"NBEG": _i(100), "NEND": _i(200)},
    })
    back = _assert_cards_survive(kw)
    assert back.cards["Card 4"]["NEND"][0] == 200


def test_card_3_is_written_only_for_the_rows_that_call_for_it():
    """Card 3 follows a Card 1 row whose |DOF| is 9-11 or whose VAD is 4.

    It is stored with one row per Card 1 row, so a row without one holds None
    in every column.
    """
    kw = _build(BoundaryPrescribedMotion, "*BOUNDARY_PRESCRIBED_MOTION_NODE", {
        "Card 1": _motion_card1(2, dof=[9, 2]),
        "Card 3": {"OFFSET1": _o(1.5, None), "OFFSET2": _o(2.5, None),
                   "LRB": _o(0, None), "NODE1": _o(0, None),
                   "NODE2": _o(0, None)},
    })
    back = _assert_cards_survive(kw)

    assert back.cards["Card 3"]["OFFSET1"][0] == 1.5
    assert back.cards["Card 3"]["OFFSET1"][1] is None


def test_card_3_for_a_relative_displacement_row():
    kw = _build(BoundaryPrescribedMotion, "*BOUNDARY_PRESCRIBED_MOTION_NODE", {
        "Card 1": _motion_card1(1, dof=[1], vad=[4]),
        "Card 3": {"OFFSET1": _o(0.0), "OFFSET2": _o(0.0), "LRB": _o(9),
                   "NODE1": _o(11), "NODE2": _o(12)},
    })
    back = _assert_cards_survive(kw)
    assert back.cards["Card 3"]["LRB"][0] == 9


# ---------------------------------------------------------------------------
# *PARAMETER
# ---------------------------------------------------------------------------

def test_build_a_parameter_keyword():
    kw = _build(Parameter, "*PARAMETER", {
        "Card 1": {"PRMR1": _o("Rterm"), "VAL1": _o(0.5),
                   "PRMR2": _o("Istates"), "VAL2": _o(100),
                   "PRMR3": _o(None), "VAL3": _o(None),
                   "PRMR4": _o(None), "VAL4": _o(None)},
    })
    back = _assert_cards_survive(kw)
    assert back.cards["Card 1"]["VAL1"][0] == 0.5
    assert back.cards["Card 1"]["VAL2"][0] == 100


def test_parameter_type_prefix_selects_the_value_format():
    """R writes a float, I an integer, C a string."""
    kw = _build(Parameter, "*PARAMETER", {
        "Card 1": {"PRMR1": _o("Rreal"), "VAL1": _o(2.5),
                   "PRMR2": _o("Iint"), "VAL2": _o(7),
                   "PRMR3": _o("Cchar"), "VAL3": _o("foo"),
                   "PRMR4": _o(None), "VAL4": _o(None)},
    })
    back = _roundtrip(kw)

    assert isinstance(back.cards["Card 1"]["VAL1"][0], float)
    assert isinstance(back.cards["Card 1"]["VAL2"][0], int)
    assert back.cards["Card 1"]["VAL3"][0] == "foo"


def test_build_several_parameter_rows():
    kw = _build(Parameter, "*PARAMETER", {
        "Card 1": {"PRMR1": _o("Ra", "Rb"), "VAL1": _o(1.0, 2.0),
                   "PRMR2": _o("Ic", None), "VAL2": _o(3, None),
                   "PRMR3": _o(None, None), "VAL3": _o(None, None),
                   "PRMR4": _o(None, None), "VAL4": _o(None, None)},
    })
    back = _assert_cards_survive(kw)
    assert list(back.cards["Card 1"]["VAL1"]) == [1.0, 2.0]


def test_built_parameters_are_readable_by_the_reader(tmp_path):
    """The values come back through the reader's parameters() helper."""
    kw = _build(Parameter, "*PARAMETER", {
        "Card 1": {"PRMR1": _o("Rterm"), "VAL1": _o(0.5),
                   "PRMR2": _o("Istates"), "VAL2": _o(100),
                   "PRMR3": _o(None), "VAL3": _o(None),
                   "PRMR4": _o(None), "VAL4": _o(None)},
    })
    path = tmp_path / "params.k"
    with open(path, "w") as fh:
        kw.write(fh)

    params = dynakw.DynaKeywordReader(str(path)).parameters()
    assert params["term"] == 0.5
    assert params["states"] == 100
