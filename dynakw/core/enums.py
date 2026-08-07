"""Enumeration of LS-DYNA keyword types"""

from enum import Enum, auto


class KeywordType(Enum):
    """Enumeration of supported LS-DYNA keywords"""
    BOUNDARY_PRESCRIBED_MOTION = auto()
    CONSTRAINED_JOINT = auto()
    CONTROL_TERMINATION = auto()
    DEFINE_CURVE = auto()
    NODE = auto()
    ELEMENT_SOLID = auto()
    ELEMENT_SHELL = auto()
    MAT_ELASTIC = auto()
    MAT_RIGID = auto()
    PARAMETER = auto()
    PARAMETER_EXPRESSION = auto()
    PART = auto()
    SECTION_SOLID = auto()
    SECTION_SHELL = auto()
    SET_SEGMENT = auto()
    SET_NODE = auto()
    SET_SHELL = auto()
    SET_SOLID = auto()
    UNKNOWN = auto()
