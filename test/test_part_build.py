"""*PART: fixed-width parsing, and building a keyword from data.

``Part`` declares ``builds_from_cards``, which makes ``describe_keyword`` report
``can_build`` even though the class has its own ``write``.  That flag is a claim;
this module is the evidence for it.

Covers:
- Parsing preserves fixed-width columns (values wider than one character)
- A *PART built from data alone writes correctly and reads back unchanged
- The same for the INERTIA option, including its per-part card
- The PID join column that ties an optional card to its part
"""

import io
import numpy as np
import pytest
import sys
sys.path.append('.')

import dynakw
from dynakw.keywords.PART import Part


def _obj(*values):
    return np.array(values, dtype=object)


def _build(keyword_name, cards) -> Part:
    kw = Part(keyword_name)
    kw.cards.update(cards)
    return kw


def _roundtrip(kw) -> Part:
    buf = io.StringIO()
    kw.write(buf)
    lines = buf.getvalue().splitlines()
    return Part(lines[0], lines)


def _main_card(pids, secids, mids):
    n = len(pids)
    zeros_i = np.zeros(n, dtype=np.int32)
    return {
        "PID": _obj(*pids), "SECID": _obj(*secids), "MID": _obj(*mids),
        "EOSID": _obj(*([0] * n)), "HGID": zeros_i, "GRAV": zeros_i,
        "ADPOPT": _obj(*([0] * n)), "TMID": _obj(*([0] * n)),
    }


# ---------------------------------------------------------------------------
# Fixed-width parsing
# ---------------------------------------------------------------------------

def test_multi_character_fields_keep_their_columns():
    """Stripping the card lines would shift every column left.

    The damage is invisible while every value is a single digit, which is what
    the sample decks happen to contain, so this case is checked explicitly.
    """
    lines = ["*PART", "bracket",
             "         7        10        20         0        30"]
    card = Part(lines[0], lines).cards["Card 2"]

    assert card["PID"][0] == 7
    assert card["SECID"][0] == 10
    assert card["MID"][0] == 20
    assert card["EOSID"][0] == 0
    assert card["HGID"][0] == 30


def test_single_digit_fields_still_parse():
    lines = ["*PART", "bracket", "         7         1         2"]
    card = Part(lines[0], lines).cards["Card 2"]
    assert (card["PID"][0], card["SECID"][0], card["MID"][0]) == (7, 1, 2)


def test_heading_is_stripped_even_though_cards_are_not():
    lines = ["*PART", "  bracket  ", "         7         1         2"]
    kw = Part(lines[0], lines)
    assert kw.cards["Card 1"]["HEADING"][0] == "bracket"


def test_wide_ids_roundtrip():
    lines = ["*PART", "panel",
             "   1000001   2000002   3000003"]
    kw = Part(lines[0], lines)
    assert kw.cards["Card 2"]["PID"][0] == 1000001

    back = _roundtrip(kw)
    assert back.cards["Card 2"]["PID"][0] == 1000001
    assert back.cards["Card 2"]["SECID"][0] == 2000002
    assert back.cards["Card 2"]["MID"][0] == 3000003


# ---------------------------------------------------------------------------
# Building from data
# ---------------------------------------------------------------------------

def test_introspection_reports_part_as_buildable():
    spec = dynakw.describe_keyword("*PART")
    assert spec.can_build
    assert spec.custom_write          # ... despite writing itself


def test_build_a_part_from_data():
    kw = _build("*PART", {
        "Card 1": {"PID": _obj(7, 42),
                   "HEADING": _obj("bracket", "panel")},
        "Card 2": _main_card([7, 42], [10, 11], [20, 21]),
    })

    back = _roundtrip(kw)

    assert list(back.cards["Card 2"]["PID"]) == [7, 42]
    assert list(back.cards["Card 2"]["SECID"]) == [10, 11]
    assert list(back.cards["Card 2"]["MID"]) == [20, 21]
    assert list(back.cards["Card 1"]["HEADING"]) == ["bracket", "panel"]


def test_built_part_writes_its_heading_before_the_data():
    kw = _build("*PART", {
        "Card 1": {"PID": _obj(7), "HEADING": _obj("bracket")},
        "Card 2": _main_card([7], [10], [20]),
    })
    buf = io.StringIO()
    kw.write(buf)
    lines = buf.getvalue().splitlines()

    assert lines[0] == "*PART"
    assert lines[1] == "bracket"
    assert lines[2].startswith("$")          # column header comment
    assert lines[3].split() == ["7", "10", "20", "0", "0", "0", "0", "0"]


