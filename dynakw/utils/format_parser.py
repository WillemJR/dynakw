"""Parser for LS-DYNA fixed format fields"""

import re
from typing import List, Any
from dynakw.core.parameter_ref import ParameterRef


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

            if field_str.startswith('&'):
                fields.append(ParameterRef(field_str[1:]))
                pos = end
                continue

            try:
                if field_type == 'I':
                    # Use int(float(...)) so that float-formatted integers
                    # like "0.0000000" or "4.000E+00" are handled correctly.
                    fields.append(int(float(field_str)))
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

                if field_str.startswith('&'):
                    parsed_fields.append(ParameterRef(field_str[1:]))
                    continue

                try:
                    if field_type == 'I':
                        parsed_fields.append(int(float(field_str)))
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

    def format_header(self, cols: List[str], long_format: bool = False, field_len=None) -> str:
        """
        Formats a list of column names into a keyword header line.

        Args:
            cols (List[str]): A list of column name strings. Unused columns can be represented
                              by None or an empty string.
            long_format (bool): Whether to use long format (20 char fields vs 10).
            field_len (int | List[int]): An optional field width (single int applied to all
                                         columns, or a list of per-column widths).

        Returns:
            str: A formatted header line, e.g., "$     col1      col2"
        """
        default_width = self.long_field_width if long_format else self.field_width

        if field_len is None:
            widths = [default_width] * len(cols)
        elif isinstance(field_len, list):
            widths = field_len
        else:
            widths = [field_len] * len(cols)

        header_parts = [f'{(col.lower() if col else ""):>{widths[i]}}' for i, col in enumerate(cols)]
        header_parts[0] = header_parts[0][1:]
        body = "".join(header_parts)
        return f"${body}\n"

    @staticmethod
    def _relative_error(value: float, formatted: str) -> float:
        """How much of *value* is lost by writing it as *formatted*."""
        try:
            written = float(formatted)
        except ValueError:                       # 'inf', 'nan'
            return float('inf')
        if written == value:
            return 0.0
        if value == 0.0:
            return abs(written)
        return abs(written - value) / abs(value)

    @staticmethod
    def _fixed_point(value: float, width: int, decimals: int) -> str:
        """*value* in fixed-point notation, using the room the field allows.

        ``decimals`` is a floor, not a fixed count.  Writing a twenty-character
        field with four decimals throws away digits it had room for: a
        ``*DEFINE_CURVE`` ordinate of 7.13000011 came back as 7.1300.  A wider
        field therefore gets proportionally more decimals, and the surplus is
        trimmed back off again when it turns out to be trailing zeros, so a
        value that needs no extra digits keeps its familiar form -- 7.13 stays
        ``"7.1300"`` rather than becoming ``"7.13000000000000"``.

        Ten characters is the usual field, and its rendering is unchanged.
        """
        precision = decimals + max(0, width - 10)
        text = f"{value:.{precision}f}"
        if precision > decimals and "." in text:
            whole, _, fraction = text.partition(".")
            keep = max(decimals, len(fraction.rstrip("0")))
            text = f"{whole}.{fraction[:keep]}"
        return text

    def _format_float(self, value: float, width: int, long_format: bool) -> str:
        """Fit *value* into *width* characters, keeping as much of it as possible.

        A fixed-point representation can fail in two directions:

        * it needs more characters than the field has, as ``%.4f`` of 2.1e11
          does, and
        * it has too few decimals to hold the value at all, as ``%.4f`` of
          7.85e-9 does --- that yields ``"0.0000"``, which silently writes a
          steel density as zero.

        Only the first is visible to a "does it fit" test; the second produces a
        *short* string.  So the candidates are compared on the value they read
        back as, and the closest wins.  Fixed-point wins a tie, which keeps the
        familiar form for ordinary values.
        """
        decimals = 6 if long_format else 4
        fixed = self._fixed_point(value, width, decimals)

        # Keep the fixed-point form whenever it holds the value to the
        # precision it nominally offers.  Only when it does not is it worth
        # trading the conventional look of a deck for scientific notation.
        if (len(fixed) <= width
                and self._relative_error(value, fixed) <= 10.0 ** -decimals):
            return fixed

        candidates = []
        if len(fixed) <= width:
            candidates.append(fixed)

        # As many significant digits as the field can hold, keeping one column
        # free so that adjacent fields do not run together -- a full-width
        # 2.1000E+11 beside 7.8500 reads as "7.85002.1000E+11".  The exponent
        # costs four characters ("E+dd"), the decimal point one, and a minus
        # sign one more; step down from there until it fits, which also covers
        # the three-digit exponents of very large and very small magnitudes.
        start = width - 5 - (1 if value < 0 else 0)
        for limit in (width - 1, width):
            scientific = next(
                (s for s in (f"{value:.{p}E}"
                             for p in range(max(start, 0), -1, -1))
                 if len(s) <= limit),
                None)
            if scientific is not None:
                candidates.append(scientific)
                break

        if not candidates:
            # The field is too narrow for any representation; the fixed-point
            # one at least keeps the leading digits.
            return fixed

        return min(candidates, key=lambda s: self._relative_error(value, s))

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

        if isinstance(value, ParameterRef):
            return f"{str(value):>{width}}"

        if field_type == 'I':
            return f"{int(value):>{width}d}"
        elif field_type == 'F':
            return f"{self._format_float(float(value), width, long_format):>{width}}"

        else:  # 'A'
            return f"{str(value):>{width}}"


if __name__ == '__main__':

    fp = FormatParser()
    s = fp.format_field( 210000000000.0,  'F', field_len = 10 )
    print( s )


    s2 = fp.parse_line( '       1       1       5       6       7       8       1       2       3       4', ["I"] * 10, field_len=[8] * 10)
    print( s2 )
