"""Implementation of the *UNKNOWN keyword."""

from .lsdyna_keyword import LSDynaKeyword
from ..core.enums import KeywordType
from typing import List


class Unknown(LSDynaKeyword):
    """Represents an unrecognized keyword.

    The data for this keyword is stored as a raw string.
    """

    _keyword = KeywordType.UNKNOWN

    def __init__(self, keyword_line: str, data_lines: list[str]):
        super().__init__(keyword_line, data_lines)

        self.raw_data = "\n".join(data_lines)

    def __repr__(self) -> str:
        return f"Unknown(keyword='{self.keyword_line.strip()}', data='{self.raw_data[:20]}...')"

    def write(self, file_obj):
        """Write the keyword and its raw data to a file."""
        assert self.keyword_type == self._keyword
        file_obj.write(self.keyword_line)
        file_obj.write(self.raw_data)
        file_obj.write("\n")
        
    def _parse_raw_data(self, raw_lines: List[str]):
        pass
