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
from ..keywords.SECTION_SOLID import SectionSolid
from ..keywords.SECTION_SHELL import SectionShell
from ..keywords.UNKNOWN import Unknown



class DynaParser:
    """Parser for LS-DYNA keyword files"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.format_parser = FormatParser()
        self._keyword_map = LSDynaKeyword.KEYWORD_MAP
    
    def parse_keyword_line(self, line: str) -> Tuple[Optional[LSDynaKeyword], str]:
        """Parse a keyword line and return the type and options"""
        line = line.strip()
        
        # Remove format modifiers
        clean_line = line.rstrip('+-% ')
        
        # Find the longest matching keyword
        best_match = None
        best_length = 0
        
        for keyword_str, keyword_class in self._keyword_map.items():
            if clean_line.startswith(keyword_str):
                if len(keyword_str) > best_length:
                    best_match = keyword_class
                    best_length = len(keyword_str)
        
        if best_match:
            return best_match, line
        else:
            self.logger.warning(f"Unknown keyword: {line}")
            return None, line
    
    def parse_keyword_block(self, lines: List[str]) -> LSDynaKeyword:
        """Parse a complete keyword block, ignoring comment lines."""
        if not lines:
            return Unknown("", lines)

        # Filter out comment lines (starting with '$')
        filtered_lines = [line for line in lines if not line.strip().startswith("$")]

        if not filtered_lines:
            # The block may have only contained comments
            return Unknown("", lines)

        keyword_line = filtered_lines[0]
        keyword_class, _ = self.parse_keyword_line(keyword_line)

        if keyword_class:
            return keyword_class(keyword_line, filtered_lines)
        else:
            return Unknown(keyword_line, filtered_lines[1:])

