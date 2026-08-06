# Architecture and Logic

The `dynakw` library is structured to be modular and extensible. The main components are organized as follows:

```
dynakw/
├── core/              # Core parsing and data structures
│   ├── card_schema.py # CardField, CardSchema, CardGroup dataclasses
│   ├── enums.py       # Enumerations for KeywordType
│   ├── introspect.py  # Capability reporting: what the library can read and build
│   ├── keyword_file.py# Main class for reading and writing LS-DYNA keyword files
│   └── parameter_ref.py # ParameterRef: represents &VAR references in data fields
├── keywords/          # Keyword-specific implementations
│   ├── lsdyna_keyword.py # Abstract base class for all keywords
│   └── ...            # Individual keyword files (e.g., BOUNDARY_PRESCRIBED_MOTION.py)
├── manifest.py        # CLI: python -m dynakw.manifest
└── utils/             # Utilities
    └── format_parser.py # Parser for LS-DYNA's fixed-width format
```

## Core Components

*   **`dynakw/core/card_schema.py`**: Defines the declarative schema dataclasses used to
    describe keyword card layouts.  The declaration is the single source of truth: it
    drives parsing and writing, and it is also what introspection reports, so
    descriptive metadata belongs here rather than in a separate table that could drift.
    *   `CardField(name, type, width, default, header_name, description, units,
        required, choices, stored)` — one field in a card.  `type` is `'I'` (int),
        `'F'` (float), or `'A'` (string).  `header_name` overrides the label shown in
        the `$  …` comment header line (default: same as `name`).  `description` states
        what the field means, per the manual.  `units` gives the dimension of the
        quantity (`'length'`, `'stress'`, …) or None — LS-DYNA is unit-agnostic, so this
        is a hint for callers converting between unit systems.  `required=True` marks a
        field the manual gives no default for.  `choices` maps accepted value to meaning
        for fields with a short, closed value set (left None when the enumeration is
        long — a partial mapping would be worse than none).  `stored=False` marks a
        column that holds a position in the fixed-width layout but has no entry in
        `cards` (reserved/unused columns).
    *   `CardSchema(name, fields, repeating, condition, write_header, description,
        condition_doc, dynamic)` — one card in a keyword.  `repeating=True` means the
        card spans one line per element/node.  `condition(kw) -> bool` makes the card
        conditional on keyword instance state; it **must be safe to call on an instance
        with no parsed data**, because introspection resolves a variant's cards by
        probing an empty instance — for a card whose presence depends on values parsed
        from an earlier card, give `condition_doc` alone and leave `condition` None.
        `condition_doc` states the rule in words, since a callable is opaque to a caller
        reading the schema.  `write_header=True` emits a `$  col1  col2  …` comment line
        before the data.  `dynamic=True` marks a card whose field list is not fixed
        (column or row count depends on data parsed earlier); `fields` then describes one
        representative line.
    *   `CardGroup(schemas)` — a group of `CardSchema` objects written and parsed in
        interleaved row order (one row per schema per element, all headers first).

