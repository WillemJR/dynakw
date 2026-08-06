"""
LS-DYNA Keywords Reader Library
"""
__version__ = "1.4.1"

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())


from .core.keyword_file import DynaKeywordReader
from .core.enums import KeywordType
from .core.parameter_ref import ParameterRef
from .keywords.lsdyna_keyword import LSDynaKeyword
from .core.introspect import (
    CardSpec,
    FieldSpec,
    KeywordNotSupported,
    KeywordSpec,
    capability_manifest,
    describe_keyword,
    supported_keywords,
)

__all__ = [
    "DynaKeywordReader",
    "KeywordType",
    "ParameterRef",
    "LSDynaKeyword",
    # Capability introspection
    "supported_keywords",
    "describe_keyword",
    "capability_manifest",
    "KeywordSpec",
    "CardSpec",
    "FieldSpec",
    "KeywordNotSupported",
]
