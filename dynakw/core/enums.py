"""Enumeration of LS-DYNA keyword types"""

from enum import Enum, auto


class KeywordType(Enum):
    """Enumeration of supported LS-DYNA keywords"""
    BOUNDARY_PRESCRIBED_MOTION = auto()
    BOUNDARY_SPC_SET = auto()
    CONSTRAINED_JOINT = auto()
    CONTACT_AUTOMATIC_SURFACE_TO_SURFACE = auto()
    CONTROL_TERMINATION = auto()
    DEFINE_CURVE = auto()
    NODE = auto()
    ELEMENT_SOLID = auto()
    ELEMENT_SHELL = auto()
    LOAD_BODY = auto()
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
