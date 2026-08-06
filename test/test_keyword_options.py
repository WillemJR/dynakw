"""Keyword option matching tests.

``self.options`` is the keyword's option suffix split on ``'_'``, so a plain
membership test cannot see an option whose name contains an underscore:
``*PART_ATTACHMENT_NODES`` has the options ``['ATTACHMENT', 'NODES']``, and
``'ATTACHMENT_NODES' in kw.options`` is False.  Keywords therefore match options
with ``has_option``.

Covers:
- ``has_option`` semantics: multi-token names, token boundaries, one option name
  being a prefix of another
- The three keywords that were affected: *PART, *ELEMENT_SHELL and
  *BOUNDARY_PRESCRIBED_MOTION
- That single-token options, which always worked, still do
"""

import io
import numpy as np
import pytest
import sys
sys.path.append('.')

from dynakw import DynaKeywordReader
from dynakw.keywords.NODE import Node
from dynakw.keywords.PART import Part
from dynakw.keywords.ELEMENT_SHELL import ElementShell
from dynakw.keywords.BOUNDARY_PRESCRIBED_MOTION import BoundaryPrescribedMotion


def _write(kw) -> str:
    buf = io.StringIO()
    kw.write(buf)
    return buf.getvalue()


def _reparse(kw):
    """Write *kw* out and parse the result back with the same class."""
    lines = _write(kw).splitlines()
    return type(kw)(lines[0], lines)


def _same(a, b) -> bool:
    """Compare two card columns, which may be 1D or 2D and may hold None."""
    a = np.asarray(a, dtype=object)
    b = np.asarray(b, dtype=object)
    return a.shape == b.shape and bool((a == b).all())


def _assert_roundtrips(kw):
    """The cards must survive a write/parse cycle unchanged."""
    again = _reparse(kw)
    assert list(again.cards) == list(kw.cards)
    for card_name, card in kw.cards.items():
        assert list(again.cards[card_name]) == list(card), card_name
        for field, values in card.items():
            assert _same(again.cards[card_name][field], values), \
                f"{card_name}.{field}"


# ---------------------------------------------------------------------------
# has_option
# ---------------------------------------------------------------------------

def test_has_option_matches_a_multi_token_option():
    kw = Part("*PART_ATTACHMENT_NODES")
    assert kw.options == ["ATTACHMENT", "NODES"]      # what the split gives
    assert "ATTACHMENT_NODES" not in kw.options       # why the plain test failed
    assert kw.has_option("ATTACHMENT_NODES")


def test_has_option_matches_a_single_token_option():
    assert Part("*PART_INERTIA").has_option("INERTIA")


def test_has_option_respects_token_boundaries():
    """A name must match whole tokens, not a substring of one."""
    kw = BoundaryPrescribedMotion("*BOUNDARY_PRESCRIBED_MOTION_RIGID")
    assert not kw.has_option("ID")      # 'RIGID' ends in 'ID'
    assert kw.has_option("RIGID")


def test_has_option_finds_a_trailing_option():
    kw = BoundaryPrescribedMotion("*BOUNDARY_PRESCRIBED_MOTION_SET_ID")
    assert kw.has_option("ID")
    assert kw.has_option("SET")
    assert kw.has_option("SET_ID")


def test_has_option_is_case_insensitive():
    assert Part("*PART_INERTIA").has_option("inertia")


def test_has_option_on_a_keyword_without_options():
    kw = Node("*NODE")
    assert not kw.has_option("ANYTHING")
    assert not kw.has_option("")


def test_has_option_sees_a_prefix_of_a_longer_option():
    """COMPOSITE is a token run of COMPOSITE_LONG, so both match.

    Callers treating the two as alternatives must test the longer name first;
    ElementShell._option_flags does.
    """
    kw = ElementShell("*ELEMENT_SHELL_COMPOSITE_LONG")
    assert kw.has_option("COMPOSITE")
    assert kw.has_option("COMPOSITE_LONG")

    flags = kw._option_flags()
    assert flags.composite_long
    assert not flags.composite


# ---------------------------------------------------------------------------
# *PART_ATTACHMENT_NODES
# ---------------------------------------------------------------------------

PART_ATTACHMENT_NODES = [
    "*PART_ATTACHMENT_NODES",
    "bracket",
    "         1         2         3",
    "       101",
]


