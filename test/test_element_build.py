"""*ELEMENT_SHELL and *ELEMENT_SOLID: building a keyword from data.

Both classes declare ``builds_from_cards``; this module is the evidence.

Covers:
- Building each keyword from data and reading it back unchanged
- The thickness, beta, mcid, offset and dof option cards
- Composite layer stacks, including uneven layer counts across elements and
  the column-4 rule that separates a layer card from the next element
- The orthotropic and scalar-node cards of *ELEMENT_SOLID, and the
  multi-node-card formats
"""

import io
import numpy as np
import pytest
import sys
sys.path.append('.')

import dynakw
from dynakw.keywords.ELEMENT_SHELL import ElementShell
from dynakw.keywords.ELEMENT_SOLID import ElementSolid


def _i(*values):
    return np.array(values, dtype=np.int32)


def _f(*values):
    return np.array(values, dtype=np.float64)


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


def _shell_card1(n=1, midside=False):
    card = {"EID": _i(*range(1, n + 1)), "PID": _i(*([7] * n))}
    for i in range(1, 5):
        card[f"N{i}"] = _i(*[i + 10 * e for e in range(n)])
    for i in range(5, 9):
        card[f"N{i}"] = _i(*[(i + 10 * e) if midside else 0 for e in range(n)])
    return card


def _solid_cards(n=1, n_nodes=10, with_eid=False):
    nodes = {f"N{i + 1}": _i(*[i + 1 + 10 * e for e in range(n)])
             for i in range(n_nodes)}
    if with_eid:
        nodes = {"EID": _i(*range(1, n + 1)), **nodes}
    return {"Card 1": {"EID": _i(*range(1, n + 1)), "PID": _i(*([7] * n))},
            "nodes": nodes}


# ---------------------------------------------------------------------------
# Introspection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("keyword", ["*ELEMENT_SHELL", "*ELEMENT_SOLID"])
def test_introspection_reports_the_element_keywords_as_buildable(keyword):
    spec = dynakw.describe_keyword(keyword)
    assert spec.can_build
    assert spec.custom_write


# ---------------------------------------------------------------------------
# *ELEMENT_SHELL
# ---------------------------------------------------------------------------

def test_build_a_plain_element_shell():
    kw = _build(ElementShell, "*ELEMENT_SHELL", {"Card 1": _shell_card1(3)})
    back = _assert_cards_survive(kw)
    assert list(back.cards["Card 1"]["EID"]) == [1, 2, 3]


def test_build_with_thickness_and_midside_nodes():
    kw = _build(ElementShell, "*ELEMENT_SHELL_THICKNESS", {
        "Card 1": _shell_card1(1, midside=True),
        "Card 2": {"THIC1": _f(1.0), "THIC2": _f(1.1),
                   "THIC3": _f(1.2), "THIC4": _f(1.3)},
        "Card 3": {"THIC5": _f(2.0), "THIC6": _f(2.1),
                   "THIC7": _f(2.2), "THIC8": _f(2.3)},
    })
    back = _assert_cards_survive(kw)
    assert back.cards["Card 3"]["THIC5"][0] == 2.0


def test_card_3_is_only_written_for_elements_with_midside_nodes():
    """A four-node shell has no mid-side thickness card.

    Rows supplied for such elements are dropped on write, so a builder has to
    keep N5-N8 and Card 3 consistent.
    """
    kw = _build(ElementShell, "*ELEMENT_SHELL_THICKNESS", {
        "Card 1": _shell_card1(1, midside=False),
        "Card 2": {"THIC1": _f(1.0), "THIC2": _f(1.0),
                   "THIC3": _f(1.0), "THIC4": _f(1.0)},
        "Card 3": {"THIC5": _f(9.0), "THIC6": _f(9.0),
                   "THIC7": _f(9.0), "THIC8": _f(9.0)},
    })
    assert "Card 3" not in _roundtrip(kw).cards


@pytest.mark.parametrize("option,card_name,card", [
    ("BETA", "Card 2", {"THIC1": _f(1.0), "THIC2": _f(1.0), "THIC3": _f(1.0),
                        "THIC4": _f(1.0), "BETA": _f(30.0)}),
    ("MCID", "Card 2", {"THIC1": _f(1.0), "THIC2": _f(1.0), "THIC3": _f(1.0),
                        "THIC4": _f(1.0), "MCID": _i(4)}),
    ("OFFSET", "Card 4", {"OFFSET": _f(0.5)}),
    ("DOF", "Card 5", {"NS1": _i(11), "NS2": _i(12),
                       "NS3": _i(13), "NS4": _i(14)}),
])
def test_build_element_shell_option_cards(option, card_name, card):
    kw = _build(ElementShell, f"*ELEMENT_SHELL_{option}", {
        "Card 1": _shell_card1(1), card_name: card,
    })
    _assert_cards_survive(kw)


def test_build_a_composite_shell():
    kw = _build(ElementShell, "*ELEMENT_SHELL_COMPOSITE", {
        "Card 1": _shell_card1(1),
        "Card 6": {"MID": np.array([[1, 2]], dtype=np.int32),
                   "THICK": np.array([[0.5, 0.5]]),
                   "B": np.array([[0.0, 90.0]]),
                   "N_LAYERS": _i(2)},
    })
    back = _assert_cards_survive(kw)
    assert list(back.cards["Card 6"]["B"][0]) == [0.0, 90.0]


