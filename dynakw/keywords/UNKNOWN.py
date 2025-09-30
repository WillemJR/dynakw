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

    def __repr__(self) -> str:
        return f"Unknown(keyword='{self.keyword_line.strip()}', data='{self.raw_data[:20]}...')"

    def write(self, file_obj):
        """Write the keyword and its raw data to a file."""
        assert self.type == self._keyword
        file_obj.write(self.full_keyword)
        file_obj.write('\n')
        if self.raw_data is not None:
            file_obj.write(self.raw_data)
        else:
            pass
        file_obj.write("\n")

    def _parse_raw_data(self, raw_lines: List[str]):
        self.raw_data = "\n".join(raw_lines)
