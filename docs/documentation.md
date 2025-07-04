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

## Format Support

### Standard Format
- 8 fields per line
- 10 characters per field
- Fixed-width format

### Long Format  
- 20 characters per numeric field
- 160 characters for long text fields
- Activated with `long=y` or `+` suffix

### I10 Format
- 10 characters per integer field (vs 8 in standard)
- Activated with `i10=y` or `%` suffix

## Error Handling

- **Unknown keywords**: Preserved as raw text, logged as warnings
- **Parsing errors**: Keywords fall back to raw text storage
- **Missing include files**: Logged as errors, processing continues
- **Format errors**: Individual fields default to None/empty values

## Logging

All parsing activities are logged to `dynakw.log`. Configure logging:

```python
from dynakw.utils.logger import get_logger
logger = get_logger(__name__, log_file='custom.log')
```

## API Reference

### DynaKeywordFile

Main interface for file operations.

#### Methods

- `__init__(filename: str)`: Initialize with filename
- `read_all(follow_include: bool = False)`: Read all keywords from file
- `next_kw() -> Iterator[DynaKeyword]`: Iterate over keywords
- `write(filename: str)`: Write all keywords to file
- `find_keywords(keyword_type: KeywordType) -> List[DynaKeyword]`: Find keywords by type

### DynaKeyword

Represents a single keyword with its data.

#### Members

- `type: KeywordType`: Keyword type enumeration
- `cards: Dict[str][str] \-\> numpy array : Card data

#### Methods

- `write(file\_obj: TextIO)`: Write keyword to file

### KeywordType

Enumeration of supported keywords:
- `BOUNDARY\_PRESCRIBED\_MOTION`
- `NODE`
- `ELEMENT\_SOLID`
- `SECTION\_SOLID`
- `UNKNOWN`

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Changelog

### v0.1.0 (Initial Release)
- Basic keyword parsing and writing
- Support for common LS-DYNA keywords
- Test infrastructure
- Documentation and examples


## Contents

- **API Reference**: Detailed API documentation
- **Keyword Specifications**: Documentation for each supported keyword
- **Format Guide**: Details on LS-DYNA format support
- **Development Guide**: Information for contributors

## Generating Documentation

Documentation can be generated using Sphinx:

```bash
pip install sphinx sphinx-rtd-theme
sphinx-build -b html docs/ docs/_build/
```

## Format Specifications

### LS-DYNA Card Format

Based on the LS-DYNA manual, cards follow these conventions:

- **Standard Format**: 8 fields × 10 characters = 80 character lines
- **Field Types**: 
  - `I`: Integer
  - `F`: Floating point  
  - `A`: Alphanumeric
- **Free Format**: Comma-delimited values (limited to field width)
- **Long Format**: Extended field widths (20 chars for numeric, 160 for text)

## Testing Strategy

### Test Categories

1. **Unit Tests**: Individual keyword parsing
2. **Integration Tests**: Complete file processing
3. **Roundtrip Tests**: Read → Write → Read verification
4. **Format Tests**: Different format variations

### Test Data Management

- `test/full_files/`: Complete LS-DYNA input files
- `test/keywords/`: Individual keyword examples
- `test/utils/file_splitter.py`: Utility to generate keyword-specific test data

### Continuous Integration

Tests run automatically on:
- Multiple Python versions (3.10+)
- Different platforms (Linux, Windows, macOS)
- Various LS-DYNA file formats

## Architecture Decisions

### Data storage in a keyword

The data are stored using dictionaries and numpy arrays.

These can be easily converted to Pandas dataframes by the user.


### Error Handling Strategy

- **Graceful Degradation**: Unknown keywords preserved as text
- **Logging**: All issues logged but don't stop processing
- **Recovery**: Fallback to raw text storage when parsing fails

### Extensibility Design

- **Plugin Architecture**: Easy to add new keyword parsers
- **Configurable**: Format detection and parsing rules
- **Modular**: Core parsing separate from keyword-specific logic

## Performance Considerations

### Memory Usage

- **Lazy Loading**: Keywords parsed on demand
- **Streaming**: Large files processed in chunks
- **Memory Efficient**: DataFrames only store necessary data

### Processing Speed

- **Optimized Parsing**: Efficient regex and string operations
- **Parallel Processing**: Multiple files can be processed concurrently
- **Caching**: Parsed data cached to avoid re-parsing

## Future Enhancements

### Planned Features

- **More Keywords**: Support for additional LS-DYNA keywords
- **Validation**: Data validation against LS-DYNA specifications
- **Conversion**: Convert between different LS-DYNA versions
- **Visualization**: Built-in plotting for common data types

### API Improvements

- **Context Managers**: Better resource management
- **Async Support**: Asynchronous file processing
- **Streaming API**: Process very large files without loading entirely
- **Schema Definition**: Formal schema for keyword structures
