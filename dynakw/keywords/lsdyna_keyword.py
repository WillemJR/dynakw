"""Abstract base class for all LS-DYNA keyword objects."""

from collections import OrderedDict
from abc import ABC, abstractmethod
from typing import TextIO, List, Dict, Tuple
import numpy as np
from dynakw.core.enums import KeywordType
from dynakw.utils.format_parser import FormatParser
import os
import importlib


class LSDynaKeyword(ABC):
    """
    Base class for all LS-DYNA keyword objects.

    This class provides the basic structure for representing an LS-DYNA
    keyword, including methods for parsing from raw text and writing
    back to a file format.
    """

    KEYWORD_MAP: Dict[str, "LSDynaKeyword"] = OrderedDict()
    """A registry of all known keyword strings and the classes that handle them."""

    def __init_subclass__(cls, **kwargs):
        """This method is called when a subclass of LSDynaKeyword is defined."""
        super().__init_subclass__(**kwargs)
        # The 'keyword_string' is the primary identifier for the keyword class.
        if hasattr(cls, 'keyword_string'):
            # Register the primary keyword string.
            cls.KEYWORD_MAP[cls.keyword_string] = cls
        # 'keyword_aliases' can be used for alternative names for the same keyword.
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
        self.type, self.options = self._parse_keyword_name(self.full_keyword)
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
                type = KeywordType[base_keyword_str]
                options = parts[i:]
                return type, options
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
        return f"LSDynaKeyword(type={self.type.name}, options={self.options})"

    @staticmethod
    def discover_keywords():
        """
        Dynamically imports all keyword modules from the 'keywords' directory
        to ensure they are registered in the KEYWORD_MAP.
        """
        keyword_dir = os.path.dirname(__file__)
        for filename in os.listdir(keyword_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"dynakw.keywords.{filename[:-3]}"
                try:
                    importlib.import_module(module_name)
                except ImportError as e:
                    # Handle potential import errors gracefully
                    print(f"Could not import {module_name}: {e}")
