import pytest
import sys
sys.path.append('.')
from dynakw.core.keyword_file import DynaKeywordReader
from dynakw.core.enums import KeywordType

def test_set_parameters(tmp_path):
    # 1. Create a dummy k file with *PARAMETER and *PARAMETER_EXPRESSION
    k_file = tmp_path / "test_params.k"
    content = """*KEYWORD
*PARAMETER
Rlength, 10.5, Icount, 5, Rwidth, 3.2
*PARAMETER_EXPRESSION
Rarea     Rlength * Rwidth
*END
"""
    k_file.write_text(content, encoding="utf-8")

    # 2. Define updates
    # Note: Keys are case-insensitive and match against parameter name without the type prefix (R, I, etc.)
    # "length" matches "Rlength", "count" matches "Icount"
    updates = {
        "length": 20.0,
        "count": 10,
        "area": "Rlength * Rwidth * 2" 
    }
    
    # 3. Run set_parameters
    # We use a context manager to ensure everything is handled cleanly
    # but we need to explicitly write back to verify the changes if we read again.
    # Alternatively, we can inspect the in-memory objects after edit.
    
    # Method 1: Edit and verify in-memory
    with DynaKeywordReader(str(k_file)) as reader:
        # Before edit check (sanity check)
        keywords = list(reader.keywords())
        param_kw = next(kw for kw in keywords if kw.type == KeywordType.PARAMETER)
        
        # Helper to find value for parameter name in *PARAMETER
        def get_val_param(kw, p_name):
            card = kw.cards.get('Card 1')
            if not card: return None
            for i in range(1, 5): # PRMR1..4
                p_col = f"PRMR{i}"
                v_col = f"VAL{i}"
                if p_col in card:
                    names = card[p_col]
                    vals = card[v_col]
                    for idx, name in enumerate(names):
                        if name == p_name:
                            return vals[idx]
            return None

        assert float(get_val_param(param_kw, "Rlength")) == 10.5
        
        # Perform edit
        reader.set_parameters(updates)
        
        # Verify updates in memory
        assert float(get_val_param(param_kw, "Rlength")) == 20.0
        assert int(get_val_param(param_kw, "Icount")) == 10
        assert float(get_val_param(param_kw, "Rwidth")) == 3.2 # Should not change

        # Verify *PARAMETER_EXPRESSION
        pexpr_kw = next(kw for kw in keywords if kw.type == KeywordType.PARAMETER_EXPRESSION)
        card_expr = pexpr_kw.cards['Card 1']
        assert card_expr['PRMR1'][0] == "Rarea"
        assert card_expr['EXPRESSION1'][0] == "Rlength * Rwidth * 2"
        
        # Write back to file to test persistence
        reader.write(str(k_file))

    # 4. Read back and verify persistence
    with DynaKeywordReader(str(k_file)) as reader:
        keywords = list(reader.keywords())
        param_kw = next(kw for kw in keywords if kw.type == KeywordType.PARAMETER)
        
        # Re-define helper or reuse logic
        def get_val_param_final(kw, p_name):
            card = kw.cards.get('Card 1')
            if not card: return None
            for i in range(1, 5): 
                p_col = f"PRMR{i}"
                v_col = f"VAL{i}"
                if p_col in card:
                    names = card[p_col]
                    vals = card[v_col]
                    for idx, name in enumerate(names):
                        if name == p_name:
                            return vals[idx]
            return None

        assert float(get_val_param_final(param_kw, "Rlength")) == 20.0
        assert int(get_val_param_final(param_kw, "Icount")) == 10
        assert float(get_val_param_final(param_kw, "Rwidth")) == 3.2

        pexpr_kw = next(kw for kw in keywords if kw.type == KeywordType.PARAMETER_EXPRESSION)
        card_expr = pexpr_kw.cards['Card 1']
        assert card_expr['PRMR1'][0] == "Rarea"
        # Check if expression is preserved/updated
        assert card_expr['EXPRESSION1'][0].strip() == "Rlength * Rwidth * 2"

def test_set_parameters_robustness(tmp_path):
    """Test that set_parameters handles missing params and mixed case updates gracefully."""
    k_file = tmp_path / "test_params_robust.k"
    content = """*KEYWORD
*PARAMETER
Rval1, 1.0
*END
"""
    k_file.write_text(content, encoding="utf-8")
    
    updates = {
        "val1": 2.0,
        "NON_EXISTENT": 5.0,
        "VaL1": 3.0 # Should overwrite previous update if processed sequentially, but dict order matters
    }
    # Note: dict key order is insertion order in Python 3.7+.
    # "val1" is updated to 2.0. "VaL1" (same key normalized) updates it to 3.0?
    # set_parameters normalizes keys: { 'val1': 2.0, 'non_existent': 5.0, 'val1': 3.0 } -> 'val1' gets 3.0 overwriting 2.0
    
    with DynaKeywordReader(str(k_file)) as reader:
        reader.set_parameters(updates)
        
        keywords = list(reader.keywords())
        param_kw = next(kw for kw in keywords if kw.type == KeywordType.PARAMETER)
        
        # Helper (simplified)
        vals = param_kw.cards['Card 1']['VAL1']
        names = param_kw.cards['Card 1']['PRMR1']
        
        assert names[0] == "Rval1"
        assert float(vals[0]) == 3.0

def test_parameters(tmp_path):
    """Test the parameters() method."""
    k_file = tmp_path / "test_get_params.k"
    # Note: PARAMETER_EXPRESSION uses fixed width: PRMR1 (10 chars), EXPRESSION1 (70 chars)
    # So Rarea needs to be padded to 10 chars.
    content = """*KEYWORD
*PARAMETER
Rlength, 10.5, Icount, 5
Rwidth, 3.2
*PARAMETER_EXPRESSION
Rarea     Rlength * Rwidth
*END
"""
    k_file.write_text(content, encoding="utf-8")

    with DynaKeywordReader(str(k_file)) as reader:
        params = reader.parameters()
        
        assert len(params) == 4
        assert params["length"] == 10.5
        assert params["count"] == 5
        assert params["width"] == 3.2
        assert params["area"].strip() == "Rlength * Rwidth"

def test_parameters_with_spaces(tmp_path):
    """Test that parameters with spaces between type and name are handled correctly."""
    k_file = tmp_path / "test_spaces.k"
    # Testing both *PARAMETER and *PARAMETER_EXPRESSION with internal spaces
    content = """*KEYWORD
*PARAMETER
R  dist, 100.0, I  count, 42
*PARAMETER_EXPRESSION
R  area    R dist * 2.0
*END
"""
    k_file.write_text(content, encoding="utf-8")

    with DynaKeywordReader(str(k_file)) as reader:
        params = reader.parameters()
        assert "dist" in params
        assert params["dist"] == 100.0
        assert "count" in params
        assert params["count"] == 42
        assert "area" in params
        assert params["area"].strip() == "R dist * 2.0"

        # Test set_parameters with these
        reader.set_parameters({"dist": 200.0, "area": "R dist * 3.0"})
        
        # Verify in memory
        params_updated = reader.parameters()
        assert params_updated["dist"] == 200.0
        assert params_updated["area"].strip() == "R dist * 3.0"