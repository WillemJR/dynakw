"""Abstract base class for all LS-DYNA keyword objects."""

from collections import OrderedDict
from abc import ABC, abstractmethod
from typing import TextIO, List, Dict, Tuple
import numpy as np
from dynakw.core.enums import KeywordType
from dynakw.core.card_schema import CardField, CardGroup, CardSchema
from dynakw.core.parameter_ref import ParameterRef
from dynakw.utils.format_parser import FormatParser
import os
import importlib


class LSDynaKeyword(ABC):
    """
    Base class for all LS-DYNA keyword objects.

    This class provides the basic structure for representing an LS-DYNA
    keyword, including methods for parsing from raw text and writing
    back to a file format.

    Subclasses can either:
    - Define ``card_schemas`` (a list of CardSchema objects) to get automatic
      parse and write behaviour provided by this base class, or
    - Override ``_parse_raw_data`` and ``write`` directly for custom logic.

    Attributes:
        cards ( Dict[str, Dict[str, np.ndarray]] = {} ): The cards content as described in the LS-DYNA manual; e.g. kw.cards['Card 1']['SF']
        card_schemas ( List[CardSchema] ): Declarative card layout. When set, the base
            class automatically handles parsing and writing.
    """

    KEYWORD_MAP: Dict[str, "LSDynaKeyword"] = OrderedDict()
    """A registry of all known keyword strings and the classes that handle them."""

    card_schemas: List[CardSchema] = []
    """Declarative card layout. Override in subclasses to enable auto-parse/write."""

    card_groups: List[CardGroup] = []
    """Grouped card layout for interleaved (per-element) parse/write.
    When set, each group is written as: all headers first, then one row per schema
    per element. Takes precedence over card_schemas in the default implementations."""

    def __init_subclass__(cls, **kwargs):
        """This method is called when a subclass of LSDynaKeyword is defined."""
        super().__init_subclass__(**kwargs)
        # The 'keyword_string' is the primary identifier for the keyword class.
        if hasattr(cls, 'keyword_string'):
            # Register the primary keyword string.
            cls.KEYWORD_MAP[cls.keyword_string] = cls
        # 'keyword_aliases' can be used for alternative names for the same keyword.
        if hasattr(cls, 'keyword_aliases'):
            for alias in cls.keyword_aliases:
                cls.KEYWORD_MAP[alias] = cls

    def __init__(self, keyword_name: str, raw_lines: List[str] = None, start_line: int = None):
        """
        Initializes the LSDynaKeyword object.

        Args:
            keyword_name (str): The full name of the keyword (e.g., "*BOUNDARY_PRESCRIBED_MOTION_NODE").
            raw_lines (List[str], optional): The raw text lines for the keyword. Defaults to None.
            start_line (int, optional): The line number where the keyword starts in the file. Defaults to None.
        """
        self.full_keyword = keyword_name.strip()
        self.type, self.options = self._parse_keyword_name(self.full_keyword)
        self.cards: Dict[str, Dict[str, np.ndarray]] = {}
        self.parser = FormatParser()
        self._start_line = start_line

        if raw_lines:
            self._parse_raw_data(raw_lines)

    @staticmethod
    def _parse_keyword_name(keyword_name: str) -> Tuple[KeywordType, List[str]]:
        """
        Parses the keyword name to extract the base type and options.
        Example: "*BOUNDARY_PRESCRIBED_MOTION_NODE" -> (KeywordType.BOUNDARY_PRESCRIBED_MOTION, ["NODE"])
        """
        # Remove leading '*' and split by '_'
        parts = keyword_name.strip()[1:].split('_')

        # Find the longest matching enum name
        for i in range(len(parts), 0, -1):
            base_keyword_str = '_'.join(parts[:i])
            try:
                type = KeywordType[base_keyword_str]
                options = parts[i:]
                return type, options
            except KeyError:
                continue

        return KeywordType.UNKNOWN, parts

    def _parse_raw_data(self, raw_lines: List[str]):
        """
        Parses the raw data lines and populates self.cards.

        If ``card_groups`` is defined, uses interleaved grouped parsing.
        If ``card_schemas`` is defined, uses sequential schema parsing.
        Otherwise subclasses must override this method.
        """
        if self.card_groups:
            data_lines = [l for l in raw_lines[1:] if not l.strip().startswith('$')]
            for group in self.card_groups:
                active = [s for s in group.schemas if not s.condition or s.condition(self)]
                self._parse_grouped_lines(data_lines, active)
            return
        if not self.card_schemas:
            raise NotImplementedError(
                f"{type(self).__name__} must define card_schemas/card_groups or override _parse_raw_data"
            )
        data_lines = [l for l in raw_lines[1:] if not l.strip().startswith('$')]
        idx = 0
        for schema in self.card_schemas:
            if schema.condition and not schema.condition(self):
                continue
            if schema.repeating:
                self.cards[schema.name] = self._parse_repeating_card(data_lines[idx:], schema)
                break
            else:
                if idx < len(data_lines):
                    self.cards[schema.name] = self._parse_single_card(data_lines[idx], schema)
                    idx += 1

    def write(self, file_obj: TextIO):
        """
        Writes the keyword and its data to a file object.

        If ``card_groups`` is defined, uses interleaved grouped writing.
        If ``card_schemas`` is defined, uses sequential schema writing.
        Otherwise subclasses must override this method.
        """
        if self.card_groups:
            file_obj.write(f"{self.full_keyword}\n")
            for group in self.card_groups:
                active = [s for s in group.schemas if not s.condition or s.condition(self)]
                self._write_grouped_schemas(file_obj, active)
            return
        if not self.card_schemas:
            raise NotImplementedError(
                f"{type(self).__name__} must define card_schemas/card_groups or override write"
            )
        file_obj.write(f"{self.full_keyword}\n")
        for schema in self.card_schemas:
            if schema.condition and not schema.condition(self):
                continue
            card = self.cards.get(schema.name)
            if card is not None:
                self._write_card(file_obj, card, schema)

    # ------------------------------------------------------------------
    # Schema-driven helpers (used by the default _parse_raw_data / write)
    # ------------------------------------------------------------------

    _DTYPE_MAP = {'I': np.int32, 'F': np.float64, 'A': object}

    def _parse_single_card(self, line: str, schema: CardSchema) -> Dict[str, np.ndarray]:
        """Parse one fixed-width line into a dict of single-element numpy arrays."""
        field_types = [f.type for f in schema.fields]
        field_lens  = [f.width for f in schema.fields]
        values = self.parser.parse_line(line, field_types, field_len=field_lens)
        return {
            f.name: np.array(
                [values[i]],
                dtype=object if isinstance(values[i], ParameterRef) else self._DTYPE_MAP[f.type],
            )
            for i, f in enumerate(schema.fields)
        }

    def _parse_repeating_card(self, lines: List[str], schema: CardSchema) -> Dict[str, np.ndarray]:
        """Parse multiple fixed-width lines into a dict of numpy arrays (one row per line)."""
        field_types = [f.type for f in schema.fields]
        field_lens  = [f.width for f in schema.fields]
        col_dtypes  = [self._DTYPE_MAP[f.type] for f in schema.fields]
        columns     = [f.name for f in schema.fields]

        parsed_data = []
        for line in lines:
            values = self.parser.parse_line(line, field_types, field_len=field_lens)
            if any(v is not None for v in values):
                parsed_data.append(values[:len(schema.fields)])

        if parsed_data:
            arr = np.array(parsed_data, dtype=object)
            result = {}
            for i, col in enumerate(columns):
                col_arr = arr[:, i]
                has_ref = any(isinstance(v, ParameterRef) for v in col_arr)
                result[col] = col_arr.astype(object if has_ref else col_dtypes[i], copy=False)
            return result
        else:
            return {col: np.array([], dtype=col_dtypes[i]) for i, col in enumerate(columns)}

    def _write_card(self, file_obj: TextIO, card: Dict[str, np.ndarray], schema: CardSchema):
        """Write one card (single or repeating) to file_obj."""
        if schema.write_header:
            file_obj.write(self.parser.format_header(
                [f.header_name or f.name for f in schema.fields],
                field_len=[f.width for f in schema.fields],
            ))
        if schema.repeating:
            n_rows = len(card[schema.fields[0].name])
            for idx in range(n_rows):
                parts = [
                    self.parser.format_field(card[f.name][idx], f.type, field_len=f.width)
                    for f in schema.fields
                ]
                file_obj.write(''.join(parts) + '\n')
        else:
            parts = [
                self.parser.format_field(card[f.name][0], f.type, field_len=f.width)
                for f in schema.fields
            ]
            file_obj.write(''.join(parts) + '\n')

    def _parse_grouped_lines(self, data_lines: List[str], schemas: List[CardSchema]):
        """Parse interleaved data lines into self.cards.

        Lines are assumed to cycle through schemas with a fixed stride equal to
        ``len(schemas)``:  line 0 → schema 0, line 1 → schema 1, ...,
        line N → schema 0 again, etc.
        """
        stride = len(schemas)
        if stride == 0:
            return
        for i, schema in enumerate(schemas):
            self.cards[schema.name] = self._parse_repeating_card(
                data_lines[i::stride], schema
            )

    def _write_grouped_schemas(self, file_obj: TextIO, schemas: List[CardSchema]):
        """Write headers once then interleaved data rows (one row per schema per element).

        For each schema, if a field name is absent from the card (e.g. trailing
        optional columns never parsed), it is written as blank space.
        """
        # 1. Headers
        for schema in schemas:
            if schema.write_header:
                file_obj.write(self.parser.format_header(
                    [f.header_name or f.name for f in schema.fields],
                    field_len=[f.width for f in schema.fields],
                ))

        if not schemas:
            return

        # Row count from the first schema's first field
        first_card = self.cards.get(schemas[0].name)
        if first_card is None:
            return
        n_rows = len(first_card[schemas[0].fields[0].name])

        # 2. Interleaved data rows
        for idx in range(n_rows):
            for schema in schemas:
                card = self.cards.get(schema.name)
                if card is None:
                    continue
                parts = [
                    self.parser.format_field(
                        card[f.name][idx] if f.name in card else None,
                        f.type,
                        field_len=f.width,
                    )
                    for f in schema.fields
                ]
                file_obj.write(''.join(parts) + '\n')

    def __repr__(self):
        return f"LSDynaKeyword(type={self.type.name}, options={self.options})"

    @staticmethod
    def discover_keywords():
        """
        Dynamically imports all keyword modules from the 'keywords' directory
        to ensure they are registered in the KEYWORD_MAP.
        """
        keyword_dir = os.path.dirname(__file__)
        for filename in os.listdir(keyword_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"dynakw.keywords.{filename[:-3]}"
                try:
                    importlib.import_module(module_name)
                except ImportError as e:
                    # Handle potential import errors gracefully
                    print(f"Could not import {module_name}: {e}")
