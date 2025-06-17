"""Basic usage example for dynakw library"""

import dynakw

def main():
    """Demonstrate basic usage of the library"""
    
    # Example 1: Read and write a keyword file
    print("Example 1: Read and write keyword file")
    try:
        dkw = dynakw.DynaKeywordFile('example.k')
        dkw.read_all(follow_include=True)
        print(f"Found {len(dkw.keywords)} keywords")
        
        # Write to output file
        dkw.write('output.k')
        print("Successfully wrote output.k")
        
    except FileNotFoundError:
        print("example.k not found - create a sample file to test")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Create a simple keyword programmatically
    print("\nExample 2: Create keyword programmatically")
    
    # Create a simple BOUNDARY_PRESCRIBED_MOTION keyword
    import pandas as pd
    from dynakw.core.keyword import DynaKeyword
    from dynakw import BOUNDARY_PRESCRIBED_MOTION
    
    keyword = DynaKeyword(BOUNDARY_PRESCRIBED_MOTION)
    keyword._original_line = "*BOUNDARY_PRESCRIBED_MOTION"
    
    # Create Card1 data
    data = [
        [1, 1, 0, 1, 1.0, 0, 0.0, 0.0],
        [2, 2, 0, 1, 2.0, 0, 0.0, 0.0]
    ]
    df = pd.DataFrame(data, columns=['NID', 'DOF', 'VAD', 'LCR', 'SF', 'VID', 'DEATH', 'BIRTH'])
    keyword.add_card('Card1', df)
    
    # Write to stdout
    import sys
    print("Generated keyword:")
    keyword.write(sys.stdout)

if __name__ == "__main__":
    main()

