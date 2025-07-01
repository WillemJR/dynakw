# run_tests.py
"""Test runner for the dynakw project"""

import sys
import subprocess

def run_file_splitter():
    """Runs the file splitter setup script."""
    print("Running file splitter setup...")
    result = subprocess.run(
        [sys.executable, "test/utils/file_splitter.py"],
        capture_output=True,
        text=True,
        check=False
    )

    if result.stdout:
        print("--- FILE SPLITTER STDOUT ---")
        print(result.stdout)

    if result.stderr:
        print("--- FILE SPLITTER STDERR ---")
        print(result.stderr)

    if result.returncode != 0:
        print(f"File splitter exited with status {result.returncode}")
        sys.exit(result.returncode)
    else:
        print("File splitter completed successfully!")

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
    run_file_splitter()
    run_all_tests()

