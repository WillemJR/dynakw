"""Example of editing keywords"""

import sys
sys.path.append( '.' )
import dynakw

def edit_boundary():
    """Demonstrate editing keywords"""
    
    # Read a file
    fname = 'test/full_files/sample.k'
    try:
        dkw = dynakw.DynaKeywordFile( fname )
        dkw.read_all()
        
        print(f"Processing {len(dkw.keywords)} keywords...")
        
        # Find and edit BOUNDARY_PRESCRIBED_MOTION keywords
        for kw in dkw.next_kw():
            if kw.keyword_type == dynakw.KeywordType.BOUNDARY_PRESCRIBED_MOTION:
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
        
        # Write all keywords to new file
        dkw.write('modified_output.k')
        print("Wrote modified file to modified_output.k")
        
    except FileNotFoundError:
        exit(f"{fname}.k not found")
        
        # Create a sample file for demonstration
        

if __name__ == "__main__":
    edit_boundary()

