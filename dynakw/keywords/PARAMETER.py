"""Implementation of the *PARAMETER keyword."""

from typing import TextIO, List
import numpy as np

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.card_schema import CardField, CardSchema


class Parameter(LSDynaKeyword):
    """
    Implements the *PARAMETER keyword.
    """
    keyword_string = "*PARAMETER"
    keyword_aliases = []

    description = (
        "Defines named constants that can be referenced as &name in any later "
        "data field.  Up to four name/value pairs are given per line."
    )
    manual_section = "Vol I, *PARAMETER"

    # This class writes from `cards` alone, so a hand-built *PARAMETER renders
    # correctly even though `write` is custom.  When building one, each name
    # must keep its type prefix -- R for real, I for integer, C for character --
    # since that is what selects the format its value is written in.  Unused
    # pairs hold None.  Verified by test_parameter_build.py.
    builds_from_cards = True

    # Declared for introspection only: _parse_raw_data and write are both
    # overridden, so the base class never consults this list.  The value
    # columns are declared 'A' because their type is not fixed by the layout —
    # it is selected per row by the type character that prefixes the name.
    card_schemas = [
        CardSchema("Card 1", [
            f
            for i in range(1, 5)
            for f in (
                CardField(f"PRMR{i}", "A", width=10,
                          description=f"Name of parameter {i}, prefixed by its "
                                      f"type character: R (real), I (integer) "
                                      f"or C (character)"),
                CardField(f"VAL{i}", "A", width=10,
                          description=f"Value of parameter {i}; stored as int, "
                                      f"float or str according to the type "
                                      f"character of PRMR{i}"),
            )
        ], repeating=True, write_header=True,
           description="Up to four name/value pairs per line."),
    ]

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        super().__init__(keyword_name, raw_lines)

    def _parse_raw_data(self, raw_lines: List[str]):
        """
        Parses the raw data for *PARAMETER.
        """
        card_lines = [line for line in raw_lines[1:]
                      if line.strip() and not line.startswith('$')]
        if not card_lines:
            return

        # Initialize lists to store data for the 4 pairs
        # PRMR1, VAL1, PRMR2, VAL2, PRMR3, VAL3, PRMR4, VAL4
        data_lists = {
            "PRMR1": [], "VAL1": [],
            "PRMR2": [], "VAL2": [],
            "PRMR3": [], "VAL3": [],
            "PRMR4": [], "VAL4": []
        }

        for line in card_lines:
            # Parse all 8 fields as strings initially to handle mixed types
            # We use default_value=None to detect empty fields
            row_data = self.parser.parse_line(
                line, ["A"] * 8, default_value=None)

            for i in range(4):
                prmr_key = f"PRMR{i+1}"
                val_key = f"VAL{i+1}"
                
                prmr_val = row_data[2 * i]
                val_raw = row_data[2 * i + 1]
                
                final_val = val_raw
                
                # Perform type conversion based on PRMR prefix
                if prmr_val:
                    # Strip to ensure we get the first char correctly
                    p_str = str(prmr_val).strip()
                    if p_str:
                        type_char = p_str[0].upper()
                        
                        if val_raw is not None:
                            val_str = str(val_raw)
                            if type_char == 'R':
                                try:
                                    # Use FormatParser's internal helper for scientific notation without 'E'
                                    final_val = self.parser._parse_float_str(val_str)
                                except ValueError:
                                    # Fallback: keep as is if conversion fails
                                    pass
                            elif type_char == 'I':
                                try:
                                    # Handle "2.0" -> 2
                                    final_val = int(float(val_str))
                                except ValueError:
                                    pass
                
                data_lists[prmr_key].append(prmr_val)
                data_lists[val_key].append(final_val)

        # Store in cards dictionary as numpy arrays
        self.cards["Card 1"] = {
            key: np.array(val, dtype=object) for key, val in data_lists.items()
        }

    def write(self, file_obj: TextIO):
        """Writes the *PARAMETER keyword to a file."""
        file_obj.write(f"{self.full_keyword}\n")

        card1 = self.cards.get("Card 1")
        if not card1:
            return

        # Get the number of rows from one of the columns (e.g., PRMR1)
        # We assume all columns in Card 1 have the same length
        any_col = next(iter(card1.values()))
        num_rows = len(any_col)

        if num_rows == 0:
            return

        # Prepare header
        cols = []
        for i in range(1, 5):
            cols.append(f"PRMR{i}")
            cols.append(f"VAL{i}")
        
        file_obj.write(self.parser.format_header(cols))

        # Write data rows
        for r in range(num_rows):
            line_parts = []
            for i in range(1, 5):
                p_key = f"PRMR{i}"
                v_key = f"VAL{i}"
                
                p_val = card1[p_key][r]
                v_val = card1[v_key][r]
                
                # Format PRMR as string
                line_parts.append(self.parser.format_field(p_val, "A"))
                
                # Format VAL based on PRMR type
                val_type = "A" # Default to string
                if p_val:
                    p_str = str(p_val).strip()
                    if p_str:
                        type_char = p_str[0].upper()
                        if type_char == 'R':
                            val_type = "F"
                        elif type_char == 'I':
                            val_type = "I"
                
                line_parts.append(self.parser.format_field(v_val, val_type))
            
            file_obj.write("".join(line_parts) + "\n")
