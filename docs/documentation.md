# LS-DYNA Keywords Reader Library (dynakw)

A Python library for reading, parsing, editing, and writing LS-DYNA keyword files.

## Features

- **Read LS-DYNA keyword files** into structured Python data (numpy arrays)
- **Edit keyword data** programmatically 
- **Write modified data** back to LS-DYNA format
- **Support for INCLUDE files** with recursive processing
- **Robust error handling** - unknown keywords are preserved as raw text
- **Multiple format support** - standard, long format, and I10 formats
- **Extensible architecture** - easy to add support for new keywords

## Quick Start

### Installation

```bash
pip install -e .  # Install in development mode
```

### Basic Usage

```python
import dynakw

# Read and write a keyword file
dkw = dynakw.DynaKeywordFile('input.k')
dkw.read_all(follow_include=True)
dkw.write('output.k')

# Find and edit specific keywords
for kw in dkw.next_kw():
    if kw.type == dynakw.BOUNDARY_PRESCRIBED_MOTION:
        print(kw.cards['Card 1']['SF'])  # Print scale factors
        kw.cards['Card 1']['SF'] = kw.cards['Card 1']['SF'] * 1.5  # Scale by 1.5
        kw.write(sys.stdout)  # Write to stdout
```

## Architecture

### Core Components

- **DynaKeywordFile**: Main class for file I/O operations
- **DynaKeyword**: Represents individual keywords with card data
- **DynaParser**: Parses keyword text into structured data
- **FormatParser**: Handles LS-DYNA fixed-format field parsing

### Data Structure

Each keyword contains:
- `type`: KeywordType enumeration
- `cards`: Dictionary of cards names ('Card 1', 'Card 2', etc.). Each card has a dictionary containing
     name / numpy arrays pairs.
- `write()`: Method to output keyword in LS-DYNA format

### Supported Keywords

Currently implemented:
- NODE
- ELEMENT\_SOLID
- SECTION\_SOLID
- PART 
- MAT\_ELASTIC 
- BOUNDARY\_PRESCRIBED\_MOTION

Unknown keywords are preserved as raw text and can be written back unchanged.

## Development

### Project Structure

```
project/
├── dynakw/                 # Main library
│   ├── core/              # Core parsing and data structures
│   ├── keywords/          # Keyword-specific implementations
│   └── utils/             # Utilities (logging, format parsing)
├── test/                  # Test suite
│   ├── keywords/          # Individual keyword tests
│   ├── full_files/        # Complete file tests
│   └── utils/             # Test utilities
├── examples/              # Usage examples
└── docs/                  # Documentation
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest test/test_keywords.py     # Individual keyword tests
pytest test/test_full_files.py   # Complete file tests

# Run with coverage
pytest --cov=dynakw
```

### Test Data Generation

The library includes utilities to generate test data:

```bash
# Split full files into individual keywords
python test/utils/file_splitter.py
```

This takes files from `test/full_files/` and creates individual keyword files in `test/keywords/`.

### Adding New Keywords

1. Add keyword type to `core/enums.py`
2. Add parsing logic to `core/parser.py`
3. Create keyword-specific implementation in `keywords/`
4. Add tests in `test/test_keywords.py`

Example:
```python
# In core/enums.py
class KeywordType(Enum):
    MY_NEW_KEYWORD = auto()

# In core/parser.py
def _parse_my_new_keyword(self, keyword: DynaKeyword, data_lines: List[str]):
    # Implementation here
    pass
```


## Error Handling

- **Unknown keywords**: Preserved as raw text, logged as warnings
- **Parsing errors**: Keywords fall back to raw text storage
- **Missing include files**: Logged as errors, processing continues
- **Format errors**: Individual fields default to None/empty values

## Logging

The library uses Python's standard `logging` module. Configure logging in your application:

```python
import logging
logging.basicConfig(level=logging.WARNING)
```

## API Reference


## Examples

### Example 1: Read and Write
```python
import dynakw

dkw = dynakw.DynaKeywordFile('input.k')
dkw.read_all(follow_include=True)
dkw.write('output.k')
```

### Example 2: Edit Boundary Conditions
```python
import dynakw

dkw = dynakw.DynaKeywordFile('model.k')
dkw.read_all()

for kw in dkw.next_kw():
    if kw.type == dynakw.BOUNDARY_PRESCRIBED_MOTION:
        # Scale all factors by 2.0
        kw.Card1['SF'] *= 2.0

dkw.write('modified_model.k')
```

### Example 3: Create Keywords Programmatically
```python
import numpy as np
from dynakw.core.keyword import DynaKeyword
from dynakw import BOUNDARY_PRESCRIBED_MOTION

keyword = DynaKeyword(BOUNDARY_PRESCRIBED_MOTION)
keyword._original_line = "*BOUNDARY_PRESCRIBED_MOTION"

# Create data
data = np.array( [[1, 1, 0, 1, 1.0, 0, 0.0, 0.0]] )
keyword.add_card('Card1', data)

# Write to file
with open('output.k', 'w') as f:
    keyword.write(f)
```
