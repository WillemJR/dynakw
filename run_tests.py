# run_tests.py
"""Comprehensive test runner for the dynakw project"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def setup_test_environment():
    """Setup the test environment"""
    print("Setting up test environment...")
    
    # Create test directories
    test_dirs = [
        "test/keywords",
        "test/full_files", 
        "test/utils",
        "examples",
        "docs"
    ]
    
    for dir_path in test_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create sample test file
    sample_file_path = Path("test/full_files/sample.k")
    if not sample_file_path.exists():
        create_sample_file(sample_file_path)
        print(f"Created sample file: {sample_file_path}")
    
    # Generate keyword test files
    generate_keyword_tests()
    
    print("Test environment setup complete!")

def create_sample_file(file_path):
    """Create a sample LS-DYNA file for testing"""
    sample_content = """$# LS-DYNA Sample Input File
*KEYWORD
*NODE
         1             0.0             0.0             0.0       0       0
         2             1.0             0.0             0.0       0       0
         3             1.0             1.0             0.0       0       0
         4             0.0             1.0             0.0       0       0
*ELEMENT_SOLID
         1         1         1         2         3         4         5         6         7         8
*BOUNDARY_PRESCRIBED_MOTION
         1         1         0         0       0.0         0       0.0       0.0
         2         2         0         1       1.0         0       0.0       0.0
*CONTROL_TERMINATION
      10.0         0       0.0       0.0       0.0
*END
"""
    
    with open(file_path, 'w') as f:
        f.write(sample_content)

def generate_keyword_tests():
    """Generate individual keyword test files"""
    print("Generating keyword test files...")
    
    #