def test_part_attachment_nodes_card_is_parsed():
    kw = Part(PART_ATTACHMENT_NODES[0], PART_ATTACHMENT_NODES)
    assert "attachment_nodes" in kw.cards
    assert list(kw.cards["attachment_nodes"]["ANSID"]) == [101]


def test_part_attachment_nodes_roundtrips():
    kw = Part(PART_ATTACHMENT_NODES[0], PART_ATTACHMENT_NODES)
    assert "       101" in _write(kw)
    _assert_roundtrips(kw)


def test_part_inertia_still_works():
    lines = [
        "*PART_INERTIA",
        "flywheel",
        "         1         2         3",
        "       1.0       2.0       3.0       4.0         0         0",
        "       1.0       0.0       0.0       2.0       0.0       3.0",
        "       0.0       0.0       0.0       0.0       0.0       0.0",
    ]
    kw = Part(lines[0], lines)
    assert list(kw.cards["inertia"]["TM"]) == [4.0]
    assert list(kw.cards["inertia"]["IXX"]) == [1.0]


def test_plain_part_has_no_optional_cards():
    lines = ["*PART", "plain", "         1         2         3"]
    kw = Part(lines[0], lines)
    assert set(kw.cards) == {"Card 1", "Card 2"}


# ---------------------------------------------------------------------------
# *ELEMENT_SHELL_COMPOSITE_LONG
# ---------------------------------------------------------------------------

COMPOSITE_LONG = [
    "*ELEMENT_SHELL_COMPOSITE_LONG",
    "       1       1       1       2       3       4",
    "         1       0.5       0.0                   7",
    "         2       0.5      90.0                   8",
]

COMPOSITE = [
    "*ELEMENT_SHELL_COMPOSITE",
    "       1       1       1       2       3       4",
    "         1       0.5       0.0                   2       0.5      90.0",
]


def test_composite_long_uses_card_7():
    kw = ElementShell(COMPOSITE_LONG[0], COMPOSITE_LONG)
    assert "Card 7" in kw.cards
    assert "Card 6" not in kw.cards
    assert list(kw.cards["Card 7"]["PLYID"][0]) == [7, 8]
    assert list(kw.cards["Card 7"]["N_LAYERS"]) == [2]


def test_composite_long_roundtrips():
    _assert_roundtrips(ElementShell(COMPOSITE_LONG[0], COMPOSITE_LONG))


def test_composite_still_uses_card_6():
    kw = ElementShell(COMPOSITE[0], COMPOSITE)
    assert "Card 6" in kw.cards
    assert "Card 7" not in kw.cards
    assert list(kw.cards["Card 6"]["N_LAYERS"]) == [2]


def test_composite_and_composite_long_select_different_schemas():
    """Introspection must tell the two variants apart, as parsing does."""
    def cards_for(name):
        probe = ElementShell(name)
        return [s.name for s in ElementShell.card_schemas
                if s.condition is not None and s.condition(probe)]

    assert "Card 6" in cards_for("*ELEMENT_SHELL_COMPOSITE")
    assert "Card 7" not in cards_for("*ELEMENT_SHELL_COMPOSITE")
    assert "Card 7" in cards_for("*ELEMENT_SHELL_COMPOSITE_LONG")
    assert "Card 6" not in cards_for("*ELEMENT_SHELL_COMPOSITE_LONG")


def test_element_shell_thickness_still_works():
    lines = [
        "*ELEMENT_SHELL_THICKNESS",
        "       1       1       1       2       3       4",
        "             1.0             1.0             1.0             1.0",
    ]
    kw = ElementShell(lines[0], lines)
    assert list(kw.cards["Card 2"]["THIC1"]) == [1.0]


# ---------------------------------------------------------------------------
# *BOUNDARY_PRESCRIBED_MOTION — option cards and their position
# ---------------------------------------------------------------------------

SET_BOX = [
    "*BOUNDARY_PRESCRIBED_MOTION_SET_BOX",
    "         7         1         0        12       2.0",
    "         5         1         0",
]


def test_set_box_card_is_parsed_after_card_1():
    """The manual's Card Summary puts Card 2 after Card 1, not before it."""
    kw = BoundaryPrescribedMotion(SET_BOX[0], SET_BOX)
    assert list(kw.cards["Card 1"]["TYPEID"]) == [7]
    assert list(kw.cards["Card 1"]["LCID"]) == [12]
    assert list(kw.cards["Card 2"]["BOXID"]) == [5]
    assert list(kw.cards["Card 2"]["TOFFSET"]) == [1]


