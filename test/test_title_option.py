"""TITLE option tests.

Most LS-DYNA keywords accept a ``TITLE`` option, which puts a free-form title
line between the keyword line and Card 1.  It is handled once in
``LSDynaKeyword`` rather than per keyword: ``_extract_title`` lifts the line out
of the block before ``_parse_raw_data`` sees it, and ``_write_keyword_line``
puts it back.  So the cases worth pinning are the ones where that seam could
leak:

- the title is stored, and Card 1 is still Card 1 (not shifted by a line)
- a class with its own ``_parse_raw_data`` gets the same treatment for free
  (*SET_SEGMENT parses its own blank lines and attribute defaults)
- a class with its own ``write`` still emits the title
- ``exact_match`` classes resolve ``_TITLE`` without losing the discrimination
  that flag exists for
- ``Unknown`` keeps the title line in its raw text, since it is written back
  verbatim
- a title survives a build → write → read round trip
"""

import io
import sys
sys.path.append('.')

import numpy as np
import pytest

import dynakw
from dynakw import DynaKeywordReader
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.keywords.SET_SEGMENT import SetSegment
from dynakw.keywords.UNKNOWN import Unknown


SEGMENT_TITLE_BLOCK = """*SET_SEGMENT_TITLE
P4
$#     sid       da1       da2       da3       da4    solver       its         -
         1       0.0       0.0       0.0       0.0MECH               0
$#      n1        n2        n3        n4        a1        a2        a3        a4
      2841      2845      2846      2842       0.0       0.0       0.0       0.0
      2410      2416      2417      2411       0.0       0.0       0.0       0.0
      2842      2846      2847      2843       0.0       0.0       0.0       0.0
      2411      2417      2418      2412       0.0       0.0       0.0       0.0
      2843      2847      2848      2844       0.0       0.0       0.0       0.0"""


def _parse(block: str):
    lines = block.splitlines()
    cls = LSDynaKeyword.resolve(lines[0])
    return cls(lines[0], lines)


