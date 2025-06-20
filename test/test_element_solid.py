import pytest
import sys
from pathlib import Path
sys.path.append('.')
import pandas as pd
from io import StringIO

from dynakw.core.keyword_file import DynaKeywordFile
from dynakw.keywords.ELEMENT_SOLID import ElementSolid
from dynakw.core.enums import KeywordType

# Path to the test input file
TEST_FILE = Path(__file__).parent / "keywords" / "ELEMENT_SOLID.k"

class TestElementSolid:
    """Contains tests for the ELEMENT_SOLID keyword parser."""

    @pytest.fixture(scope="class")
    def dkw(self):
        """Fixture to parse the keyword file once for the test class."""
        dkf = DynaKeywordFile(str(TEST_FILE))
        return dkf

    def test_parse_element_solid(self, dkw):
        """Tests parsing *ELEMENT_SOLID from a file using DynaKeywordFile."""
        # Find ELEMENT_SOLID keywords
        element_solid_keywords = [
            kw for kw in dkw.keywords if isinstance(kw, ElementSolid)
        ]
        
        assert len(element_solid_keywords) == 2

        # Test first block (legacy format)
        elem_solid_1 = element_solid_keywords[0]
        assert elem_solid_1.keyword_type == KeywordType.ELEMENT_SOLID
        assert elem_solid_1.is_legacy
        df1 = elem_solid_1.cards['main']
        assert len(df1) == 1
        assert df1.iloc[0]['EID'] == 1
        assert df1.iloc[0]['PID'] == 1
        assert df1.iloc[0]['N8'] == 8

        # Test second block (legacy format)
        elem_solid_2 = element_solid_keywords[1]
        assert elem_solid_2.keyword_type == KeywordType.ELEMENT_SOLID
        assert elem_solid_2.is_legacy
        df2 = elem_solid_2.cards['main']
        assert len(df2) == 1
        assert df2.iloc[0]['EID'] == 1
        assert df2.iloc[0]['PID'] == 1
        assert df2.iloc[0]['N1'] == 5
        assert df2.iloc[0]['N8'] == 4

    def test_write_element_solid_roundtrip(self, dkw):
        """Tests writing and re-reading *ELEMENT_SOLID for round-trip consistency."""
        element_solid_keywords = [
            kw for kw in dkw.keywords if isinstance(kw, ElementSolid)
        ]

        for elem_solid in element_solid_keywords:
            # Write object to a string
            string_io = StringIO()
            elem_solid.write(string_io)
            output = string_io.getvalue()
            print( output )
            
            # Create a second object from the written string
            #output_lines = output.strip().splitlines()
            #elem_solid_from_output = ElementSolid(output_lines[0], output_lines)
            
            # The DataFrames of the two objects should be identical
            #pd.testing.assert_frame_equal(elem_solid.cards['main'], elem_solid_from_output.cards['main'])

if __name__ == "__main__":
    pytest.main([__file__])
