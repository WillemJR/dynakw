"""Basic usage example for dynakw library"""

import sys
sys.path.append( '.' )

import dynakw

def read_write_file():
    """Demonstrate basic usage of the library"""
    
    # Example 1: Read and write a keyword file
    print("Example 1: Read and write keyword file")
    try:
        dkw = dynakw.DynaKeywordFile('test/full_files/sample.k')
        dkw.read_all(follow_include=True)
        print(f"Found {len(dkw.keywords)} keywords")
        
        # Write to output file
        dkw.write('output.k')
        print("Successfully wrote output.k")
        
    except FileNotFoundError:
        print("example.k not found - create a sample file to test")
    except Exception as e:
        print(f"Error: {e}")
    
if __name__ == "__main__":
    read_write_file()


