"""Implementation of the *MAT_ELASTIC keyword."""

from typing import List, TextIO
import pandas as pd
from .lsdyna_keyword import LSDynaKeyword

class MatElastic(LSDynaKeyword):
    """
    Represents a *MAT_ELASTIC keyword in an LS-DYNA input file.
    This keyword can appear as *MAT_ELASTIC or *MAT_001, with an
    optional _FLUID suffix.
    """

    def __init__(self, keyword_line: str, raw_lines: List[str] = None):
        super().__init__(keyword_line, raw_lines)
        self.is_fluid = "_FLUID" in self.keyword_line.upper()
        self._parse_raw_data(self.data_lines)

    def _parse_raw_data(self, raw_lines: List[str]):
        """Parses the raw data for *MAT_ELASTIC."""
        if not raw_lines:
            raise ValueError("*MAT_ELASTIC requires at least one data card.")

        # Card 1
        card1_cols = ['MID', 'RO', 'E', 'PR', 'DA', 'DB', 'K']
        card1_types = ['A', 'F', 'F', 'F', 'F', 'F', 'F']
        parsed_card1 = self.parser.parse_line(raw_lines[0], card1_types)
        data1 = dict(zip(card1_cols, parsed_card1))

        # Validation
        if data1['MID'] is None or data1['RO'] is None:
            raise ValueError("MID and RO are required fields.")

        if self.is_fluid:
            if data1['K'] is None or data1['K'] == 0.0:
                raise ValueError("K is required for FLUID option and cannot be 0.0.")
            data1.pop('E')
            data1.pop('PR')
            data1.pop('DA')
            data1.pop('DB')
        else:
            if data1['E'] is None:
                raise ValueError("E is required for non-FLUID option.")
            data1.pop('K')

        # Apply defaults
        if data1.get('PR') is None: data1['PR'] = 0.0
        if data1.get('DA') is None: data1['DA'] = 0.0
        if data1.get('DB') is None: data1['DB'] = 0.0
        if data1.get('K') is None: data1['K'] = 0.0

        self.cards['card1'] = pd.DataFrame([data1])

        if self.is_fluid:
            if len(raw_lines) < 2:
                raise ValueError("FLUID option requires a second card.")
            
            # Card 2
            card2_cols = ['VC', 'CP']
            card2_types = ['F', 'F']
            parsed_card2 = self.parser.parse_line(raw_lines[1], card2_types)
            data2 = dict(zip(card2_cols, parsed_card2))

            if data2['VC'] is None:
                raise ValueError("VC is required for FLUID option.")
            if data2['CP'] is None: data2['CP'] = 1.0e20

            self.cards['card2'] = pd.DataFrame([data2])

    def write(self, file_obj: TextIO):
        """Writes the keyword to a file."""
        file_obj.write(f"{self.keyword_line}\n")
        card1_df = self.cards.get('card1')
        if card1_df is not None and not card1_df.empty:
            row = card1_df.iloc[0]
            line = (
                self.parser.format_field(row.get('MID'), 'A') +
                self.parser.format_field(row.get('RO'), 'F') +
                self.parser.format_field(row.get('E'), 'F') +
                self.parser.format_field(row.get('PR'), 'F') +
                self.parser.format_field(row.get('DA'), 'F') +
                self.parser.format_field(row.get('DB'), 'F') +
                self.parser.format_field(row.get('K'), 'F')
            )
            file_obj.write(f"{line.rstrip()}\n")

        if self.is_fluid:
            card2_df = self.cards.get('card2')
            if card2_df is not None and not card2_df.empty:
                row = card2_df.iloc[0]
                line = (
                    self.parser.format_field(row.get('VC'), 'F') +
                    self.parser.format_field(row.get('CP'), 'F')
                )
                file_obj.write(f"{line.rstrip()}\n")
