"""Test individual keywords"""

from pathlib import Path
import filecmp
import tempfile
import pytest
import os
import sys
sys.path.append('.')  # Ensure the dynakw package is in the path
from dynakw import DynaKeywordReader


class TestKeywords:
    """Test suite for individual keyword parsing"""

    def setup_method(self):
        """Setup for each test method"""
        self.test_dir = Path("test/keywords")
        self.results_dir = Path("test/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def test_keyword_files_exist(self):
        """Test that keyword files exist"""
        assert self.test_dir.exists(), "Test keywords directory should exist"

        keyword_files = list(self.test_dir.glob("*.k"))
        assert len(keyword_files) > 0, "Should have keyword test files"

    @pytest.mark.parametrize("keyword_file",
                             [f for f in Path("test/keywords").glob("*.k") if f.exists()])
    def test_keyword_roundtrip(self, keyword_file):
        """Test that keywords can be read and written back identically"""
        print("Testing:", keyword_file)
        keyword = keyword_file.stem
        new_file = self.results_dir / f"{keyword}_new.k"
        reference_file = self.results_dir / f"{keyword}_reference.k"

        # Read the keyword file
        dkw = DynaKeywordReader(str(keyword_file))

        # Write to results directory
        dkw.write(str(new_file))

        # Compare with reference file
        assert reference_file.exists(
        ), f"Reference file {reference_file} does not exist"
        assert self._files_equivalent(str(new_file), str(reference_file)), \
            f"Output {new_file} does not match reference {reference_file}"

    def _files_equivalent(self, file1: str, file2: str) -> bool:
        """Compare two files for equivalence, ignoring minor whitespace differences"""
        with open(file1, 'r') as f1, open(file2, 'r') as f2:
            lines1 = [line.rstrip() for line in f1.readlines() if line.strip()]
            lines2 = [line.rstrip() for line in f2.readlines() if line.strip()]

        return lines1 == lines2


if __name__ == "__main__":

    tk = TestKeywords()
    tk.setup_method()

    tk.test_keyword_roundtrip(Path("test/keywords/MAT_ELASTIC.k"))
    tk.test_keyword_roundtrip(Path("test/keywords/NODE.k"))
    tk.test_keyword_roundtrip(Path("test/keywords/PART.k"))
    tk.test_keyword_roundtrip(
        Path("test/keywords/BOUNDARY_PRESCRIBED_MOTION.k"))
    tk.test_keyword_roundtrip(Path("test/keywords/ELEMENT_SOLID.k"))
    tk.test_keyword_roundtrip(Path("test/keywords/SECTION_SOLID.k"))
    """
    """
    # tk.test_keyword_roundtrip( Path("test/keywords/ELEMENT_SHELL.k") ) # NYI
    # tk.test_keyword_roundtrip( Path("test/keywords/CONTROL_TERMINATION.k") ) # NYI

    # sys.exit(pytest.main([__file__]))