*   **`dynakw/core/introspect.py`**: Reports what the library can read and build.
    Everything it returns is derived from the same `CardSchema` declarations that drive
    parsing and writing, so a capability report cannot drift from actual behaviour.  See
    [Capability introspection](#capability-introspection) below.

*   **`dynakw/core/enums.py`**: Defines the `KeywordType` enumeration, which provides a
    standardized way to identify all supported LS-DYNA keywords.

*   **`dynakw/core/keyword_file.py`**: Contains the `DynaKeywordReader` class, which is
    the main entry point for reading and writing LS-DYNA keyword files.  It handles file
    I/O, including following `*INCLUDE` directives, splits the file into keyword blocks,
    and dispatches each block to the appropriate keyword class via `LSDynaKeyword.KEYWORD_MAP`.

*   **`dynakw/core/parameter_ref.py`**: Contains `ParameterRef(name)`, a dataclass that
    represents an `&VARNAME` parameter reference in a data field.  `str(ref)` returns
    `"&name"`.  Fields containing `&` are stored as `ParameterRef` objects rather than
    raising a `ValueError`, so round-trip fidelity is preserved.

*   **`dynakw/utils/format_parser.py`**: Contains the `FormatParser` class, a utility for
    handling the fixed-width format of LS-DYNA card fields.  It can parse lines into data
    (integers, floats, strings, or `ParameterRef`) and format data back into fixed-width
    strings for writing.

## Keyword Implementation

*   **`dynakw/keywords/lsdyna_keyword.py`**: Contains the abstract base class
    `LSDynaKeyword`.  All keyword classes inherit from this class.

    *   `__init_subclass__(...)`: Automatically registers every subclass in `KEYWORD_MAP`
        using its `keyword_string` and `keyword_aliases`.  No manual registration needed.
    *   `keyword_string`: Class attribute — the primary keyword string (e.g. `"*NODE"`).
    *   `keyword_aliases`: Optional list of alternative names for the same keyword.
    *   `description` / `manual_section`: Class attributes — what the keyword does and
        where it is documented (e.g. `"Vol I, *NODE"`).  Reported by introspection.
    *   `has_option(name)`: **Use this to test for a keyword option, not
        `name in self.options`.**  `self.options` is the option suffix split on `_`, so
        the options of `*PART_ATTACHMENT_NODES` are `['ATTACHMENT', 'NODES']` and a
        membership test for `'ATTACHMENT_NODES'` silently fails.  `has_option` matches a
        contiguous run of tokens, so multi-token names work while token boundaries are
        respected (`has_option("ID")` is False for `*BOUNDARY_PRESCRIBED_MOTION_RIGID`).
        Note one option name can be a prefix of another — for
        `*ELEMENT_SHELL_COMPOSITE_LONG` both `has_option("COMPOSITE")` and
        `has_option("COMPOSITE_LONG")` are True, so alternatives must test the longer
        name first.
    *   `card_schemas`: Class attribute — list of `CardSchema` objects.  When set, the base
        class provides default `_parse_raw_data` and `write` implementations automatically.
        **This is the preferred way to implement new keywords.**
        A class that overrides *both* `_parse_raw_data` and `write` should still declare
        its schemas here: the base implementations are the only consumers of the list, so
        it is inert for such a class, but without it the card layout is invisible to
        introspection.
    *   `card_groups`: Class attribute — list of `CardGroup` objects for interleaved
        (per-element) parse/write.  Takes precedence over `card_schemas` in the default
        implementations.
    *   `_parse_raw_data(raw_lines)`: Override only when the card layout cannot be
        expressed with `card_schemas`/`card_groups` (e.g. per-row conditional cards,
        variable-length composite layers).
    *   `write(file_obj)`: Override together with `_parse_raw_data` when custom logic is
        needed.

### Adding a new keyword (typical case)

Most keywords require only a class declaration — no `_parse_raw_data` or `write` needed:

```python
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema

class MyNewKeyword(LSDynaKeyword):
    keyword_string = "*MY_NEW_KEYWORD"

    description = "One or two sentences on what the keyword does."
    manual_section = "Vol I, *MY_NEW_KEYWORD"

    card_schemas = [
        CardSchema("Card 1", [
            CardField("ID",    "I", width=10,
                      description="Definition ID", required=True),
            CardField("PARAM", "F", width=10,
                      description="Scale factor applied to …"),
            CardField("NAME",  "A", width=10,
                      description="Optional label"),
        ], write_header=True,
           description="What this card holds."),

        CardSchema("Card 2", [
            CardField("VAL1", "F", width=10,
                      description="…", units="length"),
            CardField("VAL2", "F", width=10,
                      description="…", units="length"),
        ], write_header=True,
           description="What this card holds."),
    ]
```

`test/test_schema_metadata.py` enforces this: every keyword needs a `description` and a
`manual_section`, every card and field needs a `description`, and every conditional card
needs a `condition_doc`.

For a repeating card (one row per node/element):

```python
CardSchema("Card 1", [
    CardField("NID", "I", width=8),
    CardField("X",   "F", width=16),
    CardField("Y",   "F", width=16),
    CardField("Z",   "F", width=16),
], repeating=True, write_header=True)
```

For a conditional card (present only for certain keyword variants):

```python
CardSchema("Card 2", [
    CardField("VC", "F", description="Tensor viscosity coefficient"),
    CardField("CP", "F", description="Cavitation pressure", units="stress"),
], condition=lambda kw: kw.is_fluid, write_header=True,
   condition_doc="only with the FLUID option",
   description="Viscosity and cavitation.")
```

The condition may read option flags set in `__init__`, but not `self.cards` — it is
evaluated against an empty instance when introspection resolves a variant's cards.  For a
card whose presence depends on a value parsed from an earlier card (say `ICOMP = 1` on
Card 1), give `condition_doc` alone and leave `condition` as None.

*   **`dynakw/keywords/{KEYWORD_NAME}.py`**: Each LS-DYNA keyword is implemented in its
    own file.  For example, `NODE.py` contains `Node`, `MAT_ELASTIC.py` contains
    `MatElastic`, etc.

### Keyword data storage

Keyword data is stored in `cards: Dict[str, Dict[str, np.ndarray]]` — a two-level dict
where the outer key is the card name (`'Card 1'`, `'Card 2'`, …) and the inner key is the
field name (`'EID'`, `'PID'`, `'N1'`, …).  Values are numpy arrays.

Numpy dtypes follow the field type declared in `CardField`:
- `'I'` → `np.int32`
- `'F'` → `np.float64`
- `'A'` → `object`

A column that contains any `ParameterRef` values is stored as `dtype=object` to preserve
the reference.

Example:

```python
keyword.cards['Card 1']['N1'] = np.array([2, 11, 3, 99, 1], dtype=np.int32)
```

For repeating cards, each array has one element per row:

```python
nids = node_kw.cards['Card 1']['NID']   # shape (n_nodes,), dtype=np.int32
xs   = node_kw.cards['Card 1']['X']     # shape (n_nodes,), dtype=np.float64
```

For composite element cards (e.g. `ELEMENT_SHELL` Card 6), 2D arrays are used:

```python
mid = shell_kw.cards['Card 6']['MID']      # shape (n_elems, max_layers), dtype=np.int32
n   = shell_kw.cards['Card 6']['N_LAYERS'] # shape (n_elems,),            dtype=np.int32
```

### Parameter references (`&VAR`)

When a data field contains `&VARNAME`, it is stored as a `ParameterRef` object rather
than a numeric value.  The field's array dtype becomes `object`.  On write, the reference
is formatted back as `&VARNAME` in the correct field width.

```python
from dynakw import ParameterRef

e_val = mat_kw.cards['Card 1']['E'][0]
if isinstance(e_val, ParameterRef):
    print(e_val.name)   # e.g. "Emod"
    print(str(e_val))   # "&Emod"
```

## Capability introspection

Callers that generate decks — rather than read them — need to know which keywords exist
and what fields each card has.  That is what `dynakw.supported_keywords()`,
`describe_keyword()` and `capability_manifest()` report.  They read the `CardSchema`
declarations directly, so the report is always what the library actually does.

```python
import dynakw

for spec in dynakw.supported_keywords():
    print(spec.keyword, len(spec.cards), spec.can_build)

for spec in dynakw.supported_keywords("*SET_*"):    # fnmatch filter
    ...
```

**Every keyword name starts with `*`, which is also the glob wildcard**, so `"*NODE"`
matches `*SET_NODE` as well as `*NODE`.  Bracket the star — `"[*]NODE"` — to anchor it.

`describe_keyword(name)` describes a *concrete variant*, with option conditions resolved
by probing an instance built with no data:

```python
spec = dynakw.describe_keyword("*MAT_ELASTIC_FLUID")
[c.name for c in spec.cards]                        # ['Card 1', 'Card 2']
[f.name for f in spec.card("Card 1").fields]        # ['MID', 'RO', 'K']

dynakw.describe_keyword("*MAT_ELASTIC")             # Card 1 only, 7 fields
```

Names resolve exactly as they do when reading a file — `LSDynaKeyword.resolve()` is shared
by both — so `exact_match` is honoured and `*MAT_ELASTIC_PLASTIC_HYDRO` raises
`KeywordNotSupported` rather than being mistaken for an option of `*MAT_ELASTIC`.  The
error suggests near matches.

### What the flags mean

| Flag | Meaning |
|---|---|
| `can_parse` | A block with this name is parsed into cards.  False only for the raw-text fallback. |
| `can_build` | A `cards` dict shaped by the schemas below writes correctly.  True when the class uses the base `write`. |
| `schema_driven` | Both parsing and writing come from the base class. |
| `custom_parse` / `custom_write` | Which half the class overrides. |

`can_build` is deliberately conservative: a class with its own `write` may expect keys the
schemas do not describe, so it reports False until each writer has been checked against
the builder.  That is the checklist for Phase 3 of `DECK_BUILDING_PLAN.md`.

### Out of process

`capability_manifest()` returns the whole report as a JSON-serializable dict, versioned
with `manifest_version` and `dynakw_version`.  The CLI writes it out:

```bash
python -m dynakw.manifest                          # summary table
python -m dynakw.manifest --pattern '*SET_*'
python -m dynakw.manifest --describe '*MAT_ELASTIC_FLUID'
python -m dynakw.manifest --format json > dynakw_capabilities.json
```

`test/test_introspect.py` parses every file in `test/full_files` and asserts that each
card and field the parser produces is declared in the schemas.  A keyword that grows a
card or a column without declaring it fails there — that test is what keeps the report
honest.

## How it Works: From File to Object and Back

1.  **Reading**: `DynaKeywordReader` splits the file into keyword blocks on `*` lines.
2.  **Dispatching**: Each block's keyword line is matched against `LSDynaKeyword.KEYWORD_MAP`
    by `LSDynaKeyword.resolve()`, using longest-prefix matching.  The matching class is
    instantiated with the keyword name and its raw lines.  Introspection resolves names
    through the same method, so the two cannot disagree about what a name means.
3.  **Parsing**: `_parse_raw_data` is called.  If the subclass defines `card_schemas` or
    `card_groups`, the base class handles parsing automatically using `FormatParser` and
    stores properly-typed numpy arrays in `self.cards`.  Subclasses with custom logic
    override this method.
4.  **Manipulation**: Data in `keyword.cards` can be read and modified directly.
5.  **Writing**: `write(file_obj)` formats `self.cards` back into fixed-width LS-DYNA
    format.  For schema-driven keywords this is also fully automatic.

## Error Handling Strategy

- **Graceful Degradation**: Unrecognized keywords are stored as `Unknown`, preserving the
  entire block (including comment lines) as raw text.  No data is lost.
- **Malformed data**: A keyword block that raises an exception during parsing is logged
  and returned as `Unknown("*UNKNOWN", …)`.  The rest of the file continues parsing.
- **Wrong-type fields**: `FormatParser.parse_line` catches `ValueError` from type
  conversion and stores the raw string.  This may cause a subsequent `astype` failure in
  the schema helpers, which is caught at the block level.

## Logging

`dynakw` uses Python's standard `logging` module and adds no handlers by default
(standard library practice).

```python
import logging

# Show warnings and errors on the console
logging.basicConfig(level=logging.WARNING)
```

To target only `dynakw` logs:

```python
import logging

logger = logging.getLogger('dynakw')
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('dynakw.log')
fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)
```
