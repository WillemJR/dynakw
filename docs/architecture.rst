Architecture
============

``dynakw`` is built around one idea: **a keyword declares its card layout, and
everything else is derived from that declaration.**  Reading, writing and the
capability report all come from the same ``CardSchema`` objects, so they cannot
disagree with one another.

.. code-block:: text

   dynakw/
   ├── core/
   │   ├── card_schema.py   # CardField, CardSchema, CardGroup — the declarations
   │   ├── enums.py         # KeywordType
   │   ├── introspect.py    # Capability reporting
   │   ├── keyword_file.py  # DynaKeywordReader: file I/O and dispatch
   │   └── parameter_ref.py # ParameterRef: &VAR references in data fields
   ├── keywords/
   │   ├── lsdyna_keyword.py  # LSDynaKeyword base class
   │   └── ...                # One module per keyword
   ├── manifest.py          # CLI: python -m dynakw.manifest
   └── utils/
       └── format_parser.py # LS-DYNA fixed-width format


From file to object and back
----------------------------

1. **Reading** — :class:`~dynakw.DynaKeywordReader` splits the file into blocks
   on ``*`` lines, following ``*INCLUDE`` when asked to.
2. **Dispatching** — the block's keyword line is resolved by
   :meth:`~dynakw.LSDynaKeyword.resolve`, which takes the longest registered
   name that is a prefix of the line.  Introspection resolves names through the
   same method, so both always agree about what a name means.
3. **Parsing** — the matching class turns the raw lines into numpy arrays in
   ``keyword.cards``.  When the class declares ``card_schemas``, the base class
   does this automatically.
4. **Manipulation** — ``keyword.cards`` is read and edited directly.
5. **Writing** — ``write()`` formats ``cards`` back into fixed-width columns,
   automatically for schema-driven keywords.

An unrecognised keyword becomes an ``Unknown`` block that keeps its text
verbatim, comments included, so reading and writing a file never loses data.


The declarative card schema
---------------------------

A card layout is described with two dataclasses in
``dynakw.core.card_schema``.  They carry the fixed-width layout *and* the
documentation of what each field means, because a separate table of
descriptions would drift away from the code.

``CardField``
~~~~~~~~~~~~~

One field, i.e. one column of a card.

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - Attribute
     - Meaning
   * - ``name``
     - Field name as used in ``cards[card][name]``.  Follows the manual's
       variable name (``NID``, ``SECID``, ``ELFORM``).
   * - ``type``
     - ``'I'`` (int), ``'F'`` (float) or ``'A'`` (string).  Drives the numpy
       dtype: ``int32``, ``float64``, ``object``.
   * - ``width``
     - Field width in characters.
   * - ``default``
     - Value used when the field is blank or absent.
   * - ``header_name``
     - Label for the ``$`` comment header line, when it differs from ``name``.
   * - ``description``
     - What the field means, per the LS-DYNA manual.
   * - ``units``
     - Dimension of the quantity (``'length'``, ``'stress'``,
       ``'mass/volume'``) or ``None``.  LS-DYNA is unit-agnostic; this is a hint
       for callers converting between unit systems.
   * - ``required``
     - True when the manual gives no default.
   * - ``choices``
     - Mapping of accepted value to meaning, for fields with a short, closed
       set of values.  Left ``None`` when the enumeration is long — a partial
       mapping would be worse than none, and the description points at the
       manual instead.
   * - ``stored``
     - False for a reserved column that holds a position in the layout but has
       no entry in ``cards``.

``CardSchema``
~~~~~~~~~~~~~~

One card of a keyword.

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - Attribute
     - Meaning
   * - ``name``
     - Card key in ``cards``: ``'Card 1'``, ``'Card 2'``, …
   * - ``fields``
     - The fields, in column order.
   * - ``repeating``
     - True when the card spans one line per node, element or row.
   * - ``condition``
     - ``condition(kw) -> bool``, whether the card is present for a given
       keyword instance.  See the warning below.
   * - ``condition_doc``
     - The same rule in words.  A callable is opaque to anyone reading the
       schema, so conditional cards state their rule in prose as well.
   * - ``write_header``
     - Emit a ``$  col1  col2 …`` comment line before the data.
   * - ``description``
     - What the card holds.
   * - ``dynamic``
     - True when the field list is not fixed — the number of columns or rows
       depends on data parsed earlier in the same keyword — in which case
       ``fields`` describes one representative line.

