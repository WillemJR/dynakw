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
        assert Path(dir_path).exists(), f"Directory {dir_path} does not exist"
        print(f"Have directory: {dir_path}")
    
    # Create sample test file
    sample_file_path = Path("test/full_files/sample.k")
    if not sample_file_path.exists():
        create_sample_file(sample_file_path)
        print(f"Created sample file: {sample_file_path}")
    
    # Generate keyword test files
    generate_keyword_tests()
    
    print("Test environment setup complete!")

def generate_keyword_tests():
    """Generate individual keyword test files"""
    print("Generating keyword test files...")

def run_tests():
    keywords_dir = "test/keywords"
    for filename in os.listdir(keywords_dir):
        file_path = os.path.join(keywords_dir, filename)
        print( file_path)
        if os.path.isfile(file_path):
            test_keywords(file_path)

if __name__ == "__main__":
    setup_test_environment()
    run_tests()
    print("All tests completed successfully!")
    