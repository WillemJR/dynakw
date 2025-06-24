"""Implementation of the *NODE keyword."""

from typing import TextIO, List
import pandas as pd
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.enums import KeywordType

class Node(LSDynaKeyword):
    """
    Implements the *NODE keyword.
    """

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        super().__init__(keyword_name, raw_lines)
        if self.keyword_type != KeywordType.NODE:
            pass

    def _parse_raw_data(self, raw_lines: List[str]):
        """
        Parses the raw data for *NODE.
        Handles both standard and long formats for coordinates.
        """
        card_lines = [line for line in raw_lines[1:] if not line.strip().startswith('$')]

        columns = ['NID', 'X', 'Y', 'Z', 'TC', 'RC']
        field_types = ['I', 'F', 'F', 'F', 'I', 'I']
        flen = [8, 16, 16,  16, 8, 8 ]
        
        parsed_data = []
        for line in card_lines:
            # Heuristic to detect long format: check line length.
            long_format = len(line.rstrip()) > 80
            parsed_fields = self.parser.parse_line(line, field_types, field_len=flen, long_format=long_format )
            if any(field is not None for field in parsed_fields):
                parsed_data.append(parsed_fields[:len(columns)])

        self.cards['Card 1'] = pd.DataFrame(parsed_data, columns=columns)

    def write(self, file_obj: TextIO):
        """
        Writes the *NODE keyword to a file.
        """
        file_obj.write(f"{self.full_keyword}\n")

        df = self.cards.get('Card 1')
        if df is None or df.empty:
            return

        field_types = ['I', 'F', 'F', 'F', 'I', 'I']
        
        long_format = getattr(self, 'long_format', False)

        for _, row in df.iterrows():
            line_parts = []
            for i, col in enumerate(df.columns):
                value = row[col]
                field_str = self.parser.format_field(value, field_types[i], long_format=long_format)
                line_parts.append(field_str)
            file_obj.write(f"{''.join(line_parts)}\n")
