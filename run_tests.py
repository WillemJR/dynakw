# run_tests.py
"""Test runner for the dynakw project"""

import sys
import subprocess

def run_all_tests():
    """Runs all pytest tests."""
    print("Running pytest...")
    # Use sys.executable to ensure we're using the same python interpreter
    # that is running the script.
    result = subprocess.run(
        [sys.executable, "-m", "pytest"],
        capture_output=True,
        text=True,
        check=False  # Do not raise exception on non-zero exit code
    )
    
    print("--- STDOUT ---")
    print(result.stdout)
    
    if result.stderr:
        print("--- STDERR ---")
        print(result.stderr)
        
    if result.returncode != 0:
        print(f"Pytest exited with status {result.returncode}")
        sys.exit(result.returncode)
    else:
        print("All tests passed!")

if __name__ == "__main__":
    run_all_tests()
