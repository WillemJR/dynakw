"""Capability introspection tests.

Covers:
- ``supported_keywords`` listing and pattern filtering
- ``describe_keyword`` resolving a *variant*, with option conditions applied
- Keyword name resolution matching the reader's, including ``exact_match``
- The ``can_build`` / ``schema_driven`` flags
- ``capability_manifest`` being JSON-serializable
- That what introspection reports covers what the parser actually produces on
  the real fixture files, which is what stops the report drifting from reality
"""

import json
import pathlib
import pytest
import sys
sys.path.append('.')

import dynakw
from dynakw import (
    DynaKeywordReader,
    KeywordNotSupported,
    capability_manifest,
    describe_keyword,
    supported_keywords,
)
from dynakw.core.introspect import MANIFEST_VERSION
from dynakw.keywords.ELEMENT_SHELL import ElementShell
from dynakw.keywords.NODE import Node
from dynakw.keywords.UNKNOWN import Unknown


FIXTURES = sorted(pathlib.Path("test/full_files").glob("*.k"))


# ---------------------------------------------------------------------------
# supported_keywords
# ---------------------------------------------------------------------------

def test_supported_keywords_lists_the_implemented_keywords():
    names = [s.keyword for s in supported_keywords()]
    assert "*NODE" in names
    assert "*PART" in names
    assert "*MAT_ELASTIC" in names


def test_supported_keywords_is_sorted_and_unique():
    names = [s.keyword for s in supported_keywords()]
    assert names == sorted(names)
    assert len(names) == len(set(names))


def test_supported_keywords_excludes_the_raw_text_fallback():
    """*UNKNOWN is the fallback, not a keyword anyone would ask to build."""
    assert "*UNKNOWN" not in [s.keyword for s in supported_keywords()]


def test_supported_keywords_filters_by_pattern():
    names = [s.keyword for s in supported_keywords("*SET_*")]
    assert names == ["*SET_NODE", "*SET_SEGMENT", "*SET_SHELL", "*SET_SOLID"]


def test_pattern_also_matches_aliases():
    """*MAT_001 is an alias of *MAT_ELASTIC, so the keyword is still found."""
    names = [s.keyword for s in supported_keywords("*MAT_001")]
    assert names == ["*MAT_ELASTIC"]


def test_pattern_matching_nothing_returns_empty():
    assert supported_keywords("*NO_SUCH_THING*") == []


def test_every_spec_carries_its_metadata():
    for spec in supported_keywords():
        assert spec.description
        assert spec.manual_section
        assert spec.cards


# ---------------------------------------------------------------------------
# describe_keyword — variant resolution
# ---------------------------------------------------------------------------

def test_describe_resolves_the_fluid_variant():
    solid = describe_keyword("*MAT_ELASTIC")
    fluid = describe_keyword("*MAT_ELASTIC_FLUID")

    assert [c.name for c in solid.cards] == ["Card 1"]
    assert [c.name for c in fluid.cards] == ["Card 1", "Card 2"]

    assert solid.card("Card 1").fields[2].name == "E"
    assert [f.name for f in fluid.card("Card 1").fields] == ["MID", "RO", "K"]


def test_describe_resolves_element_shell_options():
    plain = describe_keyword("*ELEMENT_SHELL")
    thick = describe_keyword("*ELEMENT_SHELL_THICKNESS")
    comp = describe_keyword("*ELEMENT_SHELL_COMPOSITE")
    long_ = describe_keyword("*ELEMENT_SHELL_COMPOSITE_LONG")

    assert [c.name for c in plain.cards] == ["Card 1"]
    assert "Card 2" in [c.name for c in thick.cards]
    assert "Card 6" in [c.name for c in comp.cards]
    assert "Card 7" not in [c.name for c in comp.cards]
    assert "Card 7" in [c.name for c in long_.cards]
    assert "Card 6" not in [c.name for c in long_.cards]


def test_describe_resolves_multi_token_options():
    spec = describe_keyword("*PART_ATTACHMENT_NODES")
    assert "attachment_nodes" in [c.name for c in spec.cards]
    assert "inertia" not in [c.name for c in spec.cards]


def test_describe_resolves_set_node_option1():
    column = describe_keyword("*SET_NODE_COLUMN")
    listed = describe_keyword("*SET_NODE_LIST")

    assert [f.name for f in column.card("Card 2").fields] == \
        ["NID", "A1", "A2", "A3", "A4"]
    assert [f.name for f in listed.card("Card 2").fields] == \
        [f"NID{i}" for i in range(1, 9)]


def test_describe_reports_the_name_asked_about():
    spec = describe_keyword("*MAT_001_FLUID")
    assert spec.keyword == "*MAT_001_FLUID"
    assert "*MAT_001_FLUID" not in spec.aliases
    assert "*MAT_ELASTIC" in spec.aliases


def test_describe_upper_cases_like_the_reader():
    assert describe_keyword("*node").keyword == "*NODE"


def test_describe_of_the_fallback_reports_no_cards():
    spec = describe_keyword("*UNKNOWN")
    assert spec.cards == []
    assert not spec.can_parse
    assert not spec.can_build


# ---------------------------------------------------------------------------
# describe_keyword — failures
# ---------------------------------------------------------------------------

def test_unimplemented_keyword_raises():
    with pytest.raises(KeywordNotSupported):
        describe_keyword("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE")


def test_error_suggests_near_matches():
    with pytest.raises(KeywordNotSupported, match=r"MAT_ELASTIC"):
        describe_keyword("*MAT_ELASTC")