.. warning::

   A ``condition`` must be safe to call on an instance with **no parsed data**.
   Introspection works out which cards a keyword variant has by probing an
   empty instance, so a condition may read option flags set in ``__init__`` but
   must not read ``self.cards``.  For a card whose presence depends on a value
   parsed from an earlier card — say ``ICOMP = 1`` on Card 1 — give
   ``condition_doc`` alone and leave ``condition`` as ``None``.


Keyword options
---------------

The suffix after the base keyword name is split on ``_`` into
``keyword.options``, which means a plain membership test cannot see an option
whose own name contains an underscore:  the options of
``*PART_ATTACHMENT_NODES`` are ``['ATTACHMENT', 'NODES']``.

Use :meth:`~dynakw.LSDynaKeyword.has_option`, which matches a contiguous run of
tokens:

.. code-block:: python

   kw.has_option("ATTACHMENT_NODES")   # True for *PART_ATTACHMENT_NODES
   kw.has_option("ID")                 # False for *..._RIGID — token boundaries hold

One option name can be a prefix of another: for ``*ELEMENT_SHELL_COMPOSITE_LONG``
both ``has_option("COMPOSITE")`` and ``has_option("COMPOSITE_LONG")`` are True,
so alternatives must test the longer name first.


Capability introspection
------------------------

Code that *generates* decks needs to know which keywords exist and what each
card holds.  :func:`~dynakw.supported_keywords`,
:func:`~dynakw.describe_keyword` and :func:`~dynakw.capability_manifest` report
exactly that, read straight from the schemas above.

:func:`~dynakw.describe_keyword` describes a *concrete variant*, with the option
conditions resolved:

.. code-block:: python

   import dynakw

   dynakw.describe_keyword("*MAT_ELASTIC")        # Card 1 only, 7 fields
   dynakw.describe_keyword("*MAT_ELASTIC_FLUID")  # Card 1 (3 fields) + Card 2

The flags on :class:`~dynakw.KeywordSpec` say what may be done with a keyword:

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - Flag
     - Meaning
   * - ``can_parse``
     - A block with this name is parsed into cards.  False only for the
       raw-text fallback.
   * - ``can_build``
     - A ``cards`` dict shaped by the schemas writes correctly.  True when the
       class uses the base ``write``, or declares ``builds_from_cards``.
   * - ``schema_driven``
     - Both parsing and writing come from the base class.
   * - ``custom_parse``, ``custom_write``
     - Which half the class overrides.

``can_build`` is deliberately conservative.  A class using the base ``write``
gets it for free, because that writer renders from ``cards`` and the schemas
alone.  A class with its own ``write`` may expect keys the schemas do not
describe, so it reports False until someone checks --- at which point the class
sets ``builds_from_cards = True``, backed by a test that builds an instance from
data, writes it and reads it back.  ``*PART`` is the worked example: see
``test/test_part_build.py``.

Note that ``can_build`` is about *constructing* a keyword from data.  Writing
back a keyword that was read from a file works for every keyword, whatever this
flag says.

The whole report is available as a JSON-serializable dict, versioned with
``manifest_version`` and ``dynakw_version``, for consumers outside this process:

.. code-block:: bash

   python -m dynakw.manifest --format json > dynakw_capabilities.json


Data storage
------------

Keyword data lives in ``cards``, a two-level dict of card name to field name to
numpy array:

.. code-block:: python

   nids = node_kw.cards['Card 1']['NID']   # (n_nodes,)   int32
   xs   = node_kw.cards['Card 1']['X']     # (n_nodes,)   float64

Composite element cards use 2D arrays, one row per element and one column per
layer, with a companion count column:

.. code-block:: python

   mid = shell_kw.cards['Card 6']['MID']       # (n_elems, max_layers)
   n   = shell_kw.cards['Card 6']['N_LAYERS']  # (n_elems,)

A field holding ``&VAR`` is stored as a :class:`~dynakw.ParameterRef` and the
column widens to ``dtype=object``, so the reference survives a read/write cycle
instead of being flattened to a number.


Error handling
--------------

The library degrades rather than failing:

* An unrecognised keyword becomes ``Unknown`` and keeps its text verbatim.
* A block that raises while parsing is logged and returned as ``Unknown``; the
  rest of the file still parses.
* A field that will not convert to its declared type is kept as the raw string.

``dynakw`` uses the standard ``logging`` module and installs no handlers of its
own, so nothing is printed unless the application asks for it:

.. code-block:: python

   import logging
   logging.basicConfig(level=logging.WARNING)
