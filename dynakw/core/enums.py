"""Enumeration of LS-DYNA keyword types"""

from enum import Enum, auto


class KeywordType(Enum):
    """Enumeration of supported LS-DYNA keywords"""
    BOUNDARY_PRESCRIBED_MOTION = auto()
    NODE = auto()
    ELEMENT_SOLID = auto()
    ELEMENT_SHELL = auto()
    MAT_ELASTIC = auto()
    SECTION_SOLID = auto()
    SECTION_SHELL = auto()
    UNKNOWN = auto()
    PART = auto()
