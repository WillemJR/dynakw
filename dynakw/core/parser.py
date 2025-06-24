"""Parser for LS-DYNA keyword files"""

import re
import pandas as pd
import logging
from typing import List, Iterator, Tuple, Optional
from .enums import KeywordType
from ..keywords.lsdyna_keyword import LSDynaKeyword
from ..utils.format_parser import FormatParser
from ..utils.logger import get_logger
from ..keywords.NODE import Node
from ..keywords.BOUNDARY_PRESCRIBED_MOTION import BoundaryPrescribedMotion
from ..keywords.ELEMENT_SOLID import ElementSolid
from ..keywords.ELEMENT_SHELL import ElementShell
from ..keywords.PART import Part
from ..keywords.MAT_ELASTIC import MatElastic
from ..keywords.UNKNOWN import Unknown



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
        keyword_map['*ELEMENT_SHELL'] = KeywordType.ELEMENT_SHELL
        keyword_map['*MAT'] = KeywordType.MATERIAL
        keyword_map['*MATERIAL'] = KeywordType.MATERIAL
        keyword_map['*SECTION_SOLID'] = KeywordType.SECTION_SOLID
        keyword_map['*CONTROL_TERMINATION'] = KeywordType.CONTROL_TERMINATION
        keyword_map['*PART'] = KeywordType.PART

        # MAT_ELASTIC and its aliases
        keyword_map['*MAT_ELASTIC_FLUID'] = KeywordType.MAT_ELASTIC
        keyword_map['*MAT_001_FLUID'] = KeywordType.MAT_ELASTIC
        keyword_map['*MAT_ELASTIC'] = KeywordType.MAT_ELASTIC
        keyword_map['*MAT_001'] = KeywordType.MAT_ELASTIC
        
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
    
    def parse_keyword_block(self, lines: List[str]) -> LSDynaKeyword:
        """Parse a complete keyword block, ignoring comment lines."""
        if not lines:
            return DynaKeyword(KeywordType.UNKNOWN)

        # Filter out comment lines (starting with '$')
        filtered_lines = [line for line in lines if not line.strip().startswith("$")]

        if not filtered_lines:
            # The block may have only contained comments
            return DynaKeyword(KeywordType.UNKNOWN)

        keyword_line = filtered_lines[0]
        keyword_type, _ = self.parse_keyword_line(keyword_line)

        if keyword_type in [
            KeywordType.BOUNDARY_PRESCRIBED_MOTION,
            KeywordType.BOUNDARY_PRESCRIBED_MOTION_NODE,
            KeywordType.BOUNDARY_PRESCRIBED_MOTION_SET,
        ]:
            return BoundaryPrescribedMotion(keyword_line, filtered_lines)
        elif keyword_type == KeywordType.NODE:
            return Node(keyword_line, filtered_lines)
        elif keyword_type == KeywordType.ELEMENT_SOLID:
            return ElementSolid(keyword_line, filtered_lines)
        elif keyword_type == KeywordType.ELEMENT_SHELL:
            return ElementShell(keyword_line, filtered_lines)
        elif keyword_type == KeywordType.PART:
            return Part(keyword_line, filtered_lines)
        elif keyword_type == KeywordType.MAT_ELASTIC:
            return MatElastic(keyword_line, filtered_lines)
        elif keyword_type == KeywordType.UNKNOWN:
            return Unknown(keyword_line, filtered_lines[1:])
        else:
            # It's a known keyword type, but no specific class for it.
            # Treat as "Unknown" but try to parse its fields.
            keyword = Unknown(keyword_line, filtered_lines[1:])
            data_lines = filtered_lines[1:]
            try:
                self._parse_generic(keyword, data_lines)
            except Exception as e:
                self.logger.error(f"Error parsing generically {keyword_type}: {e}")
            return keyword

    def _parse_generic(self, keyword: Unknown, data_lines: List[str]):
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

