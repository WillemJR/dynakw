"""Parser for LS-DYNA keyword files"""

import re
import pandas as pd
import logging
from typing import List, Iterator, Tuple, Optional
from .keyword import DynaKeyword
from .enums import KeywordType
from ..utils.format_parser import FormatParser
from ..utils.logger import get_logger
from ..keywords.node import Node
from ..keywords.BOUNDARY_PRESCRIBED_MOTION import BoundaryPrescribedMotion

class DynaParser:
    """Parser for LS-DYNA keyword files"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.format_parser = FormatParser()
        self._keyword_map = self._build_keyword_map()
        
    def _build_keyword_map(self) -> dict:
        """Build mapping from keyword strings to KeywordType enums"""
        keyword_map = {}
        
        # Add all keyword variations
        keyword_map['*BOUNDARY_PRESCRIBED_MOTION'] = KeywordType.BOUNDARY_PRESCRIBED_MOTION
        keyword_map['*BOUNDARY_PRESCRIBED_MOTION_NODE'] = KeywordType.BOUNDARY_PRESCRIBED_MOTION_NODE
        keyword_map['*BOUNDARY_PRESCRIBED_MOTION_SET'] = KeywordType.BOUNDARY_PRESCRIBED_MOTION_SET
        keyword_map['*NODE'] = KeywordType.NODE
        keyword_map['*ELEMENT_SOLID'] = KeywordType.ELEMENT_SOLID
        keyword_map['*MAT'] = KeywordType.MATERIAL
        keyword_map['*MATERIAL'] = KeywordType.MATERIAL
        keyword_map['*SECTION_SOLID'] = KeywordType.SECTION_SOLID
        keyword_map['*CONTROL_TERMINATION'] = KeywordType.CONTROL_TERMINATION
        
        return keyword_map
    
    def parse_keyword_line(self, line: str) -> Tuple[KeywordType, str]:
        """Parse a keyword line and return the type and options"""
        line = line.strip()
        
        # Remove format modifiers
        clean_line = line.rstrip('+-% ')
        
        # Find the longest matching keyword
        best_match = None
        best_length = 0
        
        for keyword_str, keyword_type in self._keyword_map.items():
            if clean_line.startswith(keyword_str):
                if len(keyword_str) > best_length:
                    best_match = keyword_type
                    best_length = len(keyword_str)
        
        if best_match:
            return best_match, line
        else:
            self.logger.warning(f"Unknown keyword: {line}")
            return KeywordType.UNKNOWN, line
    
    def parse_keyword_block(self, lines: List[str]) -> DynaKeyword:
        """Parse a complete keyword block"""
        if not lines:
            return DynaKeyword(KeywordType.UNKNOWN)

        keyword_line = lines[0]
        keyword_type, _ = self.parse_keyword_line(keyword_line)

        if keyword_type in [
            KeywordType.BOUNDARY_PRESCRIBED_MOTION,
            KeywordType.BOUNDARY_PRESCRIBED_MOTION_NODE,
            KeywordType.BOUNDARY_PRESCRIBED_MOTION_SET,
        ]:
            return BoundaryPrescribedMotion(keyword_line, lines)
        elif keyword_type == KeywordType.NODE:
            return Node(keyword_line, lines)
        else:
            # Generic parsing for other keyword types
            keyword = DynaKeyword(keyword_type, '\n'.join(lines))
            data_lines = lines[1:]
            try:
                if keyword_type == KeywordType.ELEMENT_SOLID:
                    self._parse_element_solid(keyword, data_lines)
                else:
                    self._parse_generic(keyword, data_lines)
            except Exception as e:
                self.logger.error(f"Error parsing {keyword_type}: {e}")
                keyword.type = KeywordType.UNKNOWN
            return keyword
    
    def _parse_element_solid(self, keyword: DynaKeyword, data_lines: List[str]):
        """Parse ELEMENT_SOLID keyword"""
        if not data_lines:
            return
            
        element_data = []
        for line in data_lines:
            if line.strip():
                values = self.format_parser.parse_line(line, ['I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'I'])
                element_data.append(values)
        
        if element_data:
            df = pd.DataFrame(element_data, columns=['EID', 'PID', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8'])
            keyword.add_card('Card1', df)
    
    def _parse_generic(self, keyword: DynaKeyword, data_lines: List[str]):
        """Generic parsing for unknown keyword structures"""
        if not data_lines:
            return
            
        # Try to parse as generic numeric data
        card_data = []
        for line in data_lines:
            if line.strip():
                # Try to parse each field as either int or float
                values = self.format_parser.parse_line_generic(line)
                card_data.append(values)
        
        if card_data:
            # Create column names based on number of fields
            max_cols = max(len(row) for row in card_data) if card_data else 0
            columns = [f'Field_{i+1}' for i in range(max_cols)]
            
            # Pad short rows with None
            for row in card_data:
                while len(row) < max_cols:
                    row.append(None)
            
            df = pd.DataFrame(card_data, columns=columns)
            keyword.add_card('Card1', df)

