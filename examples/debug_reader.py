"""for dynakw library"""

import sys
import shutil
sys.path.append( '.' )

import argparse

import dynakw

# Set up argument parser
parser = argparse.ArgumentParser(description="Debug program.")
parser.add_argument("input_file", help="Path to the input LS-DYNA keyword file.")
args = parser.parse_args()


with dynakw.DynaKeywordFile( args.input_file, follow_include=True, debug=True ) as dkw:
    dkw.write( 'k.k' )

