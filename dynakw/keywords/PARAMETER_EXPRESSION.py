"Implementation of the *PARAMETER_EXPRESSION keyword."

from typing import TextIO, List
import numpy as np

from dynakw.keywords.lsdyna_keyword import LSDynaKeyword


class ParameterExpression(LSDynaKeyword):
    """
    Implements the *PARAMETER_EXPRESSION keyword.
    """
    keyword_string = "*PARAMETER_EXPRESSION"
    keyword_aliases = []

    def __init__(self, keyword_name: str, raw_lines: List[str] = None):
        super().__init__(keyword_name, raw_lines)

    def _parse_raw_data(self, raw_lines: List[str]):
        """
        Parses the raw data for *PARAMETER_EXPRESSION.
        """
        card_lines = [line for line in raw_lines[1:]
                      if line.strip() and not line.startswith('$')]
        if not card_lines:
            return

        # Card 1 is repeatable
        # Format: PRMR1 (10), EXPRESSION1 (70)
        prmr_list = []
        expression_list = []

        # We define the field lengths explicitly for this card
        # Field 1: 10 chars, Field 2: 70 chars (spanning 2-8)
        field_lens = [10, 70]
        field_types = ["A", "A"]

        for line in card_lines:
            data = self.parser.parse_line(line, field_types, field_len=field_lens)
            prmr_list.append(data[0])
            expression_list.append(data[1])

        if prmr_list:
            self.cards["Card 1"] = {
                "PRMR1": np.array(prmr_list, dtype=object),
                "EXPRESSION1": np.array(expression_list, dtype=object)
            }

    def write(self, file_obj: TextIO):
        """Writes the *PARAMETER_EXPRESSION keyword to a file."""
        file_obj.write(f"{self.full_keyword}\n")

        card1 = self.cards.get("Card 1")
        if card1 is not None:
            prmr = card1.get("PRMR1")
            expression = card1.get("EXPRESSION1")
            
            if prmr is not None and expression is not None and len(prmr) > 0:
                # We need to construct the header carefully because of the spanning field
                # Standard header generator might not handle spans well, so we do it manually or semi-manually
                # Or we assume the parser's format_header can just take the column names.
                # However, EXPRESSION1 spans multiple columns.
                # Let's write a comment header that reflects the structure.
                # Format: PRMR1 (10), EXPRESSION1 (70)
                
                # Standard header approach:
                # $# PRMR1     EXPRESSION1
                # The 'EXPRESSION1' label should probably be placed appropriately.
                # Since we are writing a custom layout, let's construct the header string manually 
                # to match the visual layout.
                
                header_str = "$#   prmr1                                                            expression1\n"
                file_obj.write(header_str)

                for p, e in zip(prmr, expression):
                    # Format PRMR1 (10 chars)
                    s_prmr = self.parser.format_field(p, "A", field_len=10)
                    # Format EXPRESSION1 (70 chars)
                    s_expr = self.parser.format_field(e, "A", field_len=70)
                    
                    file_obj.write(f"{s_prmr}{s_expr}\n")