def test_exact_match_keywords_are_not_claimed_by_prefix():
    """*MAT_ELASTIC_PLASTIC_HYDRO is MAT_010, not an option of *MAT_ELASTIC."""
    with pytest.raises(KeywordNotSupported):
        describe_keyword("*MAT_ELASTIC_PLASTIC_HYDRO")


def test_resolution_matches_the_reader(tmp_path):
    """Introspection and reading must agree on what a name means."""
    f = tmp_path / "in.k"
    f.write_text("*MAT_ELASTIC_PLASTIC_HYDRO\n         1       7.8\n")
    kw = next(iter(DynaKeywordReader(str(f)).keywords()))

    assert isinstance(kw, Unknown)          # the reader falls back
    with pytest.raises(KeywordNotSupported):
        describe_keyword("*MAT_ELASTIC_PLASTIC_HYDRO")


# ---------------------------------------------------------------------------
# Capability flags
# ---------------------------------------------------------------------------

def test_schema_driven_keyword_can_be_built():
    spec = describe_keyword("*NODE")
    assert spec.schema_driven
    assert spec.can_build
    assert not spec.custom_parse
    assert not spec.custom_write


def test_unverified_custom_write_keyword_cannot_yet_be_built():
    """A class with its own write may expect keys the schemas do not describe.

    Which keywords those are shrinks as writers get checked, so the example is
    picked from whatever is still unverified rather than named here.
    """
    from dynakw import LSDynaKeyword

    unverified = [
        s for s in supported_keywords()
        if s.custom_write
        and not LSDynaKeyword.resolve(s.keyword).builds_from_cards
    ]
    if not unverified:
        pytest.skip("every custom writer has been verified")

    for spec in unverified:
        assert not spec.schema_driven
        assert not spec.can_build


def test_verified_custom_write_keyword_can_be_built():
    """*PART writes from cards alone, and declares builds_from_cards to say so."""
    spec = describe_keyword("*PART")
    assert spec.custom_write
    assert not spec.schema_driven
    assert spec.can_build


def test_custom_parse_with_base_write_can_be_built():
    """*SET_NODE parses itself but writes through the base class."""
    spec = describe_keyword("*SET_NODE")
    assert spec.custom_parse
    assert not spec.custom_write
    assert spec.can_build


def test_flags_agree_with_the_classes():
    from dynakw import LSDynaKeyword

    for spec in supported_keywords():
        assert spec.can_parse
        assert spec.schema_driven == (not spec.custom_parse
                                      and not spec.custom_write)
        if spec.can_build and spec.custom_write:
            # Only a class that has been checked against hand-built cards may
            # claim to be buildable while writing itself.
            cls = LSDynaKeyword.resolve(spec.keyword)
            assert cls.builds_from_cards, (
                f"{spec.keyword} reports can_build with a custom write but "
                f"does not declare builds_from_cards")


# ---------------------------------------------------------------------------
# Spec helpers and the manifest
# ---------------------------------------------------------------------------

def test_field_names_skips_unstored_columns():
    spec = describe_keyword("*SECTION_SOLID")
    names = spec.field_names()
    assert "SECID" in names
    assert "ELFORM" in names
    assert not any(n.startswith("UNUSED") for n in names)


def test_card_returns_none_for_a_missing_card():
    assert describe_keyword("*NODE").card("Card 9") is None


def test_choices_are_reported():
    tc = next(f for f in describe_keyword("*NODE").card("Card 1").fields
              if f.name == "TC")
    assert tc.choices[7] == "constrained x, y and z displacements"


def test_manifest_shape():
    manifest = capability_manifest()
    assert manifest["manifest_version"] == MANIFEST_VERSION
    assert manifest["dynakw_version"] == dynakw.__version__
    assert len(manifest["keywords"]) == len(supported_keywords())


def test_manifest_is_json_serializable():
    text = json.dumps(capability_manifest())
    again = json.loads(text)
    assert again["keywords"][0]["cards"][0]["fields"][0]["name"]


def test_manifest_accepts_a_pattern():
    manifest = capability_manifest("*MAT_*")
    assert [k["keyword"] for k in manifest["keywords"]] == \
        ["*MAT_ELASTIC", "*MAT_RIGID"]


def test_pattern_treats_the_leading_star_as_a_wildcard():
    """Keyword names begin with '*', which is also the glob wildcard.

    So "*NODE" is not a way to ask for *NODE alone; bracket the star to anchor
    the name.
    """
    assert [s.keyword for s in supported_keywords("*NODE")] == \
        ["*NODE", "*SET_NODE"]
    assert [s.keyword for s in supported_keywords("[*]NODE")] == ["*NODE"]


# ---------------------------------------------------------------------------
# The report must cover what the parser really produces
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fixture", FIXTURES, ids=[f.name for f in FIXTURES])
def test_reported_cards_cover_what_is_parsed(fixture):
    """Every card and field the parser produces must be declared.

    This is what keeps the capability report honest: a keyword that grows a
    card or a column without declaring it fails here.
    """
    for kw in DynaKeywordReader(str(fixture)).keywords():
        if isinstance(kw, Unknown) or not kw.cards:
            continue

        spec = describe_keyword(kw.full_keyword)
        declared = {c.name: {f.name for f in c.fields} for c in spec.cards}

        for card_name, card in kw.cards.items():
            assert card_name in declared, \
                f"{kw.full_keyword} produced undeclared card {card_name!r}"
            undeclared = set(card) - declared[card_name]
            assert not undeclared, (
                f"{kw.full_keyword} {card_name} produced undeclared fields "
                f"{sorted(undeclared)}")
