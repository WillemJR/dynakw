
"""Enumeration of LS-DYNA keyword types"""

from enum import Enum, auto

class KeywordType(Enum):
    """Enumeration of supported LS-DYNA keywords"""
    BOUNDARY_PRESCRIBED_MOTION = auto()
    BOUNDARY_PRESCRIBED_MOTION_NODE = auto()
    BOUNDARY_PRESCRIBED_MOTION_SET = auto()
    NODE = auto()
    ELEMENT_SOLID = auto()
    MATERIAL = auto()
    SECTION_SOLID = auto()
    CONTROL_TERMINATION = auto()
    UNKNOWN = auto()

# For backward compatibility and easier access
BOUNDARY_PRESCRIBED_MOTION = KeywordType.BOUNDARY_PRESCRIBED_MOTION

