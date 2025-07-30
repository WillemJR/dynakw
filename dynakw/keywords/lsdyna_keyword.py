"""Abstract base class for all LS-DYNA keyword objects."""

from collections import OrderedDict
from abc import ABC, abstractmethod
from typing import TextIO, List, Dict, Tuple
import numpy as np
from dynakw.core.enums import KeywordType
from dynakw.utils.format_parser import FormatParser

class LSDynaKeyword(ABC):
    """
    Base class for all LS-DYNA keyword objects.

    This class provides the basic structure for representing an LS-DYNA
    keyword, including methods for parsing from raw text and writing
    back to a file format.
    """

    KEYWORD_MAP: Dict[str, "LSDynaKeyword"] = OrderedDict()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, 'keyword_string'):
            cls.KEYWORD_MAP[cls.keyword_string] = cls
        if hasattr(cls, 'keyword_aliases'):
            for alias in cls.keyword_aliases:
                cls.KEYWORD_MAP[alias] = cls

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        """
        Initializes the LSDynaKeyword object.

        Args:
            keyword_name (str): The full name of the keyword (e.g., "*BOUNDARY_PRESCRIBED_MOTION_NODE").
            raw_lines (List[str], optional): The raw text lines for the keyword. Defaults to None.
        """
        self.full_keyword = keyword_name.strip()
        self.keyword_type, self.options = self._parse_keyword_name(self.full_keyword)
        self.cards: Dict[str, np.array] = {}
        self.parser = FormatParser()

        if raw_lines:
            self._parse_raw_data(raw_lines)

    @staticmethod
    def _parse_keyword_name(keyword_name: str) -> Tuple[KeywordType, List[str]]:
        """
        Parses the keyword name to extract the base type and options.
        Example: "*BOUNDARY_PRESCRIBED_MOTION_NODE" -> (KeywordType.BOUNDARY_PRESCRIBED_MOTION, ["NODE"])
        """
        # Remove leading '*' and split by '_'
        parts = keyword_name.strip()[1:].split('_')

        # Find the longest matching enum name
        for i in range(len(parts), 0, -1):
            base_keyword_str = '_'.join(parts[:i])
            try:
                keyword_type = KeywordType[base_keyword_str]
                options = parts[i:]
                return keyword_type, options
            except KeyError:
                continue

        return KeywordType.UNKNOWN, parts

    @abstractmethod
    def _parse_raw_data(self, raw_lines: List[str]):
        """
        Parses the raw data lines and populates the internal DataFrame(s).
        This method must be implemented by subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def write(self, file_obj: TextIO):
        """
        Writes the keyword and its data to a file object.
        This method must be implemented by subclasses.
        """
        raise NotImplementedError

    def __repr__(self):
        return f"LSDynaKeyword(type={self.keyword_type.name}, options={self.options})"
