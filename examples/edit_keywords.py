"""Example of editing keywords"""

import sys
sys.path.append('.')
from dynakw import DynaKeywordReader, KeywordType

"""Demonstrate editing keywords"""

# Read a file
fname = 'test/full_files/sample.k'
out_fname = 'modified_output.k'

with DynaKeywordReader(fname) as dkr:

    # Find and edit BOUNDARY_PRESCRIBED_MOTION keywords
    for kw in dkr.keywords():
        if kw.type == KeywordType.BOUNDARY_PRESCRIBED_MOTION:
            print("Found BOUNDARY_PRESCRIBED_MOTION keyword")

            # Access Card1 and modify SF values
            if kw.cards['Card 1'] is not None:
                print(f"Original SF values: {list(kw.cards['Card 1']['SF'])}")

                # Scale all SF values by 1.5
                kw.cards['Card 1']['SF'] = kw.cards['Card 1']['SF'] * 1.5

                print(f"Modified SF values: {list(kw.cards['Card 1']['SF'])}")

                # Write the modified keyword
                print("Modified keyword:")
                kw.write(sys.stdout)
                print()
    dkr.write(out_fname)
