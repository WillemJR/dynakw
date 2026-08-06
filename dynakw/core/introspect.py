"""Capability introspection: what this library can read and build.

Everything reported here is derived from the ``CardSchema`` declarations that
also drive parsing and writing, so a capability report cannot drift from what
the library actually does.  Nothing is hand-maintained.

Typical use, from a tool that generates decks::

    import dynakw

    have = {s.keyword: s for s in dynakw.supported_keywords()}
    missing = [k for k in REQUIRED if k not in have]

and to inspect one concrete variant::

    spec = dynakw.describe_keyword("*MAT_ELASTIC_FLUID")
    fields = {f.name for c in spec.cards for f in c.fields}
"""

from dataclasses import dataclass, asdict
from fnmatch import fnmatch
from typing import Any, Dict, List, Optional

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.keywords.UNKNOWN import Unknown

# Bumped when the shape of the manifest changes, so a consumer can tell whether
# it understands the document it has been handed.
MANIFEST_VERSION = 1


class KeywordNotSupported(LookupError):
    """Raised for a keyword name this library does not implement."""


@dataclass
class FieldSpec:
    """One field of a card."""

    name: str
    type: str                      # 'I' = int, 'F' = float, 'A' = string
    width: int
    default: Any
    description: str
    units: Optional[str]
    required: bool
    choices: Optional[Dict[Any, str]]
    stored: bool
    """False for a column that holds a position in the fixed-width layout but
    has no entry in ``keyword.cards``."""


@dataclass
class CardSpec:
    """One card of a keyword."""

    name: str
    description: str
    repeating: bool
    conditional: bool
    """True when the card is not present in every variant of the keyword."""
    condition_doc: str
    """When the card applies, in words.  Empty for an unconditional card."""
    dynamic: bool
    """True when the field list is not fixed --- the number of columns or rows
    depends on data parsed earlier in the same keyword, and ``fields``
    describes one representative line."""
    fields: List[FieldSpec]


