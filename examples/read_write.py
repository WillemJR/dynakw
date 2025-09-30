"""Basic usage example for dynakw library"""

import sys
import shutil
sys.path.append('.')
import dynakw


# Example 1: Read and write a keyword file
print("Example 1: Read and write keyword file")

in_fname = 'test/full_files/sample.k'
out_fname = 'output.k'

with dynakw.DynaKeywordReader(in_fname, follow_include=True) as dkw:
    dkw.write(out_fname)
