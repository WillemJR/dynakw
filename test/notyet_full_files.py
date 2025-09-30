"""Test complete LS-DYNA files"""

import pytest
import os
import tempfile
from pathlib import Path
from dynakw import DynaKeywordReader


class TestFullFiles:
    """Test suite for complete file processing"""

    def setup_method(self):
        """Setup for each test method"""
        self.test_dir = Path("test/full_files")

    def test_full_files_exist(self):
        """Test that full test files exist"""
        assert self.test_dir.exists(), "Test full_files directory should exist"

        test_files = list(self.test_dir.glob("*.k"))
        assert len(test_files) > 0, "Should have full file test cases"

    @pytest.mark.parametrize("test_file",
                             [f for f in Path("test/full_files").glob("*.k") if f.exists()])
    def test_full_file_roundtrip(self, test_file):
        """Test that complete files can be read and written back"""
        # Read the complete file
        dkw = DynaKeywordReader(str(test_file))

        # Verify we found some keywords
        assert len(dkw.keywords) > 0, f"Should find keywords in {test_file}"

        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as tmp_file:
            tmp_filename = tmp_file.name

        try:
            dkw.write(tmp_filename)

            # Verify the output file is readable
            dkw2 = DynaKeywordReader(tmp_filename)

            # Should have same number of keywords
            assert len(dkw2.keywords) == len(
                dkw.keywords), "Should preserve keyword count"

        except Exception as e:
            pytest.fail(f"Failed to process {test_file}: {e}")

        finally:
            # Clean up
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)

    def test_include_file_processing(self):
        """Test processing files with *INCLUDE directives"""
        # Create main file with include
        main_content = """*KEYWORD
*INCLUDE
test_include.k
*CONTROL_TERMINATION
      10.0
"""

        # Create include file
        include_content = """*NODE
         1       0.0       0.0       0.0         0         0
         2       1.0       0.0       0.0         0         0
"""

        with tempfile.TemporaryDirectory() as tmp_dir:
            main_file = os.path.join(tmp_dir, "main.k")
            include_file = os.path.join(tmp_dir, "test_include.k")

            with open(main_file, 'w') as f:
                f.write(main_content)
            with open(include_file, 'w') as f:
                f.write(include_content)

            # Test with follow_include=True
            dkw = DynaKeywordReader(main_file)

            # Should find keywords from both files
            assert len(
                dkw.keywords) >= 2, "Should find keywords from main and include files"

            # Find NODE keyword from include file
            from dynakw import KeywordType
            node_keywords = [
                kw for kw in dkw.keywords if kw.type == KeywordType.NODE]
            assert len(
                node_keywords) > 0, "Should find NODE keyword from include file"
