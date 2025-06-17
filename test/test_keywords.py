"""Test individual keywords"""

import pytest
import os
import tempfile
import filecmp
from pathlib import Path
from dynakw import DynaKeywordFile

class TestKeywords:
    """Test suite for individual keyword parsing"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.test_dir = Path("test/keywords")
        
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
    
    def test_boundary_prescribed_motion_parsing(self):
        """Test specific parsing of BOUNDARY_PRESCRIBED_MOTION"""
        # Create a test keyword
        test_content = """*BOUNDARY_PRESCRIBED_MOTION
         1         1         0         1      1.0         0       0.0       0.0
         2         2         0         1      2.0         0       0.0       0.0
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as tmp_file:
            tmp_file.write(test_content)
            tmp_filename = tmp_file.name
        
        try:
            dkw = DynaKeywordFile(tmp_filename)
            dkw.read_all()
            
            assert len(dkw.keywords) == 1
            keyword = dkw.keywords[0]
            
            from dynakw import BOUNDARY_PRESCRIBED_MOTION
            assert keyword.type == BOUNDARY_PRESCRIBED_MOTION
            
            # Check that Card1 exists and has correct data
            card1 = keyword.Card1
            assert card1 is not None
            assert len(card1) == 2  # Two rows
            assert list(card1.columns) == ['NID', 'DOF', 'VAD', 'LCR', 'SF', 'VID', 'DEATH', 'BIRTH']
            
            # Check first row
            row1 = card1.iloc[0]
            assert row1['NID'] == 1
            assert row1['DOF'] == 1
            assert row1['SF'] == 1.0
            
        finally:
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)

