

# Keyword Implementation

*   **`dynakw/keywords/lsdyna_keyword.py`**: This file contains the abstract base class `LSDynaKeyword`. All specific keyword classes must inherit from this class. It provides the core structure and methods that every keyword object shares, and it also manages a registry of all keyword classes.
    *   `LSDynaKeyword.KEYWORD_MAP`: This dictionary returns the class for a keyword name.
    *   `__init_subclass__(...)`: This method automatically registers any new subclass of `LSDynaKeyword` in a central `KEYWORD_MAP`. This allows the parser to discover new keywords without any manual registration.
    *   `keyword_string`: A class attribute that defines the primary keyword string (e.g., `*NODE`).
    *   `keyword_aliases`: An optional class attribute that provides a list of alternative names for the keyword.
    *   `_parse_raw_data(...)`: An abstract method that must be implemented by subclasses to parse the data lines associated with the keyword and store them, typically in dictionaries and numpy arrays objects.
    *   `write(...)`: An abstract method that must be implemented by subclasses to write the keyword and its data back to a file.

*   **`dynakw/keywords/{KEYWORD_NAME}.py`**: Each LS-DYNA keyword is implemented in its own file within this directory. For example, `BOUNDARY_PRESCRIBED_MOTION.py` contains the `BoundaryPrescribedMotion` class. This class inherits from `LSDynaKeyword` and provides concrete implementations for parsing and writing its specific card format.

## Keyword data storage

The keyword data is stored in `cards: Dict[str, Dict[str, np.ndarray]]`.
It is a dictionary containing a dictionary with numpy arrays as values.
The upper-level dictionary has the card names as keys, for example 'Card 1', 'Card 2', 'Card 3', etc.
The lower-level dictionary has the data names as keys, for example 'EID', 'PID', 'N1', 'N8', 'MID', 'MCID', etc.

For example:
```python
keyword.cards['Card 1']['N1'] = numpy.array( [2,11,3,99,1], dtype=int )
```
