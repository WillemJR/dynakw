"""Implementation of the *BOUNDARY_PRESCRIBED_MOTION keyword."""

from typing import TextIO, List
import numpy as np
from dynakw.keywords.lsdyna_keyword import LSDynaKeyword
from dynakw.core.enums import KeywordType

class BoundaryPrescribedMotion(LSDynaKeyword):
    """
    Implements the *BOUNDARY_PRESCRIBED_MOTION keyword.
    """
    keyword_string = "*BOUNDARY_PRESCRIBED_MOTION"
    keyword_aliases = ["*BOUNDARY_PRESCRIBED_MOTION_NODE", "*BOUNDARY_PRESCRIBED_MOTION_SET"]


    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        super().__init__(keyword_name, raw_lines)
        # The base keyword type is set from parsing, but we can assert it here
        if self.keyword_type not in [
            KeywordType.BOUNDARY_PRESCRIBED_MOTION,
            KeywordType.BOUNDARY_PRESCRIBED_MOTION_NODE,
            KeywordType.BOUNDARY_PRESCRIBED_MOTION_SET,
        ]:
            # Or handle cases where _NODE/_SET might be separate enums
            pass

    def _parse_raw_data(self, raw_lines: List[str]):
        """
        Parses the raw data for *BOUNDARY_PRESCRIBED_MOTION.
        Handles multiple card formats based on keyword options.
        """
        card_lines = raw_lines[1:]

        # Determine format based on options
        option = self.options[0].upper() if self.options else ''
        if 'NODE' in option or 'SET' in option:
            columns = ['ID', 'DOF', 'VAD', 'LCID', 'SF', 'VID']
            field_types = ['I', 'I', 'I', 'I', 'F', 'I']
        else:
            columns = ['ID', 'DOF', 'VAD', 'LCID', 'SF', 'VID', 'DEATH', 'BIRTH']
            field_types = ['I', 'I', 'I', 'I', 'F', 'I', 'F', 'F']

        parsed_data = []
        for line in card_lines:
            parsed_fields = self.parser.parse_line(line, field_types, long_format=False)
            if any(field is not None for field in parsed_fields):
                # Trim None values from the end that are beyond the expected fields
                parsed_data.append(parsed_fields[:len(columns)])

        # Save as dictionary: {column: np.array(values)}
        card_dict = {col: np.array([row[i] for row in parsed_data], dtype=object) for i, col in enumerate(columns)}
        self.cards['Card 1'] = card_dict

    def write(self, file_obj: TextIO):
        """
        Writes the *BOUNDARY_PRESCRIBED_MOTION keyword to a file.
        """
        file_obj.write(f"{self.full_keyword}\n")

        card = self.cards.get('Card 1')
        if card is None or not isinstance(card, dict) or not card:
            return

        columns = list(card.keys())
        data_length = len(next(iter(card.values()))) if card else 0
        if data_length == 0:
            return

        # Determine field types based on columns
        if 'DEATH' in columns:
            field_types = ['I', 'I', 'I', 'I', 'F', 'I', 'F', 'F']
        else:
            field_types = ['I', 'I', 'I', 'I', 'F', 'I']

        for idx in range(data_length):
            line_parts = []
            for i, col in enumerate(columns):
                value = card[col][idx]
                field_str = self.parser.format_field(value, field_types[i], long_format=False)
                line_parts.append(field_str)
            file_obj.write(f"{''.join(line_parts)}\n")