def test_set_box_writes_card_2_after_card_1():
    kw = BoundaryPrescribedMotion(SET_BOX[0], SET_BOX)
    data = [l for l in _write(kw).splitlines()
            if l and not l.startswith(("$", "*"))]
    assert data[0].split() == ["7", "1", "0", "12", "2.0000", "0", "0.0000", "0.0000"]
    assert data[1].split() == ["5", "1", "0"]


def test_set_box_roundtrips():
    _assert_roundtrips(BoundaryPrescribedMotion(SET_BOX[0], SET_BOX))


def test_set_line_card_is_parsed():
    lines = [
        "*BOUNDARY_PRESCRIBED_MOTION_SET_LINE",
        "         7         1         0        12       2.0",
        "       100       200",
    ]
    kw = BoundaryPrescribedMotion(lines[0], lines)
    assert list(kw.cards["Card 4"]["NBEG"]) == [100]
    assert list(kw.cards["Card 4"]["NEND"]) == [200]


def test_option_cards_repeat_per_definition():
    """Each Card 1 carries its own option card."""
    lines = [
        "*BOUNDARY_PRESCRIBED_MOTION_SET_BOX",
        "         7         1         0        12       2.0",
        "         5         1         0",
        "         8         2         0        13       3.0",
        "         6         0         0",
    ]
    kw = BoundaryPrescribedMotion(lines[0], lines)
    assert list(kw.cards["Card 1"]["TYPEID"]) == [7, 8]
    assert list(kw.cards["Card 2"]["BOXID"]) == [5, 6]
    _assert_roundtrips(kw)


def test_plain_prescribed_motion_is_unaffected():
    lines = [
        "*BOUNDARY_PRESCRIBED_MOTION_NODE",
        "         7         1         0        12       2.0",
        "         8         2         0        13       3.0",
    ]
    kw = BoundaryPrescribedMotion(lines[0], lines)
    assert set(kw.cards) == {"Card 1"}
    assert list(kw.cards["Card 1"]["TYPEID"]) == [7, 8]


def test_card_3_still_follows_its_own_card_1():
    """Card 3 is selected by DOF on Card 1, not by a keyword option."""
    lines = [
        "*BOUNDARY_PRESCRIBED_MOTION_NODE",
        "         7         9         0        12       2.0",
        "       1.5       2.5         0         0         0",
        "         8         2         0        13       3.0",
    ]
    kw = BoundaryPrescribedMotion(lines[0], lines)
    assert list(kw.cards["Card 1"]["TYPEID"]) == [7, 8]
    assert kw.cards["Card 3"]["OFFSET1"][0] == 1.5
    assert kw.cards["Card 3"]["OFFSET1"][1] is None


def test_id_option_still_parses_a_leading_card():
    lines = [
        "*BOUNDARY_PRESCRIBED_MOTION_SET_ID",
        "         3my heading",
        "         7         1         0        12       2.0",
    ]
    kw = BoundaryPrescribedMotion(lines[0], lines)
    assert list(kw.cards["Card ID"]["ID"]) == [3]
    assert list(kw.cards["Card 1"]["TYPEID"]) == [7]


# ---------------------------------------------------------------------------
# Through the reader
# ---------------------------------------------------------------------------

def test_affected_keywords_survive_a_file_roundtrip(tmp_path):
    content = "\n".join(PART_ATTACHMENT_NODES + COMPOSITE_LONG + SET_BOX) + "\n"
    in_f = tmp_path / "in.k"
    in_f.write_text(content)

    out_f = tmp_path / "out.k"
    DynaKeywordReader(str(in_f)).write(str(out_f))

    kws = list(DynaKeywordReader(str(out_f)).keywords())
    by_name = {kw.full_keyword: kw for kw in kws}

    assert list(by_name["*PART_ATTACHMENT_NODES"]
                .cards["attachment_nodes"]["ANSID"]) == [101]
    assert list(by_name["*ELEMENT_SHELL_COMPOSITE_LONG"]
                .cards["Card 7"]["PLYID"][0]) == [7, 8]
    assert list(by_name["*BOUNDARY_PRESCRIBED_MOTION_SET_BOX"]
                .cards["Card 2"]["BOXID"]) == [5]
