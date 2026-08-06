"""Schema metadata tests.

Covers the descriptive metadata carried by the card schemas — the data that
introspection reports to callers, and that the deck-building API will validate
against.  Metadata that nothing checks rots silently, so these tests enforce it
for every registered keyword.

Covers:
- Every keyword class carries a description and a manual section
- Every keyword declares its card layout in ``card_schemas``, including the
  classes that override ``_parse_raw_data`` and ``write``
- Every field carries a description
- Every conditional card explains its condition in words
- Every condition is safe to evaluate on a keyword instance with no parsed
  data, which is how a keyword variant's cards are resolved
- ``choices`` keys are valid values for the field's declared type
"""

import pytest
import sys
sys.path.append('.')

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.keywords.UNKNOWN import Unknown


LSDynaKeyword.discover_keywords()

# Registered keyword name -> class.  Names are what a file may contain, so
# several names can map to one class (aliases and option variants).
REGISTERED = sorted(LSDynaKeyword.KEYWORD_MAP.items())

# One entry per class, for the checks that are about the class rather than the
# name it was reached by.
CLASSES = sorted({cls for _, cls in REGISTERED}, key=lambda c: c.__name__)

# Unknown is raw-text passthrough: it has no card structure by design.
SCHEMA_CLASSES = [cls for cls in CLASSES if cls is not Unknown]


def _ids(classes):
    return [c.__name__ for c in classes]


# ---------------------------------------------------------------------------
# Keyword-level metadata
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cls", CLASSES, ids=_ids(CLASSES))
def test_keyword_has_description(cls):
    assert cls.description.strip(), (
        f"{cls.__name__} has no description; introspection would report the "
        f"keyword without saying what it is for")


@pytest.mark.parametrize("cls", SCHEMA_CLASSES, ids=_ids(SCHEMA_CLASSES))
def test_keyword_has_manual_section(cls):
    assert cls.manual_section.strip(), (
        f"{cls.__name__} does not say where it is documented")


@pytest.mark.parametrize("cls", SCHEMA_CLASSES, ids=_ids(SCHEMA_CLASSES))
def test_keyword_declares_card_schemas(cls):
    """Card layout must be declared even when parse/write are overridden.

    The base implementations are the only consumers of ``card_schemas``, so for
    a class that overrides both, the list is inert — but without it the layout
    is invisible to introspection.
    """
    assert cls.card_schemas, (
        f"{cls.__name__} declares no card_schemas, so its card layout cannot "
        f"be discovered")


def test_unknown_declares_no_schema():
    """Unknown must stay a raw-text passthrough (REFACTORING_PLAN, "What NOT to do")."""
    assert not Unknown.card_schemas
    assert Unknown.description.strip()


# ---------------------------------------------------------------------------
# Card and field metadata
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cls", SCHEMA_CLASSES, ids=_ids(SCHEMA_CLASSES))
def test_every_field_has_a_description(cls):
    missing = [
        f"{schema.name}.{field.name}"
        for schema in cls.card_schemas
        for field in schema.fields
        if not field.description.strip()
    ]
    assert not missing, f"{cls.__name__} fields without a description: {missing}"


@pytest.mark.parametrize("cls", SCHEMA_CLASSES, ids=_ids(SCHEMA_CLASSES))
def test_every_card_has_a_description(cls):
    missing = [s.name for s in cls.card_schemas if not s.description.strip()]
    assert not missing, f"{cls.__name__} cards without a description: {missing}"


@pytest.mark.parametrize("cls", SCHEMA_CLASSES, ids=_ids(SCHEMA_CLASSES))
def test_conditional_cards_explain_themselves(cls):
    """A callable condition is opaque to a caller reading the schema.

    Cards that are not always present must state the rule in words, whether the
    rule is expressed as a condition or only documented (as for cards selected
    by values parsed from an earlier card).
    """
    missing = [
        s.name for s in cls.card_schemas
        if s.condition is not None and not s.condition_doc.strip()
    ]
    assert not missing, (
        f"{cls.__name__} conditional cards without condition_doc: {missing}")


@pytest.mark.parametrize("cls", SCHEMA_CLASSES, ids=_ids(SCHEMA_CLASSES))
def test_field_types_are_valid(cls):
    bad = [
        f"{schema.name}.{field.name}={field.type!r}"
        for schema in cls.card_schemas
        for field in schema.fields
        if field.type not in ("I", "F", "A")
    ]
    assert not bad, f"{cls.__name__} fields with an unknown type: {bad}"


@pytest.mark.parametrize("cls", SCHEMA_CLASSES, ids=_ids(SCHEMA_CLASSES))
def test_choices_match_field_type(cls):
    """A choices key must be a value the field could actually hold."""
    expected = {"I": int, "F": float, "A": str}
    bad = []
    for schema in cls.card_schemas:
        for field in schema.fields:
            if not field.choices:
                continue
            for key in field.choices:
                if not isinstance(key, expected[field.type]):
                    bad.append(f"{schema.name}.{field.name}: {key!r}")
    assert not bad, f"{cls.__name__} choices keys of the wrong type: {bad}"


# ---------------------------------------------------------------------------
# Conditions must be safe to probe
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,cls", REGISTERED, ids=[n for n, _ in REGISTERED])
def test_empty_instance_can_be_constructed(name, cls):
    """Every registered name must build without raw data.

    Introspection resolves which cards a keyword variant has by constructing an
    empty instance and evaluating the conditions against it.  Deck building
    starts the same way.
    """
    kw = cls(name)
    assert kw.cards == {}


@pytest.mark.parametrize("name,cls", REGISTERED, ids=[n for n, _ in REGISTERED])
def test_conditions_are_safe_on_an_empty_instance(name, cls):
    """A condition must not depend on data parsed from the file.

    Conditions may read option flags set in ``__init__``; they may not read
    ``self.cards``, which is empty at probe time.  Cards whose presence depends
    on parsed values carry ``condition_doc`` alone.
    """
    probe = cls(name)
    for schema in cls.card_schemas:
        if schema.condition is None:
            continue
        result = schema.condition(probe)
        assert isinstance(result, bool), (
            f"{cls.__name__} {schema.name}: condition returned "
            f"{type(result).__name__}, expected bool")


def test_variant_conditions_select_different_cards():
    """The probe mechanism must actually discriminate between variants.

    *MAT_ELASTIC and *MAT_ELASTIC_FLUID share a class but have different cards;
    resolving conditions against an empty instance must tell them apart.
    """
    from dynakw.keywords.MAT_ELASTIC import MatElastic

    def active(name):
        probe = MatElastic(name)
        return [s for s in MatElastic.card_schemas
                if s.condition is None or s.condition(probe)]

    solid = active("*MAT_ELASTIC")
    fluid = active("*MAT_ELASTIC_FLUID")

    assert [s.name for s in solid] == ["Card 1"]
    assert [s.name for s in fluid] == ["Card 1", "Card 2"]

    # The two Card 1 variants differ: the fluid one drops E, PR, DA and DB.
    assert [f.name for f in solid[0].fields] == \
        ["MID", "RO", "E", "PR", "DA", "DB", "K"]
    assert [f.name for f in fluid[0].fields] == ["MID", "RO", "K"]
