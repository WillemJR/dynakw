"""Implementation of the *MAT_ELASTIC keyword."""

from typing import List, TextIO
import numpy as np
from .lsdyna_keyword import LSDynaKeyword


class MatElastic(LSDynaKeyword):
    """
    Represents a *MAT_ELASTIC keyword in an LS-DYNA input file.
    This keyword can appear as *MAT_ELASTIC or *MAT_001, with an
    optional _FLUID suffix.
    """
    keyword_string = "*MAT_ELASTIC"
    keyword_aliases = ["*MAT_001", "*MAT_ELASTIC_FLUID", "*MAT_001_FLUID"]

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        self.is_fluid = "_FLUID" in keyword_name.upper()
        super().__init__(keyword_name, raw_lines)

    def _parse_raw_data(self, raw_lines: List[str]):
        """Parses the raw data for *MAT_ELASTIC."""

        card_lines = [line for line in raw_lines[1:]
                      if not line.strip().startswith('$')]

        if not card_lines:
            raise ValueError("*MAT_ELASTIC requires at least one data card.")

        # Card 1
        card1_cols = ['MID', 'RO', 'E', 'PR', 'DA', 'DB', 'K']
        card1_types = ['A', 'F', 'F', 'F', 'F', 'F', 'F']
        parsed_card1 = self.parser.parse_line(card_lines[0], card1_types)
        data1 = dict(zip(card1_cols, parsed_card1))

        # Validation
        if data1['MID'] is None or data1['RO'] is None:
            raise ValueError("MID and RO are required fields.")

        if self.is_fluid:
            if data1['K'] is None or data1['K'] == 0.0:
                raise ValueError(
                    "K is required for FLUID option and cannot be 0.0.")
            data1.pop('E')
            data1.pop('PR')
            data1.pop('DA')
            data1.pop('DB')
        else:
            if data1['E'] is None:
                raise ValueError("E is required for non-FLUID option.")
            data1.pop('K')

        # Apply defaults
        if data1.get('PR') is None:
            data1['PR'] = 0.0
        if data1.get('DA') is None:
            data1['DA'] = 0.0
        if data1.get('DB') is None:
            data1['DB'] = 0.0
        if data1.get('K') is None:
            data1['K'] = 0.0

        # Save as dict of numpy arrays
        self.cards['card1'] = {col: np.array(
            [data1.get(col)], dtype=object) for col in data1}

        if self.is_fluid:
            if len(card_lines) < 2:
                raise ValueError("FLUID option requires a second card.")

            # Card 2
            card2_cols = ['VC', 'CP']
            card2_types = ['F', 'F']
            parsed_card2 = self.parser.parse_line(card_lines[1], card2_types)
            data2 = dict(zip(card2_cols, parsed_card2))

            if data2['VC'] is None:
                raise ValueError("VC is required for FLUID option.")
            if data2['CP'] is None:
                data2['CP'] = 1.0e20

            self.cards['card2'] = {col: np.array(
                [data2.get(col)], dtype=object) for col in data2}

    def write(self, file_obj: TextIO):
        """Writes the keyword to a file."""
        file_obj.write(f"{self.full_keyword}\n")
        card1 = self.cards.get('card1')
        if card1 is not None and len(next(iter(card1.values()))) > 0:
            # Determine which fields to write based on fluid or not
            if self.is_fluid:
                cols = ['MID', 'RO', 'K']
                types = ['A', 'F', 'F']
                header_cols = cols
            else:
                cols = ['MID', 'RO', 'E', 'PR', 'DA', 'DB']
                types = ['A', 'F', 'F', 'F', 'F', 'F']
                header_cols = cols + ['K']

            header = "$#" + \
                "".join([f"{name.lower():>10}" for name in header_cols])
            file_obj.write(header + "\n")

            line_parts = [self.parser.format_field(
                card1.get(col, [None])[0], typ) for col, typ in zip(cols, types)]
            file_obj.write("".join(line_parts))
            if not self.is_fluid:
                # Write K as 0.0 for non-fluid, if present
                file_obj.write(self.parser.format_field(0.0, 'F'))
            file_obj.write("\n")

        if self.is_fluid:
            card2 = self.cards.get('card2')
            if card2 is not None and len(next(iter(card2.values()))) > 0:
                cols = ['VC', 'CP']
                types = ['F', 'F']
                header = "$#" + \
                    "".join([f"{name.lower():>10}" for name in cols])
                file_obj.write(header + "\n")
                line_parts = [self.parser.format_field(
                    card2.get(col, [None])[0], typ) for col, typ in zip(cols, types)]
                file_obj.write("".join(line_parts))
                file_obj.write("\n")
