"""Main class for handling LS-DYNA keyword files"""

import os
import re
from typing import List, Iterator, Optional, TextIO
from pathlib import Path
from .parser import DynaParser
from .keyword import DynaKeyword
from .enums import KeywordType
from ..utils.logger import get_logger

class DynaKeywordFile:
    """Main class for reading and writing LS-DYNA keyword files"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.keywords: List[DynaKeyword] = []
        self.parser = DynaParser()
        self.logger = get_logger(__name__)
        self._include_files: List[str] = []
        
    def read_all(self, follow_include: bool = False):
        """Read all keywords from the file"""
        self.keywords.clear()
        self._include_files.clear()
        
        with open(self.filename, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        self._parse_content(content, follow_include)
        
    def _parse_content(self, content: str, follow_include: bool):
        """Parse file content into keywords"""
        lines = content.split('\n')
        current_keyword_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # Check for include files
            if follow_include and line.strip().upper().startswith('*INCLUDE'):
                include_file = self._extract_include_filename(line)
                if include_file:
                    self._process_include_file(include_file, follow_include)
                i += 1
                continue
            
            # Check if this is a keyword line
            if line.startswith('*') and not line.startswith('$'):
                # Process previous keyword if exists
                if current_keyword_lines:
                    keyword = self.parser.parse_keyword_block(current_keyword_lines)
                    self.keywords.append(keyword)
                
                # Start new keyword
                current_keyword_lines = [line]
            else:
                # Add line to current keyword (including comments and data)
                if current_keyword_lines:  # Only if we're inside a keyword
                    current_keyword_lines.append(line)
            
            i += 1
        
        # Process last keyword
        if current_keyword_lines:
            keyword = self.parser.parse_keyword_block(current_keyword_lines)
            self.keywords.append(keyword)
    
    def _extract_include_filename(self, line: str) -> Optional[str]:
        """Extract filename from *INCLUDE line"""
        # Simple regex to extract filename
        match = re.search(r'["\']([^"\']+)["\']', line)
        if match:
            return match.group(1)
        
        # Try without quotes
        parts = line.split()
        if len(parts) > 1:
            return parts[1]
        
        return None
    
    def _process_include_file(self, include_file: str, follow_include: bool):
        """Process an included file"""
        # Make path relative to current file
        base_dir = os.path.dirname(self.filename)
        full_path = os.path.join(base_dir, include_file)
        
        try:
            if os.path.exists(full_path):
                self._include_files.append(full_path)
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    include_content = f.read()
                self._parse_content(include_content, follow_include)
            else:
                self.logger.warning(f"Include file not found: {full_path}")
        except Exception as e:
            self.logger.error(f"Error reading include file {full_path}: {e}")
    
    def next_kw(self) -> Iterator[DynaKeyword]:
        """Iterator over keywords"""
        for keyword in self.keywords:
            yield keyword
    
    def write(self, filename: str):
        """Write all keywords to a file"""
        with open(filename, 'w', encoding='utf-8') as f:
            for keyword in self.keywords:
                keyword.write(f)
                f.write('\n')  # Add blank line between keywords
    
    def find_keywords(self, keyword_type: KeywordType) -> List[DynaKeyword]:
        """Find all keywords of a specific type"""
        return [kw for kw in self.keywords if kw.type == keyword_type]
