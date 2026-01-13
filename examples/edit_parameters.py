"""Example of editing *PARAMETER and *PARAMETER_EXPRESSION keywords"""

import sys
import os
import numpy as np

sys.path.append('.')
from dynakw import DynaKeywordReader, KeywordType


if __name__ == "__main__":
    
    # Configuration
    input_file = 'test/full_files/parameter.k'
    output_file = 'modified_parameters.k'
    
    # Parameters to change (Name -> New Value)
    parameters_to_change = {
        "term": 0.5,
        "states": 100,
        "par2": "baz",
        "plot": "term/(states-50) * 2.0"
    }
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Error: {input_file} does not exist.")
        sys.exit(1)

    print(f"Reading {input_file}...")

    with DynaKeywordReader(input_file) as dkr:
        # Perform updates
        dkr.edit_parameters(parameters_to_change)
        
        # Write the modified file
        print(f"Writing modified file to {output_file}...")
        dkr.write(output_file)
        print("Done.")
