"""Implementation of the *UNKNOWN keyword."""

from .lsdyna_keyword import LSDynaKeyword
from ..core.enums import KeywordType
from typing import List


class Unknown(LSDynaKeyword):
    """Represents an unrecognized keyword.

    The data for this keyword is stored as a raw string.
    """
    keyword_string = "*UNKNOWN"

    _keyword = KeywordType.UNKNOWN

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        self.raw_data = None
        super().__init__(keyword_name, raw_lines)
        # The base class derives the type from the keyword name, which resolves
        # to a real KeywordType whenever the name merely begins with a known
        # one (e.g. *MAT_ELASTIC_PLASTIC_HYDRO -> MAT_ELASTIC).  An
        # unrecognized block was not parsed as that keyword and has no cards,
        # so reporting it under that type would make find_keywords() return it.
        self.type = self._keyword

    def __repr__(self) -> str:
        return f"Unknown(keyword='data='{self.raw_data[:20]}...')"

    def write(self, file_obj):
        """Write the keyword and its raw data to a file."""
        # assert self.type == self._keyword
        file_obj.write(self.full_keyword)
        file_obj.write('\n')
        if self.raw_data is not None:
            file_obj.write(self.raw_data)
        else:
            pass
        file_obj.write("\n")

    def _parse_raw_data(self, raw_lines: List[str]):
        self.raw_data = "\n".join(raw_lines)
