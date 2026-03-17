# Architecture and Logic

The `dynakw` library is structured to be modular and extensible. The main components are organized as follows:

```
dynakw/
├── core/              # Core parsing and data structures
│   ├── card_schema.py # CardField, CardSchema, CardGroup dataclasses
│   ├── enums.py       # Enumerations for KeywordType
│   ├── keyword_file.py# Main class for reading and writing LS-DYNA keyword files
│   └── parameter_ref.py # ParameterRef: represents &VAR references in data fields
├── keywords/          # Keyword-specific implementations
│   ├── lsdyna_keyword.py # Abstract base class for all keywords
│   └── ...            # Individual keyword files (e.g., BOUNDARY_PRESCRIBED_MOTION.py)
└── utils/             # Utilities
    └── format_parser.py # Parser for LS-DYNA's fixed-width format
```

## Core Components

*   **`dynakw/core/card_schema.py`**: Defines the declarative schema dataclasses used to
    describe keyword card layouts:
    *   `CardField(name, type, width, default, header_name)` — one field in a card.
        `type` is `'I'` (int), `'F'` (float), or `'A'` (string).  `header_name`
        overrides the label shown in the `$  …` comment header line (default: same as
        `name`).
    *   `CardSchema(name, fields, repeating, condition, write_header)` — one card in a
        keyword.  `repeating=True` means the card spans one line per element/node.
        `condition(kw) -> bool` makes the card conditional on keyword instance state.
        `write_header=True` emits a `$  col1  col2  …` comment line before the data.
    *   `CardGroup(schemas)` — a group of `CardSchema` objects written and parsed in
        interleaved row order (one row per schema per element, all headers first).

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
    *   `card_schemas`: Class attribute — list of `CardSchema` objects.  When set, the base
        class provides default `_parse_raw_data` and `write` implementations automatically.
        **This is the preferred way to implement new keywords.**
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

    card_schemas = [
        CardSchema("Card 1", [
            CardField("ID",    "I", width=10),
            CardField("PARAM", "F", width=10),
            CardField("NAME",  "A", width=10),
        ], write_header=True),

        CardSchema("Card 2", [
            CardField("VAL1", "F", width=10),
            CardField("VAL2", "F", width=10),
        ], write_header=True),
    ]
```

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
    CardField("VC", "F"),
    CardField("CP", "F"),
], condition=lambda kw: kw.is_fluid, write_header=True)
```

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

## How it Works: From File to Object and Back

1.  **Reading**: `DynaKeywordReader` splits the file into keyword blocks on `*` lines.
2.  **Dispatching**: Each block's keyword line is matched against `LSDynaKeyword.KEYWORD_MAP`
    using longest-prefix matching.  The matching class is instantiated with the keyword
    name and its raw lines.
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
