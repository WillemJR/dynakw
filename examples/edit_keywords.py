"""Example of editing keywords"""

import sys
import dynakw

def main():
    """Demonstrate editing keywords"""
    
    # Read a file
    try:
        dkw = dynakw.DynaKeywordFile('input.k')
        dkw.read_all()
        
        print(f"Processing {len(dkw.keywords)} keywords...")
        
        # Find and edit BOUNDARY_PRESCRIBED_MOTION keywords
        for kw in dkw.next_kw():
            if kw.type == dynakw.BOUNDARY_PRESCRIBED_MOTION:
                print("Found BOUNDARY_PRESCRIBED_MOTION keyword")
                
                # Access Card1 and modify SF values
                if kw.Card1 is not None:
                    print(f"Original SF values: {list(kw.Card1['SF'])}")
                    
                    # Scale all SF values by 1.5
                    kw.Card1['SF'] = kw.Card1['SF'] * 1.5
                    
                    print(f"Modified SF values: {list(kw.Card1['SF'])}")
                    
                    # Write the modified keyword
                    print("Modified keyword:")
                    kw.write(sys.stdout)
                    print()
        
        # Write all keywords to new file
        dkw.write('modified_output.k')
        print("Wrote modified file to modified_output.k")
        
    except FileNotFoundError:
        print("input.k not found")
        
        # Create a sample file for demonstration
        create_sample_file()
        
def create_sample_file():
    """Create a sample LS-DYNA file for testing"""
    sample_content = """*KEYWORD
*NODE
         1       0.0       0.0       0.0         0         0
         2       1.0       0.0       0.0         0         0
         3       0.0       1.0       0.0         0         0
         4       1.0       1.0       0.0         0         0
*BOUNDARY_PRESCRIBED_MOTION
         1         1         0         1      1.0         0       0.0       0.0
         2         2         0         1      2.0         0       0.0       0.0
*CONTROL_TERMINATION
      10.0
"""
    
    with open('input.k', 'w') as f:
        f.write(sample_content)
    
    print("Created sample input.k file")
    print("Run this script again to see the editing example")

if __name__ == "__main__":
    main()

