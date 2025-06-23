"""Example of how to parse a keyword file and print all instances of a specific keyword type."""
import sys
import os
import argparse

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dynakw import DynaKeywordFile
from dynakw.core.enums import KeywordType

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Print all instances of a specific keyword type from a keyword file.")
    parser.add_argument("input_file", help="Path to the keyword file.")
    parser.add_argument("keyword_type", help=f"The type of keyword to print. Available types: {[e.name for e in KeywordType]}")
    args = parser.parse_args()

    # Get the keyword type from the string
    try:
        target_keyword_type = KeywordType[args.keyword_type.upper()]
    except KeyError:
        print(f"Error: Invalid keyword type '{args.keyword_type}'.")
        print(f"Available types are: {[e.name for e in KeywordType]}")
        sys.exit(1)

    # Parse the keyword file
    dkw = DynaKeywordFile(args.input_file)

    # Iterate through the keywords and print all matching keywords
    print(f"--- Found keywords of type {target_keyword_type.name} in {args.input_file} ---")
    for keyword in dkw.keywords:
        #print( keyword.keyword_type , target_keyword_type )
        #breakpoint()
        if keyword.keyword_type == target_keyword_type:
            #print(keyword)
            keyword.write(sys.stdout)


if __name__ == "__main__":
    main()

