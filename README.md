# LS-DYNA :tm: Keywords Reader Library (dynakw)

A Python library for reading, parsing, editing, and writing LS-DYNA keyword files.

The library is designed to be extended using the LS-DYNA documentation, LS-DYNA keyword examples, and the prompt examples in the documentation. The goal is to fully automate the creation and maintenance of the library by supplying the relevant LS-DYNA documentation and keyword examples.


# Documentation
See the docs directory.



# STATUS
Currently implemented:
- \*NODE
- \*ELEMENT\_SOLID
- \*SECTION\_SOLID
- \*PART 
- \*MAT\_ELASTIC 
- \*BOUNDARY\_PRESCRIBED\_MOTION

Unknown keywords are preserved as raw text and can be written back unchanged.


# Contributing
Contributions are welcome! You can contribute either keywords examples for the QA or enhancements to the code 
reading the keywords.


## Contributing support for a new keyword
Please follow the existing structure:
1. Add the new keyword to the `KeywordType` enum in `dynakw/core/enums.py`.
2. Create a new Python file in the `dynakw/keywords/` directory named after the keyword.
3. Implement the keyword class, inheriting from `LSDynaKeyword` and providing the `_parse_raw_data` and `write` methods.
4. The unit tests should work for your new keyword (they are informed by step 1).

The is easily done using a LLM considering the relevant LS-DYNA keyword chapter, an example keyword deck,
and the existing code. See docs/add_keyword_prompts.md for example prompts.


## Contributing LS-DYNA examples
If you have LS-DYNA input decks, please consider contributing them as examples. This helps ensure the quality and
correctness of the library. A contribution can be as small as a single keyword definition.

Having many keyword contributions is important because LS-DYNA has evolved to accomodate many variations of
the keywords, not all documented in the manual.


# Trademarks
LS-DYNA :tm: trade is a registered trademark of ANSYS Inc.


# License
This project is licensed under the MIT License.
