import os
import re
from typing import List, Iterator, Optional, TextIO, Tuple
from pathlib import Path
import pandas as pd
import logging
from ..keywords.lsdyna_keyword import LSDynaKeyword
from .enums import KeywordType
from ..utils.logger import get_logger
from ..utils.format_parser import FormatParser
from ..keywords.UNKNOWN import Unknown


class DynaKeywordFile:
    """Main class for reading and writing LS-DYNA keyword files"""

    def __init__(self, filename: str, follow_include: bool = False):
        self.filename = filename
        self.keywords: List[LSDynaKeyword] = []
        self.logger = get_logger(__name__)
        self.format_parser = FormatParser()
        self._keyword_map = LSDynaKeyword.KEYWORD_MAP
        self._include_files: List[str] = []
        self.read_all(follow_include=follow_include)

    def _parse_keyword_name(self, line: str) -> Tuple[Optional[LSDynaKeyword], str]:
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

    def _parse_keyword_block(self, lines: List[str]) -> LSDynaKeyword:
        """Parse a complete keyword block, ignoring comment lines."""
        if not lines:
            return Unknown("", lines)

        # Filter out comment lines (starting with '$')
        filtered_lines = [line for line in lines if not line.strip().startswith("$")]

        if not filtered_lines:
            # The block may have only contained comments
            return Unknown("", lines)

        keyword_line = filtered_lines[0]
        keyword_class, _ = self._parse_keyword_name(keyword_line)

        if keyword_class:
            return keyword_class(keyword_line, filtered_lines)
        else:
            return Unknown(keyword_line, filtered_lines[1:])

    def read_all(self, follow_include: bool = False):
        """Read all keywords from the file"""
        self.keywords.clear()
        self._include_files.clear()

        line_iterator = self._line_iterator(self.filename, follow_include)
        self._parse_content_from_iterator(line_iterator)

    def _line_iterator(self, filepath: str, follow_include: bool) -> Iterator[str]:
        """A generator that yields lines from a file, following *INCLUDE directives."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    rstripped_line = line.rstrip()
                    if follow_include and rstripped_line.strip().upper().startswith('*INCLUDE'):
                        include_file = self._extract_include_filename(rstripped_line)
                        if include_file:
                            base_dir = os.path.dirname(filepath)
                            full_path = os.path.join(base_dir, include_file)
                            if os.path.exists(full_path):
                                self._include_files.append(full_path)
                                yield from self._line_iterator(full_path, follow_include)
                            else:
                                self.logger.warning(f"Include file not found: {full_path}")
                    else:
                        yield rstripped_line
        except FileNotFoundError:
            self.logger.error(f"File not found: {filepath}")
        except Exception as e:
            self.logger.error(f"Error reading file {filepath}: {e}")

    def _parse_content_from_iterator(self, lines_iterator: Iterator[str]):
        """Parse file content from an iterator of lines into keywords"""
        current_keyword_lines = []

        for line in lines_iterator:
            # Check if this is a keyword line
            if line.startswith('*') and not line.startswith('$'):
                # Process previous keyword if exists
                if current_keyword_lines:
                    keyword = self._parse_keyword_block(current_keyword_lines)
                    self.keywords.append(keyword)

                # Start new keyword
                current_keyword_lines = [line]
            else:
                # Add line to current keyword (including comments and data)
                if current_keyword_lines:  # Only if we're inside a keyword
                    current_keyword_lines.append(line)

        # Process last keyword
        if current_keyword_lines:
            keyword = self._parse_keyword_block(current_keyword_lines)
            self.keywords.append(keyword)

    def _extract_include_filename(self, line: str) -> Optional[str]:
        """Extract filename from *INCLUDE line"""
        # Simple regex to extract filename
        match = re.search(r'["\\]([^"\\]+)["\\]', line)
        if match:
            return match.group(1)

        # Try without quotes
        parts = line.split()
        if len(parts) > 1:
            return parts[1]

        return None

    def next_kw(self) -> Iterator[LSDynaKeyword]:
        """Iterator over keywords"""
        for keyword in self.keywords:
            yield keyword

    def write(self, filename: str):
        """Write all keywords to a file"""
        with open(filename, 'w', encoding='utf-8') as f:
            for keyword in self.keywords:
                keyword.write(f)

    def find_keywords(self, keyword_type: KeywordType) -> List[LSDynaKeyword]:
        """Find all keywords of a specific type"""
        return [kw for kw in self.keywords if kw.type == keyword_type]