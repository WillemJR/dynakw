"""for dynakw library"""

import argparse
import sys
sys.path.append('.')
import dynakw


# Set up argument parser
parser = argparse.ArgumentParser(description="Debug program.")
parser.add_argument(
    "input_file", help="Path to the input LS-DYNA keyword file.")
args = parser.parse_args()


with dynakw.DynaKeywordReader(args.input_file, follow_include=True, debug=True) as dkw:
    dkw.write('k.k')