def test_build_a_part_with_inertia():
    n = 1
    zeros = _obj(*([0.0] * n))
    kw = _build("*PART_INERTIA", {
        "Card 1": {"PID": _obj(7), "HEADING": _obj("flywheel")},
        "Card 2": _main_card([7], [10], [20]),
        "inertia": {
            "PID": _obj(7),
            "XC": _obj(1.0), "YC": _obj(2.0), "ZC": _obj(3.0),
            "TM": _obj(12.5), "IRCS": _obj(0), "NODEID": _obj(0),
            "IXX": _obj(1.0), "IXY": zeros, "IXZ": zeros,
            "IYY": _obj(2.0), "IYZ": zeros, "IZZ": _obj(3.0),
            "VTX": zeros, "VTY": zeros, "VTZ": zeros,
            "VRX": zeros, "VRY": zeros, "VRZ": zeros,
        },
    })

    back = _roundtrip(kw)

    assert back.cards["inertia"]["TM"][0] == 12.5
    assert back.cards["inertia"]["XC"][0] == 1.0
    assert back.cards["inertia"]["IZZ"][0] == 3.0
    assert back.cards["Card 2"]["SECID"][0] == 10


def test_optional_cards_are_matched_to_their_part_by_pid():
    """The PID column ties each optional card row to its part.

    A keyword option applies to the whole block, so every part carries the
    card; the PID column is what puts the right row against the right part,
    including when the rows are given in a different order from the parts.
    """
    kw = _build("*PART_CONTACT", {
        "Card 1": {"PID": _obj(7, 42), "HEADING": _obj("a", "b")},
        "Card 2": _main_card([7, 42], [10, 11], [20, 21]),
        "contact": {
            "PID": _obj(42, 7),                  # deliberately reversed
            "FS": _obj(0.9, 0.3), "FD": _obj(0.8, 0.2),
            "DC": _obj(0.0, 0.0), "VC": _obj(0.0, 0.0),
            "OPTT": _obj(0.0, 0.0), "SFT": _obj(1.0, 1.0),
            "SSF": _obj(1.0, 1.0), "CPARM8": _obj(0.0, 0.0),
        },
    })

    back = _roundtrip(kw)

    # Written in part order, so the reversed input comes back as 7 then 42.
    assert list(back.cards["Card 2"]["PID"]) == [7, 42]
    assert back.cards["contact"]["FS"][0] == 0.3      # part 7
    assert back.cards["contact"]["FS"][1] == 0.9      # part 42


def test_an_option_card_is_needed_for_every_part():
    """A keyword option applies to the whole block, not to individual parts.

    The parser therefore expects one optional card per part.  Supplying rows
    for only some parts writes a block that no longer reads back the way it was
    built, so a builder must populate the card for every part.
    """
    kw = _build("*PART_CONTACT", {
        "Card 1": {"PID": _obj(7, 42), "HEADING": _obj("a", "b")},
        "Card 2": _main_card([7, 42], [10, 11], [20, 21]),
        "contact": {
            "PID": _obj(42),                     # the second part only
            "FS": _obj(0.9), "FD": _obj(0.8), "DC": _obj(0.0),
            "VC": _obj(0.0), "OPTT": _obj(0.0), "SFT": _obj(1.0),
            "SSF": _obj(1.0), "CPARM8": _obj(0.0),
        },
    })

    back = _roundtrip(kw)

    # The second part's heading line is consumed as part 7's missing contact
    # card, so the block no longer round-trips.  Documented here rather than
    # guarded against: catching it belongs with the deck-level validation in
    # Phase 3 of DECK_BUILDING_PLAN.md.
    assert list(back.cards["Card 2"]["PID"]) != [7, 42]


def test_a_part_built_without_headings_still_writes():
    """Card 1 is optional when building; the parts are written without one."""
    kw = _build("*PART", {"Card 2": _main_card([7], [10], [20])})

    buf = io.StringIO()
    kw.write(buf)
    assert "7" in buf.getvalue()


def test_built_part_survives_the_reader(tmp_path):
    kw = _build("*PART", {
        "Card 1": {"PID": _obj(7), "HEADING": _obj("bracket")},
        "Card 2": _main_card([7], [10], [20]),
    })

    path = tmp_path / "built.k"
    with open(path, "w") as fh:
        kw.write(fh)

    parsed = list(dynakw.DynaKeywordReader(str(path)).keywords())
    assert len(parsed) == 1
    assert parsed[0].cards["Card 2"]["SECID"][0] == 10


# ---------------------------------------------------------------------------
# The flag itself
# ---------------------------------------------------------------------------

def test_builds_from_cards_defaults_to_false():
    """The claim must be made deliberately, per class."""
    assert dynakw.LSDynaKeyword.builds_from_cards is False


def test_base_write_keywords_do_not_need_the_flag():
    assert not dynakw.keywords.NODE.Node.builds_from_cards
    assert dynakw.describe_keyword("*NODE").can_build
