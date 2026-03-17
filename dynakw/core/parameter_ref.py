"""ParameterRef: represents an &VARNAME reference in a data field."""

from dataclasses import dataclass


@dataclass
class ParameterRef:
    """A reference to a *PARAMETER variable in a data field.

    In LS-DYNA files, parameter references appear as ``&VARNAME`` inside
    numeric or string card fields.  Instead of attempting (and failing) to
    convert the field to int or float, the parser stores a ``ParameterRef``
    object so that the reference is preserved faithfully on round-trip.

    Example::

        *MAT_ELASTIC
        $      MID        RO         E        PR
                 1     7.85e-9    &Emod    &PRval

    After parsing, ``kw.cards['Card 1']['E'][0]`` is
    ``ParameterRef('Emod')`` rather than raising a ValueError.
    """

    name: str
    """Variable name without the leading ``&``."""

    def __str__(self) -> str:
        return f"&{self.name}"

    def __repr__(self) -> str:
        return f"ParameterRef({self.name!r})"
