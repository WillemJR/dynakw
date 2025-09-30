import os
import re
from typing import List, Iterator, Optional, Tuple
import logging
from ..keywords.lsdyna_keyword import LSDynaKeyword
from .enums import KeywordType
from ..utils.logger import get_logger
from ..utils.format_parser import FormatParser
from ..keywords.UNKNOWN import Unknown


class DynaKeywordReader:
    """Main class for reading and writing LS-DYNA keyword files"""

    def __init__(self, filename: str, follow_include: bool = False, debug: bool = False):
        self.filename = filename
        self._keywords: List[LSDynaKeyword] = []
        self.logger = get_logger(__name__)
        self.format_parser = FormatParser()
        self._keyword_map = LSDynaKeyword.KEYWORD_MAP
        self._include_files: List[str] = []
        self.follow_include = follow_include
        self._keyword_generator: Optional[Iterator[LSDynaKeyword]] = None
        self._fully_parsed: bool = False
        self.debug = debug
        if self.debug:
            self.logger.setLevel(logging.DEBUG)

    def __enter__(self):
        """Allow the class to be used as a context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Write the keywords back to the file on exit."""
        # if exc_type is None:
        #    self.write(self.filename)
        pass

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

        if self.debug:
            self.logger.debug(f"Reading block start with: {lines[0]}")

        try:
            # Filter out comment lines (starting with '$')
            filtered_lines = [
                line for line in lines if not line.strip().startswith("$")]

            if not filtered_lines:
                # The block may have only contained comments
                return Unknown("", lines)

            keyword_line = filtered_lines[0]
            keyword_class, _ = self._parse_keyword_name(keyword_line)

            if keyword_class:
                return keyword_class(keyword_line, filtered_lines)
            else:
                return Unknown(keyword_line, filtered_lines[1:])
        except Exception as e:
            self.logger.error(f"Error {e} reading:\n{lines[0]}")

    def _create_keyword_generator(self):
        """Creates a generator that yields keywords from the file."""
        def gen() -> Iterator[LSDynaKeyword]:
            line_iterator = self._line_iterator(
                self.filename, self.follow_include)
            current_keyword_lines = []
            for line in line_iterator:
                if line.startswith('*') and not line.startswith('$'):
                    if current_keyword_lines:
                        yield self._parse_keyword_block(current_keyword_lines)
                    current_keyword_lines = [line]
                else:
                    if current_keyword_lines:
                        current_keyword_lines.append(line)
            if current_keyword_lines:
                yield self._parse_keyword_block(current_keyword_lines)
            self._fully_parsed = True

        self._keyword_generator = gen()

    def _read_all(self, follow_include: any = None):
        """Read all keywords from the file"""
        if self._fully_parsed:
            return

        if follow_include is not None and follow_include != self.follow_include:
            self._keywords.clear()
            self._include_files.clear()
            self.follow_include = follow_include
            self._keyword_generator = None
            self._fully_parsed = False

        if self._keyword_generator is None:
            self._create_keyword_generator()

        for keyword in self._keyword_generator:
            self._keywords.append(keyword)

    def _line_iterator(self, filepath: str, follow_include: bool) -> Iterator[str]:
        """A generator that yields lines from a file, following *INCLUDE directives."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    rstripped_line = line.rstrip()
                    if follow_include and rstripped_line.strip().upper().startswith('*INCLUDE'):
                        include_file = self._extract_include_filename(
                            rstripped_line)
                        if include_file:
                            base_dir = os.path.dirname(filepath)
                            full_path = os.path.join(base_dir, include_file)
                            if os.path.exists(full_path):
                                self._include_files.append(full_path)
                                yield from self._line_iterator(full_path, follow_include)
                            else:
                                self.logger.warning(
                                    f"Include file not found: {full_path}")
                    else:
                        yield rstripped_line
        except FileNotFoundError:
            self.logger.error(f"File not found: {filepath}")
        except Exception as e:
            self.logger.error(f"Error reading file {filepath}: {e}")

    def _extract_include_filename(self, line: str) -> Optional[str]:
        """Extract filename from *INCLUDE line"""
        # Simple regex to extract filename
        match = re.search(r'["\\](["\\][^"\\]+)["\\]', line)
        if match:
            return match.group(1)

        # Try without quotes
        parts = line.split()
        if len(parts) > 1:
            return parts[1]

        return None

    def keywords(self) -> Iterator[LSDynaKeyword]:
        """Iterator over keywords, reading from the file as needed."""
        def iterator_gen():
            i = 0
            while True:
                if i < len(self._keywords):
                    yield self._keywords[i]
                    i += 1
                elif not self._fully_parsed:
                    if self._keyword_generator is None:
                        self._create_keyword_generator()
                    try:
                        next_keyword = next(self._keyword_generator)
                        self._keywords.append(next_keyword)
                    except StopIteration:
                        break
                else:
                    break
        return iterator_gen()

    def write(self, filename: str):
        """Write all keywords to a file"""
        if not self._fully_parsed:
            self._read_all()
        with open(filename, 'w', encoding='utf-8') as f:
            for keyword in self._keywords:
                if self.debug:
                    self.logger.debug(f"Writing block: {keyword.type}")
                try:
                    keyword.write(f)
                except Exception as e:
                    self.logger.error(f"Error {e} writing:\n{keyword.type}")

    def find_keywords(self, keyword_type: KeywordType) -> List[LSDynaKeyword]:
        """Find all keywords of a specific type"""
        if not self._fully_parsed:
            self._read_all()
        return [kw for kw in self._keywords if kw.type == keyword_type]
