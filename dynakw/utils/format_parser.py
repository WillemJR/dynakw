"""Parser for LS-DYNA fixed format fields"""

import re
from typing import List, Any


class FormatParser:
    """Parser for LS-DYNA fixed format card fields"""

    def __init__(self):
        self.field_width = 10  # Standard field width
        self.long_field_width = 20  # Long format field width

    def _parse_float_str(self, field_str: str) -> float:
        """Helper to parse a float string that might have a missing 'E' for exponent."""
        if 'e' not in field_str.lower():
            # Handle cases like '8.90000-3' -> '8.90000E-3'
            # Use a regex to find numbers with a trailing exponent but no 'E'
            # This regex finds a number (int or float), followed by a sign, and then more digits.
            match = re.match(r'([+-]?\d+\.?\d*)([+-])(\d+)$', field_str)
            if match:
                # Reconstruct with 'E'
                reconstructed_str = f"{match.group(1)}E{match.group(2)}{match.group(3)}"
                return float(reconstructed_str)
        return float(field_str)

    def parse_line(
        self,
        line: str,
        field_types: List[str],
        field_len: List[int] = None,
        long_format: bool = False,
        default_value: Any = 0
    ) -> List[Any]:
        """
        Parse a line according to field types

        Args:
            line: Input line
            field_types: List of field types ('I' for int, 'F' for float, 'A' for string)
            field_len: List of field widths (same length as field_types). If None, uses default widths.
            long_format: Whether to use long format (20 char fields vs 10)
            default_value: Default value to use if field is empty.
        """
        if ',' in line:
            return self.parse_line_by_comma(line, field_types, default_value=default_value)

        default_width = self.long_field_width if long_format else self.field_width
        if field_len is None:
            field_len = [default_width] * len(field_types)
        elif len(field_len) != len(field_types):
            raise ValueError(
                "field_len must be the same length as field_types")

        fields = []
        pos = 0

        for i, field_type in enumerate(field_types):
            this_width = field_len[i]
            start = pos
            end = start + this_width

            if start >= len(line):
                fields.append(default_value)
                pos = end
                continue

            field_str = line[start:end].strip()

            if not field_str:
                fields.append(default_value)
                pos = end
                continue

            try:
                if field_type == 'I':
                    fields.append(int(field_str))
                elif field_type == 'F':
                    fields.append(self._parse_float_str(field_str))
                else:  # 'A' or anything else
                    fields.append(field_str)
            except ValueError:
                fields.append(field_str)
            pos = end

        return fields

    def parse_line_by_comma(
        self,
        line: str,
        field_types: List[str],
        default_value: Any = 0
    ) -> List[Any]:
        """
        Parse a comma-separated line according to field types.

        Args:
            line: Input line, with values separated by commas.
            field_types: List of field types ('I' for int, 'F' for float, 'A' for string).
            default_value: Default value to use if field is empty.
        """
        values = [v.strip() for v in line.split(',')]
        parsed_fields = []

        for i, field_type in enumerate(field_types):
            if i < len(values):
                field_str = values[i]
                if not field_str:
                    parsed_fields.append(default_value)
                    continue

                try:
                    if field_type == 'I':
                        parsed_fields.append(int(field_str))
                    elif field_type == 'F':
                        parsed_fields.append(self._parse_float_str(field_str))
                    else:  # 'A' or anything else
                        parsed_fields.append(field_str)
                except ValueError:
                    # Keep as string if conversion fails
                    parsed_fields.append(field_str)
            else:
                # Pad with default_value if not enough values
                parsed_fields.append(default_value)

        return parsed_fields

    def _is_integer(self, s: str) -> bool:
        """Check if string represents an integer"""
        try:
            int(s)
            return True
        except ValueError:
            return False

    def _is_float(self, s: str) -> bool:
        """Check if string represents a float"""
        try:
            float(s)
            return True
        except ValueError:
            return False

    def format_field(self, value: Any, field_type: str, long_format: bool = False, field_len: int = None) -> str:
        """
        Format a value according to field type

        Args:
            value: Value to format
            field_type: Field type ('I', 'F', 'A')
            long_format: Whether to use long format
        """
        width = self.long_field_width if long_format else self.field_width
        if field_len is not None:
            width = field_len

        if value is None:
            return ' ' * width

        if field_type == 'I':
            return f"{int(value):>{width}d}"
        elif field_type == 'F':
            # Use appropriate precision for the field width
            if long_format:
                return f"{float(value):>{width}.6f}"
            else:
                return f"{float(value):>{width}.4f}"
        else:  # 'A'
            return f"{str(value):>{width}}"
