"""Example of how to parse a keyword file and print all instances of a specific keyword type."""
import sys
import os
import argparse

sys.path.append('.')
from dynakw import DynaKeywordReader, KeywordType

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))


parser = argparse.ArgumentParser(
    description="Print all instances of a specific keyword type from a keyword file; e.g. python3 examples/print_keyword.py test/keywords/PART.k PART")
parser.add_argument("input_file", help="Path to the keyword file.")
parser.add_argument(
    "keyword_type", help=f"The type of keyword to print. Available types: {[e.name for e in KeywordType]}")
args = parser.parse_args()

# Get the keyword type from the string
target_keyword_type = KeywordType[args.keyword_type.upper()]

with DynaKeywordReader(args.input_file) as dkw:
    for keyword in dkw.find_keywords(target_keyword_type):
        keyword.write(sys.stdout)