def test_composite_layers_of_several_elements():
    """The layer stack runs to the next element card, with no marker between.

    Elements with different layer counts are the case that exposes it: the
    parser has to stop at the element card rather than reading on.
    """
    kw = _build(ElementShell, "*ELEMENT_SHELL_COMPOSITE", {
        "Card 1": _shell_card1(2),
        "Card 6": {"MID": np.array([[1, 2, 3], [4, 5, 0]], dtype=np.int32),
                   "THICK": np.array([[0.3, 0.3, 0.4], [0.5, 0.5, 0.0]]),
                   "B": np.array([[0.0, 45.0, 90.0], [0.0, 90.0, 0.0]]),
                   "N_LAYERS": _i(3, 2)},
    })
    back = _assert_cards_survive(kw)
    assert list(back.cards["Card 6"]["N_LAYERS"]) == [3, 2]
    assert list(back.cards["Card 1"]["EID"]) == [1, 2]


def test_composite_layer_card_leaves_column_4_blank():
    """The manual's rule: field 4 of a layer card is zero or blank.

    That is what tells a layer card from the Card 1 of the next element, so the
    second layer of a line starts at column 5.
    """
    kw = _build(ElementShell, "*ELEMENT_SHELL_COMPOSITE", {
        "Card 1": _shell_card1(1),
        "Card 6": {"MID": np.array([[1, 2]], dtype=np.int32),
                   "THICK": np.array([[0.5, 0.5]]),
                   "B": np.array([[0.0, 90.0]]),
                   "N_LAYERS": _i(2)},
    })
    buf = io.StringIO()
    kw.write(buf)
    layer = [l for l in buf.getvalue().splitlines()
             if l and not l.startswith(("$", "*"))][1]

    assert layer[30:40].strip() == ""            # column 4 blank
    assert layer[40:50].strip() == "2"           # second layer's MID
    assert ElementShell._is_layer_card(layer)


def test_element_card_is_not_mistaken_for_a_layer_card():
    element = "       2       7      11      12      13      14       0       0"
    assert not ElementShell._is_layer_card(element)


def test_build_a_composite_long_shell():
    kw = _build(ElementShell, "*ELEMENT_SHELL_COMPOSITE_LONG", {
        "Card 1": _shell_card1(2),
        "Card 7": {"MID": np.array([[1, 2], [3, 4]], dtype=np.int32),
                   "THICK": np.array([[0.5, 0.5], [0.6, 0.4]]),
                   "B": np.array([[0.0, 90.0], [45.0, -45.0]]),
                   "PLYID": np.array([[7, 8], [9, 10]], dtype=np.int32),
                   "N_LAYERS": _i(2, 2)},
    })
    back = _assert_cards_survive(kw)
    assert list(back.cards["Card 7"]["PLYID"][1]) == [9, 10]


# ---------------------------------------------------------------------------
# *ELEMENT_SOLID
# ---------------------------------------------------------------------------

def test_build_a_plain_element_solid():
    kw = _build(ElementSolid, "*ELEMENT_SOLID", _solid_cards(2))
    back = _assert_cards_survive(kw)
    assert list(back.cards["Card 1"]["EID"]) == [1, 2]
    assert back.cards["nodes"]["N8"][0] == 8


def test_build_an_element_solid_with_ortho():
    cards = _solid_cards(1, with_eid=True)
    cards["ortho"] = {"EID": _i(1),
                      "A1_BETA": _f(1.0), "A2": _f(0.0), "A3": _f(0.0),
                      "D1": _f(0.0), "D2": _f(1.0), "D3": _f(0.0)}
    kw = _build(ElementSolid, "*ELEMENT_SOLID_ORTHO", cards)
    back = _assert_cards_survive(kw)
    assert back.cards["ortho"]["D2"][0] == 1.0


def test_build_an_element_solid_with_dof():
    cards = _solid_cards(1, with_eid=True)
    cards["dof"] = {"EID": _i(1),
                    **{f"NS{i + 1}": _i(100 + i) for i in range(8)}}
    kw = _build(ElementSolid, "*ELEMENT_SOLID_DOF", cards)
    back = _assert_cards_survive(kw)
    assert back.cards["dof"]["NS8"][0] == 107


def test_dof_scalar_nodes_start_at_column_3():
    """Columns 1 and 2 of the scalar node card are unused."""
    cards = _solid_cards(1, with_eid=True)
    cards["dof"] = {"EID": _i(1),
                    **{f"NS{i + 1}": _i(100 + i) for i in range(8)}}
    buf = io.StringIO()
    _build(ElementSolid, "*ELEMENT_SOLID_DOF", cards).write(buf)
    line = [l for l in buf.getvalue().splitlines()
            if l and not l.startswith(("$", "*"))][-1]

    assert line[:16].strip() == ""
    assert line[16:24].strip() == "100"


def test_build_an_element_solid_with_twenty_nodes():
    kw = _build(ElementSolid, "*ELEMENT_SOLID_H20",
                _solid_cards(1, n_nodes=20, with_eid=True))
    back = _assert_cards_survive(kw)
    assert back.cards["nodes"]["N20"][0] == 20


def test_built_elements_survive_the_reader(tmp_path):
    shell = _build(ElementShell, "*ELEMENT_SHELL", {"Card 1": _shell_card1(2)})
    solid = _build(ElementSolid, "*ELEMENT_SOLID", _solid_cards(2))

    path = tmp_path / "elements.k"
    with open(path, "w") as fh:
        shell.write(fh)
        solid.write(fh)

    parsed = list(dynakw.DynaKeywordReader(str(path)).keywords())
    assert len(parsed) == 2
    assert list(parsed[0].cards["Card 1"]["EID"]) == [1, 2]
    assert list(parsed[1].cards["Card 1"]["EID"]) == [1, 2]
