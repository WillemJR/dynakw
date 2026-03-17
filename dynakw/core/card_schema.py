"""Declarative card schema for LS-DYNA keywords."""

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Union


@dataclass
class CardField:
    name: str
    type: str                      # 'I' = int, 'F' = float, 'A' = string
    width: int = 10                # field width in characters
    default: Any = 0
    header_name: Optional[str] = None
    # header_name: override shown in the "$  ..." comment header (default: same as name)


@dataclass
class CardSchema:
    name: str
    fields: List[CardField]
    repeating: bool = False
    condition: Optional[Callable] = None
    # condition(kw) -> bool: whether this card is present for this keyword instance
    write_header: bool = False
    # write_header=True: emit a "$  col1  col2  ..." comment line before the data


@dataclass
class CardGroup:
    """A group of CardSchemas that are written and parsed in interleaved row order.

    Write order for a group with N active schemas and M rows:
        1. All active schema headers (once, in schema order)
        2. For row 0: one data line per active schema
        3. For row 1: one data line per active schema
        ...

    Parse order: the data lines are assumed to alternate schema-by-schema with a
    fixed stride equal to the number of active schemas:
        line 0 → schema 0, row 0
        line 1 → schema 1, row 0
        ...
        line N → schema 0, row 1
        line N+1 → schema 1, row 1
        ...
    """
    schemas: List[CardSchema]
