"""Implementation of the *MAT_ELASTIC keyword."""

from typing import List, TextIO, Dict
import numpy as np
from .lsdyna_keyword import LSDynaKeyword


class MatElastic(LSDynaKeyword):
    """
    Represents a *MAT_ELASTIC keyword in an LS-DYNA input file.

    This keyword can appear as *MAT_ELASTIC or *MAT_001, with an
    optional _FLUID suffix for fluid material modeling.
    """

    keyword_string = "*MAT_ELASTIC"
    keyword_aliases = ["*MAT_001", "*MAT_ELASTIC_FLUID", "*MAT_001_FLUID"]

    # Card definitions
    CARD1_SOLID_COLS = ['MID', 'RO', 'E', 'PR', 'DA', 'DB']
    CARD1_SOLID_TYPES = ['A', 'F', 'F', 'F', 'F', 'F']
    CARD1_FLUID_COLS = ['MID', 'RO', 'K']
    CARD1_FLUID_TYPES = ['A', 'F', 'F']

    CARD2_COLS = ['VC', 'CP']
    CARD2_TYPES = ['F', 'F']

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        """Initialize the MatElastic keyword."""
        self.is_fluid = "_FLUID" in keyword_name.upper()
        super().__init__(keyword_name, raw_lines)

    def _parse_raw_data(self, raw_lines: List[str]):
        """Parse the raw data for *MAT_ELASTIC."""
        card_lines = self._extract_data_cards(raw_lines)

        if not card_lines:
            raise ValueError("*MAT_ELASTIC requires at least one data card.")

        # Parse Card 1
        card1_data = self._parse_card1(card_lines[0])
        self.cards['card1'] = self._convert_to_arrays(card1_data)

        # Parse Card 2 (only for fluid option)
        if self.is_fluid:
            if len(card_lines) < 2:
                raise ValueError("FLUID option requires a second card.")

            card2_data = self._parse_card2(card_lines[1])
            self.cards['card2'] = self._convert_to_arrays(card2_data)

    def _extract_data_cards(self, raw_lines: List[str]) -> List[str]:
        """Extract non-comment data cards from raw lines."""
        return [line for line in raw_lines[1:]
                if not line.strip().startswith('$')]

    def _parse_card1(self, line: str) -> Dict:
        """Parse Card 1 data based on fluid/solid configuration."""
        # Parse all fields first
        all_cols = ['MID', 'RO', 'E', 'PR', 'DA', 'DB', 'K']
        all_types = ['A', 'F', 'F', 'F', 'F', 'F', 'F']
        parsed_values = self.parser.parse_line(line, all_types)
        data = dict(zip(all_cols, parsed_values))

        # Validate required fields
        self._validate_card1(data)

        # Apply configuration-specific logic
        if self.is_fluid:
            return self._prepare_fluid_card1(data)
        else:
            return self._prepare_solid_card1(data)

    def _validate_card1(self, data: Dict):
        """Validate Card 1 required fields."""
        if data['MID'] is None or data['RO'] is None:
            raise ValueError("MID and RO are required fields.")

        if self.is_fluid:
            if data['K'] is None or data['K'] == 0.0:
                raise ValueError(
                    "K is required for FLUID option and cannot be 0.0.")
        else:
            if data['E'] is None:
                raise ValueError("E is required for non-FLUID option.")

    def _prepare_fluid_card1(self, data: Dict) -> Dict:
        """Prepare Card 1 data for fluid configuration."""
        return {
            'MID': data['MID'],
            'RO': data['RO'],
            'K': data['K']
        }

    def _prepare_solid_card1(self, data: Dict) -> Dict:
        """Prepare Card 1 data for solid configuration with defaults."""
        return {
            'MID': data['MID'],
            'RO': data['RO'],
            'E': data['E'],
            'PR': data.get('PR') or 0.0,
            'DA': data.get('DA') or 0.0,
            'DB': data.get('DB') or 0.0
        }

    def _parse_card2(self, line: str) -> Dict:
        """Parse Card 2 data for fluid configuration."""
        parsed_values = self.parser.parse_line(line, self.CARD2_TYPES)
        data = dict(zip(self.CARD2_COLS, parsed_values))

        if data['VC'] is None:
            raise ValueError("VC is required for FLUID option.")

        if data['CP'] is None:
            data['CP'] = 1.0e20

        return data

    def _convert_to_arrays(self, data: Dict) -> Dict:
        """Convert dictionary values to numpy arrays."""
        return {col: np.array([value], dtype=object)
                for col, value in data.items()}

    def write(self, file_obj: TextIO):
        """Write the keyword to a file."""
        file_obj.write(f"{self.full_keyword}\n")

        self._write_card1(file_obj)

        if self.is_fluid:
            self._write_card2(file_obj)

    def _write_card1(self, file_obj: TextIO):
        """Write Card 1 to file."""
        card1 = self.cards.get('card1')
        if not card1 or not self._has_data(card1):
            return

        if self.is_fluid:
            cols = self.CARD1_FLUID_COLS
            types = self.CARD1_FLUID_TYPES
            header_cols = cols
        else:
            cols = self.CARD1_SOLID_COLS
            types = self.CARD1_SOLID_TYPES
            header_cols = cols + ['K']

        # Write header
        file_obj.write(self.parser.format_header(header_cols))

        # Write data fields
        line_parts = [
            self.parser.format_field(card1.get(col, [None])[0], typ)
            for col, typ in zip(cols, types)
        ]
        file_obj.write("".join(line_parts))

        # Write K field for solid (as 0.0)
        if not self.is_fluid:
            file_obj.write(self.parser.format_field(0.0, 'F'))

        file_obj.write("\n")

    def _write_card2(self, file_obj: TextIO):
        """Write Card 2 to file (fluid only)."""
        card2 = self.cards.get('card2')
        if not card2 or not self._has_data(card2):
            return

        # Write header
        file_obj.write(self.parser.format_header(self.CARD2_COLS))

        # Write data fields
        line_parts = [
            self.parser.format_field(card2.get(col, [None])[0], typ)
            for col, typ in zip(self.CARD2_COLS, self.CARD2_TYPES)
        ]
        file_obj.write("".join(line_parts))
        file_obj.write("\n")

    def _has_data(self, card: Dict) -> bool:
        """Check if a card dictionary contains data."""
        return len(next(iter(card.values()))) > 0
