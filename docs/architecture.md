
# Architecture and Logic

The `dynakw` library is structured to be modular and extensible. The main components are organized as follows:

```
dynakw/
├── core/              # Core parsing and data structures
│   └── enums.py       # Enumerations for KeywordType
│   └── keyword_file.py# Main class for reading and writing LS-DYNA keyword files
├── keywords/          # Keyword-specific implementations
│   ├── lsdyna_keyword.py # Abstract base class for all keywords
│   └── ...            # Individual keyword files (e.g., BOUNDARY_PRESCRIBED_MOTION.py)
└── utils/             # Utilities
    └── format_parser.py # Parser for LS-DYNA's fixed-width format
```

## Core Components

*   **`dynakw/core/enums.py`**: Defines the `KeywordType` enumeration, which provides a standardized way to identify all supported LS-DYNA keywords.

*   **`dynakw/core/keyword_file.py`**:  Main class for reading and writing LS-DYNA keyword files.

*   **`dynakw/core/parser.py`**:  Parser for LS-DYNA keyword files.

*   **`dynakw/utils/format_parser.py`**: Contains the `FormatParser` class, a utility for handling the specific fixed-width format of LS-DYNA card fields. It can parse lines into data (integers, floats, strings) and format data back into fixed-width strings for writing.

## Keyword Implementation

*   **`dynakw/keywords/lsdyna_keyword.py`**: This file contains the abstract base class `LSDynaKeyword`. All specific keyword classes must inherit from this class. It provides the core structure and methods that every keyword object shares:
    *   `__init__(...)`: Initializes the object, parses the keyword name to identify its `KeywordType` and any options (e.g., `_NODE`, `_SET`).
    *   `_parse_raw_data(...)`: An abstract method that must be implemented by subclasses to parse the data lines associated with the keyword and store them, typically in dictionaries and numpy arrays objects.
    *   `write(...)`: An abstract method that must be implemented by subclasses to write the keyword and its data back to a file.

*   **`dynakw/keywords/{KEYWORD_NAME}.py`**: Each LS-DYNA keyword is implemented in its own file within this directory. For example, `BOUNDARY_PRESCRIBED_MOTION.py` contains the `BoundaryPrescribedMotion` class. This class inherits from `LSDynaKeyword` and provides concrete implementations for parsing and writing its specific card format.


### Keyword data storage

The keyword data is stored in `cards: Dict[str][str] \-\> numpy array`. 
It is a dictionary containing a dictionary with numpy arrays as values.
The upper level dictionary has the card names as keys,  for example 'Card 1', 'Card 2', 'Card 3', etc.
The lower level dictionary has the data names as keys,  for example 'EID', 'PID', 'N1', 'N8', 'MID', 'MCID', etc.

For example:
```
keyword.cards['Card 1']['N1'] = numpy.array( [2,11,3,99,1], dtype=int )
```

## How it Works: From File to Object and Back

1.  **Reading**: When a keyword is read from a file, its full name (e.g., `*BOUNDARY_PRESCRIBED_MOTION_NODE`) and its data lines are passed to the corresponding keyword class constructor (e.g., `BoundaryPrescribedMotion`).
2.  **Parsing**:
    *   The `LSDynaKeyword` base class constructor first parses the keyword name. It identifies the base keyword (`BOUNDARY_PRESCRIBED_MOTION`) and any options (`NODE`).
    *   The subclass's `_parse_raw_data` method is then called. It uses the `FormatParser` utility to read the fixed-width data lines and populates one or more dictionaries and numpy arrays which are stored in the `self.cards` dictionary.
3.  **Manipulation**: Once the data is in a keyword, it can be easily accessed and converted to a pandas dataframe.
4.  **Writing**: Calling the `write()` method on a keyword object will format the data from the DataFrames back into the correct LS-DYNA fixed-width format and write the lines to the specified file.


## Error Handling Strategy

- **Graceful Degradation**: Unknown keywords preserved as text
- **Logging**: All issues logged but don't stop processing
- **Recovery**: Fallback to raw text storage when parsing fails

## Logging

All parsing activities are logged to `dynakw.log`. Configure logging:

```python
from dynakw.utils.logger import get_logger
logger = get_logger(__name__, log_file='custom.log')
```

