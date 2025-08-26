"""
LS-DYNA Keywords Reader Library
"""

from .core.keyword_file import DynaKeywordFile
from .core.enums import KeywordType
from .keywords.lsdyna_keyword import LSDynaKeyword

LSDynaKeyword.discover_keywords()

__version__ = "0.1.0"
__all__ = [
    "DynaKeyword",
    "KeywordType",
]

