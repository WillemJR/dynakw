# Architecture and Logic

The `dynakw` library is structured to be modular and extensible. The main components are organized as follows:

```
dynakw/
├── core/              # Core parsing and data structures
│   ├── enums.py       # Enumerations for KeywordType
│   └── keyword_file.py# Main class for reading and writing LS-DYNA keyword files
├── keywords/          # Keyword-specific implementations
│   ├── lsdyna_keyword.py # Abstract base class for all keywords
│   └── ...            # Individual keyword files (e.g., BOUNDARY_PRESCRIBED_MOTION.py)
└── utils/             # Utilities
    └── format_parser.py # Parser for LS-DYNA's fixed-width format
```

## Core Components

*   **`dynakw/core/enums.py`**: Defines the `KeywordType` enumeration, which provides a standardized way to identify all supported LS-DYNA keywords.

*   **`dynakw/core/keyword_file.py`**: This file contains the `DynaKeywordFile` class, which is the main entry point for reading and writing LS-DYNA keyword files. It handles file I/O, including following `*INCLUDE` directives, and uses the `DynaParser` to process the file content.

*   **`dynakw/core/parser.py`**: This file contains the `DynaParser` class, which is responsible for parsing the raw text of an LS-DYNA keyword file.
    *   The `DynaParser` uses a registry of known keywords to map keyword strings (e.g., `*NODE`, `*ELEMENT_SHELL`) to their corresponding keyword classes.
    *   The `parse_keyword_block` method takes a list of lines belonging to a single keyword and determines which specific keyword class (e.g., `Node`, `ElementShell`) should be used to instantiate the object.

*   **`dynakw/utils/format_parser.py`**: Contains the `FormatParser` class, a utility for handling the specific fixed-width format of LS-DYNA card fields. It can parse lines into data (integers, floats, strings) and format data back into fixed-width strings for writing.

## Keyword Implementation

*   **`dynakw/keywords/lsdyna_keyword.py`**: This file contains the abstract base class `LSDynaKeyword`. All specific keyword classes must inherit from this class. It provides the core structure and methods that every keyword object shares, and it also manages a registry of all keyword classes.
    *   `__init_subclass__(...)`: This method automatically registers any new subclass of `LSDynaKeyword` in a central `KEYWORD_MAP`. This allows the parser to discover new keywords without any manual registration.
    *   `keyword_string`: A class attribute that defines the primary keyword string (e.g., `*NODE`).
    *   `keyword_aliases`: An optional class attribute that provides a list of alternative names for the keyword.
    *   `_parse_raw_data(...)`: An abstract method that must be implemented by subclasses to parse the data lines associated with the keyword and store them, typically in dictionaries and numpy arrays objects.
    *   `write(...)`: An abstract method that must be implemented by subclasses to write the keyword and its data back to a file.

*   **`dynakw/keywords/{KEYWORD_NAME}.py`**: Each LS-DYNA keyword is implemented in its own file within this directory. For example, `BOUNDARY_PRESCRIBED_MOTION.py` contains the `BoundaryPrescribedMotion` class. This class inherits from `LSDynaKeyword` and provides concrete implementations for parsing and writing its specific card format.

### Keyword data storage

The keyword data is stored in `cards: Dict[str, Dict[str, np.ndarray]]`.
It is a dictionary containing a dictionary with numpy arrays as values.
The upper-level dictionary has the card names as keys, for example 'Card 1', 'Card 2', 'Card 3', etc.
The lower-level dictionary has the data names as keys, for example 'EID', 'PID', 'N1', 'N8', 'MID', 'MCID', etc.

For example:
```python
keyword.cards['Card 1']['N1'] = numpy.array( [2,11,3,99,1], dtype=int )
```

## How it Works: From File to Object and Back

1.  **Reading**: When a keyword is read from a file, its full name (e.g., `*BOUNDARY_PRESCRIBED_MOTION_NODE`) and its data lines are passed to the `DynaParser`.
2.  **Parsing**:
    *   The `DynaParser` searches its keyword registry for the longest matching keyword string.
    *   If a match is found, the corresponding keyword class is instantiated with the keyword name and its raw data lines.
    *   The subclass's `_parse_raw_data` method is then called. It uses the `FormatParser` utility to read the fixed-width data lines and populates one or more dictionaries and numpy arrays which are stored in the `self.cards` dictionary.
3.  **Manipulation**: Once the data is in a keyword, it can be easily accessed and manipulated.
4.  **Writing**: Calling the `write()` method on a keyword object will format the data from the `cards` dictionary back into the correct LS-DYNA fixed-width format and write the lines to the specified file.


## Error Handling Strategy

The library is designed to be robust and handle errors gracefully.

- **Graceful Degradation**: If an unknown keyword is encountered during parsing (i.e., a keyword not present in the `DynaParser`'s keyword map), it is treated as an `Unknown` keyword. The entire keyword block, including the keyword line and all its data lines, is preserved as raw text. This ensures that no data is lost when reading and writing files, even if they contain unsupported keywords.

- **Logging**: All significant events, warnings, and errors are logged using Python's standard `logging` module. This includes notifications about unknown keywords, parsing errors for specific data lines, or missing include files. By default, logs are written to `dynakw.log`. This allows developers to inspect the parsing process without interrupting it.

- **Recovery**: When a specific keyword's data lines cannot be parsed according to the rules in its class (e.g., due to malformed data), the parsing of that keyword may fail, but the overall file processing continues. The error is logged, and the parser moves on to the next keyword.

## Logging

All parsing activities are logged to a file named `dynakw.log` by default. You can customize the logging behavior by obtaining a logger instance and configuring it.

**Default Logging:**
By default, the library logs INFO-level messages and above to `dynakw.log`.

**Custom Logging:**
To change the log file, log level, or format, you can get the logger and add your own handlers.

```python
import logging
from dynakw.utils.logger import get_logger

# Get the logger for a specific module
logger = get_logger('dynakw.core.parser')

# Set a different log level
logger.setLevel(logging.DEBUG)

# Create a new handler to log to a different file
file_handler = logging.FileHandler('custom_parser.log')
file_handler.setLevel(logging.DEBUG)

# Create a formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the handler to the logger
# (You might want to clear existing handlers first)
if logger.hasHandlers():
    logger.handlers.clear()
logger.addHandler(file_handler)

logger.debug("This is a debug message.")
```
