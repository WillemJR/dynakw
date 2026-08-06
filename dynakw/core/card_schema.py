"""Declarative card schema for LS-DYNA keywords.

A keyword declares its card layout with these dataclasses.  The declaration is
the single source of truth: it drives parsing and writing (see
``LSDynaKeyword``), and it is also what introspection reports to callers that
want to know what the library can read and build.  Any descriptive metadata
therefore belongs here rather than in a separate table that could drift.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union


@dataclass
class CardField:
    """One field (column) in a card.

    Attributes:
        name: Field name as used in ``keyword.cards[card][name]``.  Follows the
            LS-DYNA manual's variable name (``NID``, ``SECID``, ``ELFORM``).
        type: ``'I'`` (int), ``'F'`` (float) or ``'A'`` (string).
        width: Field width in characters.
        default: Value used when the field is absent or blank.
        header_name: Label shown in the ``$  …`` comment header line.
            Defaults to ``name``.
        description: What the field means, per the LS-DYNA manual.  One line.
        units: Dimension of the quantity (``'length'``, ``'stress'``,
            ``'mass/volume'``, …) or None for dimensionless/ID fields.
            LS-DYNA itself is unit-agnostic; this is a hint for callers that
            convert between unit systems.
        required: True when the manual gives no default and the field must be
            supplied.  Advisory for readers; enforced when building a keyword
            from data.
        choices: Mapping of accepted value to meaning, for fields with a short,
            closed set of values.  Left None when the enumeration is long or
            open-ended — a partial mapping would be worse than none; the
            description points at the manual instead.
        stored: False for a column that exists in the fixed-width layout but is
            not kept in ``keyword.cards`` (reserved/unused columns).  Such a
            field holds the column position so that later fields land in the
            right place, but has no entry in the card dict.
    """

    name: str
    type: str                      # 'I' = int, 'F' = float, 'A' = string
    width: int = 10                # field width in characters
    default: Any = 0
    header_name: Optional[str] = None
    description: str = ""
    units: Optional[str] = None
    required: bool = False
    choices: Optional[Dict[Any, str]] = None
    stored: bool = True


@dataclass
class CardSchema:
    """One card in a keyword.

    Attributes:
        name: Card key in ``keyword.cards`` (``'Card 1'``, ``'Card 2'``, …).
        fields: The card's fields, in column order.
        repeating: True when the card spans one line per node/element/row.
        condition: ``condition(kw) -> bool`` — whether this card is present for
            a given keyword instance.  Evaluated against an instance, so it can
            read option flags set in ``__init__``.  It must be safe to call on
            an instance with no parsed data, because introspection resolves a
            keyword variant's cards by probing an empty instance.  For a card
            whose presence depends on values parsed from an earlier card, give
            ``condition_doc`` alone and leave this None.
        write_header: True to emit a ``$  col1  col2  …`` comment line before
            the data.
        description: What the card holds.  One line.
        condition_doc: Human-readable form of ``condition`` ("only for the
            _FLUID option").  A callable is opaque to a caller reading the
            schema, so state the rule in words as well.
        dynamic: True when the field list is not fixed — the number of columns
            or rows depends on data parsed earlier in the same keyword (for
            example a count field on a preceding card).  ``fields`` then
            describes one representative line, not the whole card.
    """

    name: str
    fields: List[CardField]
    repeating: bool = False
    condition: Optional[Callable] = None
    write_header: bool = False
    description: str = ""
    condition_doc: str = ""
    dynamic: bool = False


@dataclass
class CardGroup:
    """A group of CardSchemas that are written and parsed in interleaved row order.

    Write order for a group with N active schemas and M rows::

        all active schema headers (once, in schema order)
        row 0: one data line per active schema
        row 1: one data line per active schema
        ...

    Parse order: the data lines are assumed to alternate schema-by-schema with a
    fixed stride equal to the number of active schemas::

        line 0    -> schema 0, row 0
        line 1    -> schema 1, row 0
        ...
        line N    -> schema 0, row 1
        line N+1  -> schema 1, row 1
        ...
    """
    schemas: List[CardSchema]
    description: str = ""
