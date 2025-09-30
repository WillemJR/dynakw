"""Implementation of the *NODE keyword."""

from typing import TextIO, List
import numpy as np
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword


class Node(LSDynaKeyword):
    """
    Implements the *NODE keyword.
    """
    keyword_string = "*NODE"
    flen = [8, 16, 16, 16, 8, 8]

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        super().__init__(keyword_name, raw_lines)

    def _parse_raw_data(self, raw_lines: List[str]):
        """
        Parses the raw data for *NODE.
        Handles both standard and long formats for coordinates.
        """
        card_lines = [line for line in raw_lines[1:]
                      if not line.strip().startswith('$')]

        columns = ['NID', 'X', 'Y', 'Z', 'TC', 'RC']
        field_types = ['I', 'F', 'F', 'F', 'I', 'I']

        # Map field_types to numpy dtypes
        dtype_map = {'I': np.int32, 'F': np.float64}
        col_dtypes = [dtype_map[ft] for ft in field_types]

        parsed_data = []
        for line in card_lines:
            # Heuristic to detect long format: check line length.
            long_format = len(line.rstrip()) > 80
            parsed_fields = self.parser.parse_line(
                line, field_types, field_len=Node.flen, long_format=long_format)
            if any(field is not None for field in parsed_fields):
                parsed_data.append(parsed_fields[:len(columns)])

        # Store as dictionary of numpy arrays with correct dtype
        if parsed_data:
            arr = np.array(parsed_data)
            self.cards['Card 1'] = {
                col: arr[:, i].astype(col_dtypes[i], copy=False) for i, col in enumerate(columns)
            }
        else:
            self.cards['Card 1'] = {
                col: np.array([], dtype=col_dtypes[i]) for i, col in enumerate(columns)
            }

    def write(self, file_obj: TextIO):
        """
        Writes the *NODE keyword to a file.
        """
        file_obj.write(f"{self.full_keyword}\n")

        card = self.cards.get('Card 1')
        if card is None or len(card['NID']) == 0:
            return

        field_types = ['I', 'F', 'F', 'F', 'I', 'I']
        long_format = getattr(self, 'long_format', False)
        columns = ['NID', 'X', 'Y', 'Z', 'TC', 'RC']

        n_rows = len(card['NID'])
        for idx in range(n_rows):
            line_parts = []
            for i, col in enumerate(columns):
                value = card[col][idx]
                field_str = self.parser.format_field(
                    value, field_types[i], long_format=long_format, field_len=Node.flen[i])
                line_parts.append(field_str)
            file_obj.write(f"{''.join(line_parts)}\n")
