"""Example of editing keywords"""

import sys
import shutil
sys.path.append( '.' )
import dynakw

"""Demonstrate editing keywords"""

# Read a file
fname = 'test/full_files/sample.k'
out_fname = 'modified_output.k'

with dynakw.DynaKeywordFile(fname) as dkw:
    dkw.read_all()
    
    # Find and edit BOUNDARY_PRESCRIBED_MOTION keywords
    for kw in dkw.next_kw():
        if kw.type == dynakw.KeywordType.BOUNDARY_PRESCRIBED_MOTION:
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
    dkw.save( out_fname )
    
