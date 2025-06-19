"""Test individual keywords"""

import pytest
import os
import sys
sys.path.append( '.' )# Ensure the dynakw package is in the path
import tempfile
import filecmp
from pathlib import Path
from dynakw import DynaKeywordFile
import sys

class TestKeywords:
    """Test suite for individual keyword parsing"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.test_dir = Path("test/keywords")
        #self.test_dir = Path("keywords")
        
    def test_keyword_files_exist(self):
        """Test that keyword files exist"""
        assert self.test_dir.exists(), "Test keywords directory should exist"
        
        keyword_files = list(self.test_dir.glob("*.k"))
        assert len(keyword_files) > 0, "Should have keyword test files"
    
    @pytest.mark.parametrize("keyword_file", 
                            [f for f in Path("test/keywords").glob("*.k") if f.exists()])
    def test_keyword_roundtrip(self, keyword_file):
        """Test that keywords can be read and written back identically"""
        # Read the keyword file
        dkw = DynaKeywordFile(str(keyword_file))
        dkw.read_all()
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as tmp_file:
            tmp_filename = tmp_file.name
            
        try:
            dkw.write(tmp_filename)
            
            # Compare files (ignoring whitespace differences for now)
            assert self._files_equivalent(str(keyword_file), tmp_filename)
            
        finally:
            # Clean up
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)
    
    def _files_equivalent(self, file1: str, file2: str) -> bool:
        """Compare two files for equivalence, ignoring minor whitespace differences"""
        with open(file1, 'r') as f1, open(file2, 'r') as f2:
            lines1 = [line.rstrip() for line in f1.readlines() if line.strip()]
            lines2 = [line.rstrip() for line in f2.readlines() if line.strip()]
            
        return lines1 == lines2
    
if __name__ == "__main__":
        sys.exit(pytest.main([__file__]))
