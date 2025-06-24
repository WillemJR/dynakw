# LS-DYNA Keywords Reader Library (dynakw)

A Python library for reading, parsing, editing, and writing LS-DYNA keyword files.

The library is designed that it can improve itself when presented with more ls-dyna examples and documentation.


# WORK IN PROGRESS
This is projected to be useful to all at the end of June 2025.


# Documentation
See the docs directory.


# Contributing
Contributions are welcome! You can contribute either keywords examples for the QA or enhancements to the code 
reading the keywords.

## Contributing support for a new keyword
Please follow the existing structure:
1. Add the new keyword to the `KeywordType` enum in `dynakw/core/enums.py`.
2. Create a new Python file in the `dynakw/keywords/` directory named after the keyword.
3. Implement the keyword class, inheriting from `LSDynaKeyword` and providing the `_parse_raw_data` and `write` methods.
4. Add unit tests for your new keyword.

The is easily done using a LLM considering the relevant LS-DYNA keyword chapter, an example keyword deck,
and the existing code. See docs/add_keyword_prompts.md for example prompts.

## Contributing LS-DYNA examples
If you have LS-DYNA input decks, please consider contributing them as examples. This helps ensure the quality and correctness of the library. A contribution can be as small as a single keyword definition.

Having many keyword contributions is important because LS-DYNA has evolved to accomodate many variations of
the keywords, not all documented in the manual.


# License
This project is licensed under the MIT License.