@dataclass
class KeywordSpec:
    """What the library knows about one keyword."""

    keyword: str
    """The name this spec describes.  For ``describe_keyword`` it is the name
    asked about, so the cards are those of that concrete variant."""
    aliases: List[str]
    description: str
    manual_section: str
    cards: List[CardSpec]

    can_parse: bool
    """Whether a block with this name is parsed into cards.  False only for the
    raw-text fallback."""

    can_build: bool
    """Whether a keyword of this type can be populated from data and written.

    True when the class uses the base ``write``, so a ``cards`` dict shaped by
    the schemas below renders correctly, or when a class with its own ``write``
    declares ``builds_from_cards`` --- a claim that the writer has been checked
    against hand-built cards and is covered by a test.  Any other class with a
    custom ``write`` may expect keys the schemas do not describe, and is
    reported False until someone checks."""

    schema_driven: bool
    """True when both parsing and writing are provided by the base class."""

    custom_parse: bool
    custom_write: bool

    def field_names(self) -> List[str]:
        """Every stored field name in this keyword, in card order."""
        return [f.name for c in self.cards for f in c.fields if f.stored]

    def card(self, name: str) -> Optional[CardSpec]:
        """The card called *name*, or None."""
        for c in self.cards:
            if c.name == name:
                return c
        return None

    def to_dict(self) -> dict:
        """A plain, JSON-serializable dict."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Building specs from the schema declarations
# ---------------------------------------------------------------------------

def _field_spec(f) -> FieldSpec:
    return FieldSpec(
        name=f.name,
        type=f.type,
        width=f.width,
        default=f.default,
        description=f.description,
        units=f.units,
        required=f.required,
        choices=dict(f.choices) if f.choices else None,
        stored=f.stored,
    )


def _card_spec(schema) -> CardSpec:
    return CardSpec(
        name=schema.name,
        description=schema.description,
        repeating=schema.repeating,
        conditional=schema.condition is not None or bool(schema.condition_doc),
        condition_doc=schema.condition_doc,
        dynamic=schema.dynamic,
        fields=[_field_spec(f) for f in schema.fields],
    )


def _resolve(name: str):
    """The class handling *name*, or raise KeywordNotSupported."""
    cls = LSDynaKeyword.resolve(name)
    if cls is None:
        near = _near_matches(name)
        hint = f"  Did you mean: {', '.join(near)}?" if near else ""
        raise KeywordNotSupported(f"{name.strip()} is not implemented.{hint}")
    return cls


def _near_matches(name: str, limit: int = 3) -> List[str]:
    """Registered names sharing a leading run with *name*, longest first."""
    target = name.strip().upper().lstrip('*')
    scored = []
    for registered in LSDynaKeyword.KEYWORD_MAP:
        candidate = registered.lstrip('*')
        shared = 0
        for a, b in zip(target, candidate):
            if a != b:
                break
            shared += 1
        if shared >= 3:
            scored.append((shared, registered))
    scored.sort(key=lambda s: (-s[0], s[1]))
    return [n for _, n in scored[:limit]]


def _active_schemas(cls, name: str) -> List:
    """The schemas that apply to the variant *name*.

    Conditions are resolved against an instance built with no raw data: option
    flags are set from the keyword name in ``__init__``, so a condition can see
    them, while ``cards`` is empty.  A card selected by values parsed from an
    earlier card therefore carries ``condition_doc`` and no condition, and is
    always reported.
    """
    probe = cls(name)
    return [s for s in cls.card_schemas
            if s.condition is None or s.condition(probe)]


def _spec_for(cls, name: str) -> KeywordSpec:
    custom_parse = cls._parse_raw_data is not LSDynaKeyword._parse_raw_data
    custom_write = cls.write is not LSDynaKeyword.write

    # Every other registered name for the same keyword.  The primary name is
    # included, so a caller who asked about *MAT_001_FLUID is told the keyword
    # is also known as *MAT_ELASTIC; the name asked about is not repeated back
    # as an alias of itself.
    all_names = [cls.keyword_string] + list(getattr(cls, "keyword_aliases", []))

    return KeywordSpec(
        keyword=name,
        aliases=[n for n in dict.fromkeys(all_names) if n != name],
        description=cls.description,
        manual_section=cls.manual_section,
        cards=[_card_spec(s) for s in _active_schemas(cls, name)],
        can_parse=cls is not Unknown,
        can_build=bool(cls.card_schemas)
                  and (not custom_write or cls.builds_from_cards),
        schema_driven=not custom_parse and not custom_write,
        custom_parse=custom_parse,
        custom_write=custom_write,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def describe_keyword(name: str) -> KeywordSpec:
    """Describe one concrete keyword variant.

    The cards reported are those of the variant named, with the option
    conditions resolved: ``*MAT_ELASTIC`` reports a seven-field Card 1 and no
    Card 2, while ``*MAT_ELASTIC_FLUID`` reports a three-field Card 1 and a
    Card 2.

    Args:
        name: A full keyword line, e.g. ``"*ELEMENT_SHELL_COMPOSITE_LONG"``.
            Resolved exactly as when reading a file.

    Returns:
        A :class:`KeywordSpec` for that variant.

    Raises:
        KeywordNotSupported: if no class handles the name.
    """
    cls = _resolve(name)
    # Upper-cased for the same reason the reader upper-cases a keyword line:
    # the base type lookup matches the KeywordType enum names.
    return _spec_for(cls, name.strip().rstrip('+-% ').upper())


def supported_keywords(pattern: str = None) -> List[KeywordSpec]:
    """Every implemented keyword, one spec per keyword class.

    Each spec describes the keyword under its primary name, so option-dependent
    cards are reported as they are for that base variant; use
    :func:`describe_keyword` for a particular variant.  The raw-text fallback
    (``*UNKNOWN``) is not a keyword anyone would ask for and is excluded; it is
    still reachable through :func:`describe_keyword`.

    Args:
        pattern: Optional fnmatch pattern, matched against the primary name and
            the aliases, e.g. ``"*SET_*"``.  Note that every keyword name
            begins with ``*``, which is also the glob wildcard, so ``"*NODE"``
            matches ``*SET_NODE`` as well as ``*NODE``.  Anchor the name with
            the literal star --- ``"[*]NODE"`` --- to match only ``*NODE``.

    Returns:
        Specs sorted by keyword name.
    """
    seen = {}
    for cls in LSDynaKeyword.KEYWORD_MAP.values():
        if cls is Unknown:
            continue
        seen.setdefault(cls.keyword_string, cls)

    specs = [_spec_for(cls, name) for name, cls in seen.items()]

    if pattern:
        specs = [
            s for s in specs
            if fnmatch(s.keyword, pattern)
            or any(fnmatch(a, pattern) for a in s.aliases)
        ]

    return sorted(specs, key=lambda s: s.keyword)


def capability_manifest(pattern: str = None) -> dict:
    """The whole capability report, as a JSON-serializable dict.

    Intended for a consumer that is not running in this process: write it to a
    file with ``python -m dynakw.manifest`` and read it from the other side.

    Args:
        pattern: Optional fnmatch pattern, as for :func:`supported_keywords`.

    Returns:
        ``{"manifest_version", "dynakw_version", "keywords": [...]}``.
    """
    from dynakw import __version__

    return {
        "manifest_version": MANIFEST_VERSION,
        "dynakw_version": __version__,
        "keywords": [s.to_dict() for s in supported_keywords(pattern)],
    }