def _write(kw) -> str:
    buf = io.StringIO()
    kw.write(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# The title line is read, and does not displace the cards
# ---------------------------------------------------------------------------

def test_title_is_stored():
    kw = _parse(SEGMENT_TITLE_BLOCK)
    assert isinstance(kw, SetSegment)
    assert kw.title == "P4"


def test_cards_are_not_shifted_by_the_title():
    """Card 1 must still be Card 1 --- the failure this whole thing prevents."""
    kw = _parse(SEGMENT_TITLE_BLOCK)
    assert kw.cards['Card 1']['SID'][0] == 1
    assert kw.cards['Card 1']['SOLVER'][0] == 'MECH'
    assert list(kw.cards['Card 2']['N1']) == [2841, 2410, 2842, 2411, 2843]
    assert list(kw.cards['Card 2']['N4']) == [2842, 2411, 2843, 2412, 2844]


def test_no_title_option_means_no_title():
    kw = _parse(SEGMENT_TITLE_BLOCK.replace("*SET_SEGMENT_TITLE", "*SET_SEGMENT")
                                   .replace("P4\n", ""))
    assert kw.title is None
    assert kw.cards['Card 1']['SID'][0] == 1


def test_round_trip_preserves_the_title():
    kw = _parse(SEGMENT_TITLE_BLOCK)
    out = _write(kw).splitlines()
    assert out[0] == "*SET_SEGMENT_TITLE"
    assert out[1] == "P4"

    again = _parse(_write(kw))
    assert again.title == "P4"
    assert list(again.cards['Card 2']['N1']) == list(kw.cards['Card 2']['N1'])


def test_title_may_be_indented_or_blank():
    """The first non-comment line is the title whatever it holds.

    A blank line is *not* skipped: LS-DYNA reads it as an empty title, and
    skipping it would consume Card 1 as the title instead.
    """
    kw = _parse(SEGMENT_TITLE_BLOCK.replace("\nP4\n", "\n\n"))
    assert kw.title == ""
    assert kw.cards['Card 1']['SID'][0] == 1

    kw = _parse(SEGMENT_TITLE_BLOCK.replace("\nP4\n", "\n   spaced title  \n"))
    assert kw.title == "   spaced title"


def test_comment_before_the_title_is_skipped():
    kw = _parse(SEGMENT_TITLE_BLOCK.replace("\nP4\n", "\n$ a comment\nP4\n"))
    assert kw.title == "P4"
    assert kw.cards['Card 1']['SID'][0] == 1


# ---------------------------------------------------------------------------
# The seam holds for classes that parse or write themselves
# ---------------------------------------------------------------------------

def test_custom_parse_still_gets_its_defaults_applied():
    """*SET_SEGMENT parses itself; its Remark 2 handling must still line up.

    ``_apply_attribute_defaults`` walks the segment lines in parallel with the
    parsed rows, so an off-by-one from the title line would fill the wrong rows.
    """
    block = SEGMENT_TITLE_BLOCK.replace(
        "         1       0.0       0.0       0.0       0.0MECH               0",
        "         1       1.5       0.0       0.0       0.0MECH               0",
    ).replace(
        "      2410      2416      2417      2411       0.0       0.0       0.0       0.0",
        "      2410      2416      2417      2411",
    )
    kw = _parse(block)
    assert kw.title == "P4"
    # Row 1 left A1 blank, so it takes DA1; the others gave an explicit 0.0.
    assert kw.cards['Card 2']['A1'][1] == pytest.approx(1.5)
    assert kw.cards['Card 2']['A1'][0] == pytest.approx(0.0)


def test_custom_write_emits_the_title():
    """A class with its own ``write`` must use ``_write_keyword_line``."""
    block = "\n".join([
        "*SECTION_SHELL_TITLE",
        "shell section for the floor pan",
        "         1         2       1.0         2       1.0         0         0         0",
        "       1.0       1.0       1.0       1.0       0.0       0.0       0.0",
    ])
    kw = _parse(block)
    assert type(kw).write is not LSDynaKeyword.write, "expected a custom writer"
    assert kw.title == "shell section for the floor pan"

    out = _write(kw).splitlines()
    assert out[0] == "*SECTION_SHELL_TITLE"
    assert out[1] == "shell section for the floor pan"
    assert _parse(_write(kw)).title == kw.title


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name, expected", [
    ("*SET_SEGMENT_TITLE",                 "SetSegment"),
    ("*SET_SEGMENT_GENERAL_TITLE",         "SetSegment"),
    ("*MAT_RIGID_TITLE",                   "MatRigid"),
    ("*MAT_ELASTIC_TITLE",                 "MatElastic"),
    ("*CONSTRAINED_JOINT_SPHERICAL_TITLE", "ConstrainedJoint"),
])
def test_title_variants_resolve(name, expected):
    cls = LSDynaKeyword.resolve(name)
    assert cls is not None and cls.__name__ == expected


@pytest.mark.parametrize("name", [
    "*MAT_RIGID_DISCRETE",          # MAT_220, not an option of *MAT_RIGID
    "*MAT_ELASTIC_PLASTIC_HYDRO",   # MAT_010, not an option of *MAT_ELASTIC
    "*CONSTRAINED_JOINT_STIFFNESS", # its own keyword, its own layout
])
def test_exact_match_still_discriminates(name):
    """Accepting ``_TITLE`` must not reopen what ``exact_match`` closed."""
    assert LSDynaKeyword.resolve(name) is None


def test_unknown_keeps_the_title_in_its_raw_text():
    """The fallback is written back verbatim, so nothing may be lifted out."""
    block = "*NOT_A_REAL_KEYWORD_TITLE\nsome title\n         1\n"
    kw = Unknown("*NOT_A_REAL_KEYWORD_TITLE", block.splitlines())
    assert kw.title is None
    assert "some title" in kw.raw_data
    assert "some title" in _write(kw)


# ---------------------------------------------------------------------------
# Building
# ---------------------------------------------------------------------------

def test_build_with_a_title():
    kw = SetSegment("*SET_SEGMENT_TITLE")
    kw.title = "built from scratch"
    kw.cards['Card 1'] = {
        'SID': np.array([7], dtype=np.int32),
        'DA1': np.array([0.0]), 'DA2': np.array([0.0]),
        'DA3': np.array([0.0]), 'DA4': np.array([0.0]),
        'SOLVER': np.array(['MECH'], dtype=object),
        'ITS': np.array([0], dtype=np.int32),
    }
    kw.cards['Card 2'] = {
        'N1': np.array([1, 5], dtype=np.int32),
        'N2': np.array([2, 6], dtype=np.int32),
        'N3': np.array([3, 7], dtype=np.int32),
        'N4': np.array([4, 8], dtype=np.int32),
        'A1': np.array([0.0, 0.0]), 'A2': np.array([0.0, 0.0]),
        'A3': np.array([0.0, 0.0]), 'A4': np.array([0.0, 0.0]),
    }

    back = _parse(_write(kw))
    assert back.title == "built from scratch"
    assert back.cards['Card 1']['SID'][0] == 7
    assert list(back.cards['Card 2']['N1']) == [1, 5]


