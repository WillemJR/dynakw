# LS-DYNA™ Keywords Reader Library (dynakw)

A Python library for reading, parsing, editing, and writing LS-DYNA keyword files.

The library is designed to scale by incorporating LS-DYNA documentation and keyword examples, using prompt examples from the documentation.
The maintenance and expansion of the library is automated by supplying this information to AI coding agents.



# Status
Currently implemented:
- \*NODE
- \*ELEMENT\_SOLID
- \*SECTION\_SOLID
- \*PART 
- \*MAT\_ELASTIC 
- \*BOUNDARY\_PRESCRIBED\_MOTION

The other keywords are preserved as raw text and type unknown. They can be written out unchanged, allowing
any deck to be edited.



# Usage
To read a file and print the keywords:
```
dkw = DynaKeywordFile( 'lsdyna_exa.k' )

for keyword in dkw.keywords:
    keyword.write(sys.stdout)
```

The values inside a keyword are accessed using dictionaries following the LS-DYNA documentation with
the data stored as numpy arrays as applicable.
For example, a scale factor can be changed as follows:
```
kw.cards['Card 1']['SF'] = kw.cards['Card 1']['SF'] * 1.5
```

See the code in the examples directory for more usage information.


# More documentation
See the docs directory.




# Contributing
Contributions are welcome! You can contribute either keywords examples for the QA or enhancements to the code 
reading the keywords.


## Contributing support for a new keyword
The is easily done using AI coding agents considering the relevant LS-DYNA keyword chapter, an example keyword deck,
and the existing code.

Please follow the existing structure:
1. Add the new keyword to the `KeywordType` enum in `dynakw/core/enums.py`.
2. Create a new Python file in the `dynakw/keywords/` directory named after the keyword.
3. Implement the keyword class, inheriting from `LSDynaKeyword` and providing the `_parse_raw_data` and `write` methods.
4. The unit tests should work for your new keyword (they use the enum from step 1).

See the docs/add_keyword_prompts.md for example prompts.


## Contributing LS-DYNA examples
If you have LS-DYNA input decks, please consider contributing them as examples. This helps ensure the quality and
correctness of the library. A contribution can be as small as a single keyword definition.
Contributing a keyword is how you ensure that it will always be read correctly by the library.

The keywords should be added to the test/full_files/ directory.

Having many keyword contributions is important because LS-DYNA has evolved to accomodate many variations of
the keywords, not all of which are documented in the manual.


## Testing
The code in the test directory can be exercised using 'python3 run_tests.py'.
This step is essential in a new checkout because it create test data from the keyword contributions.



# Trademarks
LS-DYNA™ is a registered trademark of ANSYS Inc.

LS-DYNA examples can be downloaded at https://www.dynaexamples.com/ .
This is currently free of charge, please see the instructions on the website, specifically the home page.


# License
This project is licensed under the MIT License.
