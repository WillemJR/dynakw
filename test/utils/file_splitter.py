"""Utility to split LS-DYNA files by keyword"""

import os
import re
import sys
sys.path.append( '.' )# Ensure the dynakw package is in the path
from pathlib import Path
from typing import List, Dict

from dynakw.core.enums import KeywordType

class KeywordFileSplitter:
    """Split LS-DYNA files into individual keyword segments"""
    
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.allowed_keywords = {member.name for member in KeywordType if member.name != 'UNKNOWN'}
        
    def split_all_files(self):
        """Split all files in the input directory"""
        for file_path in self.input_dir.glob("*.k"):
            self.split_file(file_path)
            
    def split_file(self, file_path: Path):
        """Split a single file into keyword segments"""
        print(f"Splitting file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        keywords = self._extract_keywords(content)
        
        for keyword_name, keyword_data in keywords.items():
            self._append_to_keyword_file(keyword_name, keyword_data)
    
    def _extract_keywords(self, content: str) -> Dict[str, List[str]]:
        """Extract keywords from file content"""
        lines = content.split('\n')
        keywords = {}
        current_keyword = None
        current_lines = []
        
        for line in lines:
            line = line.rstrip()
            
            # Check if this is a keyword line
            if line.startswith('*') and not line.startswith('$'):
                # Save previous keyword
                if current_keyword and current_lines:
                    keyword_name = self._normalize_keyword_name(current_keyword)
                    if keyword_name in self.allowed_keywords:
                        if keyword_name not in keywords:
                            keywords[keyword_name] = []
                        keywords[keyword_name].append('\n'.join(current_lines))
                
                # Start new keyword
                current_keyword = line
                current_lines = [line]
            else:
                # Add line to current keyword
                if current_keyword:
                    current_lines.append(line)
        
        # Save last keyword
        if current_keyword and current_lines:
            keyword_name = self._normalize_keyword_name(current_keyword)
            if keyword_name in self.allowed_keywords:
                if keyword_name not in keywords:
                    keywords[keyword_name] = []
                keywords[keyword_name].append('\n'.join(current_lines))
        
        return keywords
    
    def _normalize_keyword_name(self, keyword_line: str) -> str:
        """Normalize keyword name for filename"""
        # Remove * and clean up the name
        name = keyword_line.strip().lstrip('*')
        # Remove format modifiers
        name = name.rstrip('+-% ')
        # Replace invalid filename characters
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        return name.upper()
    
    def _append_to_keyword_file(self, keyword_name: str, keyword_data: str):
        """Append keyword data to the appropriate file"""
        filename = f"{keyword_name}.k"
        file_path = self.output_dir / filename
        
        with open(file_path, 'a') as f:
            if isinstance(keyword_data, list):
                f.write(''.join(keyword_data))
            else:
                f.write(keyword_data)
            f.write('\n\n')  # Add separation between keyword instances

def main():
    """Main function to run the file splitter"""
    splitter = KeywordFileSplitter('test/full_files', 'test/keywords')
    splitter.split_all_files()
    print("File splitting completed!")

if __name__ == "__main__":
    main()

