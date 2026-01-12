import os
import re
from typing import List, Iterator, Optional, Tuple, Dict, Any, Union
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

            keyword_line = filtered_lines[0].upper()
            keyword_class, _ = self._parse_keyword_name(keyword_line)

            if keyword_class:
                return keyword_class(keyword_line, filtered_lines)
            else:
                return Unknown(keyword_line, filtered_lines[1:])
        except Exception as e:
            self.logger.error(f"Error {e} reading: \"{lines[0]}\"")
            return Unknown("*UNKNOWN", [ 'Parsing failed' ])

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
        
    def _substitute_parameters_in_card(self, card: Dict[str, Any], updates_normalized: Dict[str, Any], key_pairs: List[Tuple[str, str]], context_name: str = "PARAMETER"):
        """
        Substitutes values in a card based on parameter names.

        Args:
            card (dict): The card dictionary (column name -> data array).
            updates_normalized (dict): Mapping of lowercase parameter name to new value.
            key_pairs (list): List of tuples (parameter_column_name, value_column_name).
            context_name (str): Name for logging purposes.
        """
        if not card:
            return

        # Use the first parameter column to determine number of rows
        # We assume standard LS-DYNA card structure where columns are aligned
        # However, we must ensure at least one key pair is provided and exists to check length
        if not key_pairs:
            return

        # Try to find a valid key to determine rows. 
        # Usually the first PRMR column is a good candidate.
        first_prmr_key = key_pairs[0][0]
        if first_prmr_key not in card:
            return

        num_rows = len(card[first_prmr_key])

        for r in range(num_rows):
            for prmr_key, val_key in key_pairs:
                # Ensure columns exist in the card data
                if prmr_key in card and val_key in card:
                    p_name = card[prmr_key][r]
                    
                    if p_name:
                        p_name_str = str(p_name).strip()
                        p_name_lower = p_name_str.lower()
                        
                        if p_name_lower in updates_normalized:
                            new_val = updates_normalized[p_name_lower]
                            old_val = card[val_key][r]
                            card[val_key][r] = new_val
                            self.logger.info(f"[{context_name}] Updated {p_name_str}: {old_val} -> {new_val}")

    def edit_parameters(self, params_update_dict: Dict[str, Union[str, float, int]]):
        """
        Updates parameters in the file based on the dictionary.
        
        Args:
            params_update_dict (dict): Dictionary where keys are parameter names (str)
                                    and values are the new values (float, int, str).
                                    Keys are matched case-insensitively.
        """
        # Normalize dictionary keys to lower case for case-insensitive matching
        updates_normalized = {k.lower(): v for k, v in params_update_dict.items()}

        # Loop through all keywords
        for kw in self.keywords():
            
            # --- Handle *PARAMETER ---
            if kw.type == KeywordType.PARAMETER:
                self.logger.debug(f"Found *PARAMETER keyword at line {kw._start_line if hasattr(kw, '_start_line') else 'unknown'}")
                
                card1 = kw.cards.get('Card 1')
                # *PARAMETER has up to 4 pairs per row: PRMR1, VAL1, ..., PRMR4, VAL4
                key_pairs = [(f"PRMR{i}", f"VAL{i}") for i in range(1, 5)]
                self._substitute_parameters_in_card(card1, updates_normalized, key_pairs, "PARAMETER")

            # --- Handle *PARAMETER_EXPRESSION ---
            elif kw.type == KeywordType.PARAMETER_EXPRESSION:
                self.logger.debug(f"Found *PARAMETER_EXPRESSION keyword")
                
                card1 = kw.cards.get('Card 1')
                # *PARAMETER_EXPRESSION has PRMR1 and EXPRESSION1
                key_pairs = [("PRMR1", "EXPRESSION1")]
                self._substitute_parameters_in_card(card1, updates_normalized, key_pairs, "PARAMETER_EXPRESSION")