def test_title_is_none_on_a_fresh_instance():
    assert SetSegment("*SET_SEGMENT").title is None
    assert SetSegment("*SET_SEGMENT_TITLE").title is None


# ---------------------------------------------------------------------------
# Reading a file, and introspection
# ---------------------------------------------------------------------------

def test_reader_round_trip(tmp_path):
    src = tmp_path / "in.k"
    src.write_text("*KEYWORD\n" + SEGMENT_TITLE_BLOCK + "\n*END\n")

    reader = DynaKeywordReader(str(src))
    sets = [k for k in reader.keywords() if isinstance(k, SetSegment)]
    assert len(sets) == 1 and sets[0].title == "P4"

    out = tmp_path / "out.k"
    reader.write(str(out))
    text = out.read_text()
    assert "*SET_SEGMENT_TITLE\nP4\n" in text


def test_introspection_reports_title_support():
    assert dynakw.describe_keyword("*SET_SEGMENT_TITLE").has_title is True
    assert dynakw.describe_keyword("*SET_SEGMENT").has_title is True
    assert dynakw.describe_keyword("*NODE").has_title is False
    assert dynakw.describe_keyword("*UNKNOWN").has_title is False


# The manual grants TITLE by family, in the introduction to a section rather
# than in each keyword's option list.  Checked against R14:
#
#   Vol I,  *SET      "appended to all the *SET keywords"
#   Vol I,  *SECTION  "appended to all the *SECTION keywords"
#   Vol I,  *DEFINE   "unless noted otherwise ... the *DEFINE keywords"
#   Vol II, *MAT      "appended to a *MAT keyword"
#
# The rest list their options explicitly and TITLE is not among them:
# *NODE (MERGE), *ELEMENT_SHELL (THICKNESS, BETA/MCID, OFFSET, ...),
# *ELEMENT_SOLID (ORTHO, DOF, ...), *PART (INERTIA, REPOSITION, ...),
# *PARAMETER and *PARAMETER_EXPRESSION (LOCAL, MUTABLE, NOECHO),
# *CONTROL_TERMINATION (no options at all),
# *BOUNDARY_PRESCRIBED_MOTION (ID, BNDOUT2DYNAIN) and
# *CONSTRAINED_JOINT (LOCAL, ID, FAILURE) --- the last two have an ID option
# that reads an ID and a heading, which is a different card, not this one.
TITLE_KEYWORDS = {
    "*DEFINE_CURVE",
    "*MAT_ELASTIC",
    "*MAT_RIGID",
    "*SECTION_SHELL",
    "*SECTION_SOLID",
    "*SET_NODE",
    "*SET_SEGMENT",
    "*SET_SHELL",
    "*SET_SOLID",
}


def test_title_roster_matches_the_manual():
    """Which keywords claim TITLE, pinned so a change has to be deliberate.

    ``supports_title`` is a claim about the manual that no code can check, so
    it is checked here instead: adding a keyword that accepts TITLE means
    adding it to this set, and the citation goes next to the flag.
    """
    reported = {s.keyword for s in dynakw.supported_keywords() if s.has_title}
    assert reported == TITLE_KEYWORDS


def test_keywords_without_the_option_do_not_take_a_title():
    """A keyword the manual gives no TITLE to must not eat its first data line."""
    node = "       1             0.0             0.0             0.0       0       0"
    kw = _parse("*NODE_TITLE\n" + node)
    assert kw.title is None
    assert kw.cards['Card 1']['NID'][0] == 1


def test_the_title_is_not_reported_as_a_card():
    """It lives in ``keyword.title``, so no card or field may claim it."""
    spec = dynakw.describe_keyword("*SET_SEGMENT_TITLE")
    assert "TITLE" not in spec.field_names()
    assert all("TITLE" not in c.name.upper() for c in spec.cards)
