"""Base keyword class and specific keyword implementations"""

import pandas as pd
import io
from typing import Dict, Any, Optional, TextIO
from .enums import KeywordType

class DynaKeyword:
    """Base class for LS-DYNA keywords"""
    
    def __init__(self, keyword_type: KeywordType, raw_data: str = ""):
        self.type = keyword_type
        self.raw_data = raw_data
        self.cards: Dict[str, pd.DataFrame] = {}
        self._original_line = ""
        
    def add_card(self, card_name: str, dataframe: pd.DataFrame):
        """Add a card (dataframe) to the keyword"""
        self.cards[card_name] = dataframe
        
    def get_card(self, card_name: str) -> Optional[pd.DataFrame]:
        """Get a card by name"""
        return self.cards.get(card_name)
    
    @property 
    def Card_ID(self) -> Optional[pd.DataFrame]:
        """Access to Card ID"""
        return self.cards.get("Card_ID")
    
    @property
    def Card1(self) -> Optional[pd.DataFrame]:
        """Access to Card 1"""
        return self.cards.get("Card1")
    
    @property
    def Card2(self) -> Optional[pd.DataFrame]:
        """Access to Card 2"""
        return self.cards.get("Card2")
        
    @property 
    def Card3(self) -> Optional[pd.DataFrame]:
        """Access to Card 3"""
        return self.cards.get("Card3")
    
    def write(self, file_obj: TextIO):
        """Write the keyword to a file object"""
        if self.type == KeywordType.UNKNOWN:
            # Write raw data for unknown keywords
            file_obj.write(self.raw_data)
            return
            
        # Write keyword header
        file_obj.write(f"{self._original_line}\n")
        
        # Write cards in order
        for card_name in sorted(self.cards.keys()):
            df = self.cards[card_name]
            if df is not None and not df.empty:
                self._write_card(file_obj, df)
                
    def _write_card(self, file_obj: TextIO, df: pd.DataFrame):
        """Write a single card to file"""
        for _, row in df.iterrows():
            line = ""
            for col in df.columns:
                value = row[col]
                if pd.isna(value):
                    line += "          "  # 10 spaces for empty field
                elif isinstance(value, int):
                    line += f"{value:>10d}"
                elif isinstance(value, float):
                    line += f"{value:>10.4f}"
                else:
                    line += f"{str(value):>10s}"
            file_obj.write(line.rstrip() + "\n")

