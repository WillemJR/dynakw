"""Parser for LS-DYNA fixed format fields"""

import re
from typing import List, Any, Union

class FormatParser:
    """Parser for LS-DYNA fixed format card fields"""
    
    def __init__(self):
        self.field_width = 10  # Standard field width
        self.long_field_width = 20  # Long format field width
        
    def parse_line(self, line: str, field_types: List[str], long_format: bool = False) -> List[Any]:
        """
        Parse a line according to field types
        
        Args:
            line: Input line
            field_types: List of field types ('I' for int, 'F' for float, 'A' for string)
            long_format: Whether to use long format (20 char fields vs 10)
        """
        width = self.long_field_width if long_format else self.field_width
        fields = []
        
        for i, field_type in enumerate(field_types):
            start = i * width
            end = start + width
            
            if start >= len(line):
                # Field is beyond line length, use default
                fields.append(None)
                continue
                
            field_str = line[start:end].strip()
            
            if not field_str:
                fields.append(None)
                continue
            
            try:
                if field_type == 'I':
                    fields.append(int(field_str))
                elif field_type == 'F':
                    fields.append(float(field_str))
                else:  # 'A' or anything else
                    fields.append(field_str)
            except ValueError:
                # If conversion fails, store as string
                fields.append(field_str)
        
        return fields
    
    def parse_line_generic(self, line: str, long_format: bool = False) -> List[Any]:
        """
        Parse a line with automatic type detection
        
        Args:
            line: Input line  
            long_format: Whether to use long format
        """
        width = self.long_field_width if long_format else self.field_width
        fields = []
        
        # Split line into fixed-width fields
        for i in range(0, len(line), width):
            field_str = line[i:i+width].strip()
            
            if not field_str:
                fields.append(None)
                continue
            
            # Try to determine type automatically
            if self._is_integer(field_str):
                fields.append(int(field_str))
            elif self._is_float(field_str):
                fields.append(float(field_str))
            else:
                fields.append(field_str)
        
        return fields
    
    def _is_integer(self, s: str) -> bool:
        """Check if string represents an integer"""
        try:
            int(s)
            return True
        except ValueError:
            return False
    
    def _is_float(self, s: str) -> bool:
        """Check if string represents a float"""
        try:
            float(s)
            return True
        except ValueError:
            return False
    
    def format_field(self, value: Any, field_type: str, long_format: bool = False) -> str:
        """
        Format a value according to field type
        
        Args:
            value: Value to format
            field_type: Field type ('I', 'F', 'A')
            long_format: Whether to use long format
        """
        width = self.long_field_width if long_format else self.field_width
        
        if value is None:
            return ' ' * width
        
        if field_type == 'I':
            return f"{int(value):>{width}d}"
        elif field_type == 'F':
            # Use appropriate precision for the field width
            if long_format:
                return f"{float(value):>{width}.6f}"
            else:
                return f"{float(value):>{width}.4f}"
        else:  # 'A'
            return f"{str(value):>{width}}"

