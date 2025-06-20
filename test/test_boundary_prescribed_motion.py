import pytest
import sys
sys.path.append( '.' )# Ensure the dynakw package is in the path
import pandas as pd
from io import StringIO
from dynakw.keywords.BOUNDARY_PRESCRIBED_MOTION import BoundaryPrescribedMotion
from dynakw.core.enums import KeywordType

# Test cases from user-provided data
# Case 1: Standard format with 8 columns
RAW_TEXT_STANDARD = '''*BOUNDARY_PRESCRIBED_MOTION
$#     NID       DOF       VAD       LCR        SF       VID     DEATH     BIRTH
         1         1         0         0       0.0         0       0.0       0.0
         1         2         0         0       0.0         0       0.0       0.0
         1         3         0         0       0.0         0       0.0       0.0
         2         1         0         0       0.0         0       0.0       0.0
         2         2         0         0       0.0         0       0.0       0.0
         2         3         0         0       0.0         0       0.0       0.0
         3         1         0         0       0.0         0       0.0       0.0
         3         2         0         0       0.0         0       0.0       0.0
         3         3         0         0       0.0         0       0.0       0.0
         4         1         0         0       0.0         0       0.0       0.0
         4         2         0         0       0.0         0       0.0       0.0
         4         3         0         0       0.0         0       0.0       0.0
'''

# Case 2: _NODES format with 6 columns
RAW_TEXT_NODES = '''*BOUNDARY_PRESCRIBED_MOTION_NODES
$      nid       dof       vad      lcid        sf       vid
         1         4         2         1 4.000E-02         1
         2         4         2         1 4.000E-02         1
         3         4         2         1 4.000E-02         1
         4         4         2         1 4.000E-02         1
'''

@pytest.mark.parametrize("raw_text, expected_keyword_type, expected_options, expected_columns, expected_rows, expected_first_row", [
    (RAW_TEXT_STANDARD, KeywordType.BOUNDARY_PRESCRIBED_MOTION, [], ['ID', 'DOF', 'VAD', 'LCID', 'SF', 'VID', 'DEATH', 'BIRTH'], 12, {'ID': 1, 'DOF': 1, 'SF': 0.0, 'DEATH': 0.0}),
    (RAW_TEXT_NODES, KeywordType.BOUNDARY_PRESCRIBED_MOTION, ['NODES'], ['ID', 'DOF', 'VAD', 'LCID', 'SF', 'VID'], 4, {'ID': 1, 'DOF': 4, 'SF': 0.04}),
])
def test_parse_boundary_prescribed_motion(raw_text, expected_keyword_type, expected_options, expected_columns, expected_rows, expected_first_row):
    lines = raw_text.strip().split('\n')
    keyword_name = lines[0]
    
    bpm = BoundaryPrescribedMotion(keyword_name, lines)
    
    assert bpm.keyword_type == expected_keyword_type
    assert bpm.options == expected_options
    
    assert 'Card 1' in bpm.cards
    df = bpm.cards['Card 1']
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == expected_rows
    assert list(df.columns) == expected_columns
    
    for col, val in expected_first_row.items():
        assert df.iloc[0][col] == val


    print( raw_text )
    bpm.write(sys.stdout)

@pytest.mark.parametrize("raw_text", [
    RAW_TEXT_STANDARD,
    RAW_TEXT_NODES,
])
def test_write_boundary_prescribed_motion(raw_text):
    lines = raw_text.strip().split('\n')
    keyword_name = lines[0]
    
    # Create object from raw text
    bpm = BoundaryPrescribedMotion(keyword_name, lines)
    
    # Write object to a string
    string_io = StringIO()
    bpm.write(string_io)
    output = string_io.getvalue()
    
    # Create a second object from the written string
    output_lines = output.strip().split('\n')
    bpm_from_output = BoundaryPrescribedMotion(output_lines[0], output_lines)
    
    # The DataFrames of the two objects should be identical
    pd.testing.assert_frame_equal(bpm.cards['Card 1'], bpm_from_output.cards['Card 1'])



if __name__ == "__main__":
    #test_write_boundary_prescribed_motion(RAW_TEXT_STANDARD, KeywordType.BOUNDARY_PRESCRIBED_MOTION, [], ['ID', 'DOF', 'VAD', 'LCID', 'SF', 'VID', 'DEATH', 'BIRTH'], 12, {'ID': 1, 'DOF': 1, 'SF': 0.0, 'DEATH': 0.0})
    #test_parse_boundary_prescribed_motion(RAW_TEXT_STANDARD)
    test_parse_boundary_prescribed_motion( RAW_TEXT_STANDARD, KeywordType.BOUNDARY_PRESCRIBED_MOTION, [], ['ID', 'DOF', 'VAD', 'LCID', 'SF', 'VID', 'DEATH', 'BIRTH'], 12, {'ID': 1, 'DOF': 1, 'SF': 0.0, 'DEATH': 0.0} )
    #test_parse_boundary_prescribed_motion(RAW_TEXT_STANDARD)
    test_parse_boundary_prescribed_motion( RAW_TEXT_NODES, KeywordType.BOUNDARY_PRESCRIBED_MOTION, ['NODES'], ['ID', 'DOF', 'VAD', 'LCID', 'SF', 'VID'], 4, {'ID': 1, 'DOF': 4, 'SF': 0.04} )

    test_write_boundary_prescribed_motion(RAW_TEXT_STANDARD)
    test_write_boundary_prescribed_motion(RAW_TEXT_NODES)   
