# LS-DYNA® Keyword Reader (dynakw)

A Python library for reading, editing, and writing LS-DYNA keyword files.

The library is designed to scale by incorporating LS-DYNA documentation and keyword examples.

The maintenance and expansion of the library is automated by supplying the relevant LS-DYNA information
to AI coding agents, the details of which are handled by the Gemini slash commands provided.



# Status

Currently implemented:

 - \*BOUNDARY\_PRESCRIBED\_MOTION  
 - \*ELEMENT\_SHELL  
 - \*ELEMENT\_SOLID 
 - \*MAT\_ELASTIC 
 - \*NODE
 - \*PARAMETER 
 - \*PARAMETER_EXPRESSION 
 - \*PART 
 - \*SECTION\_SHELL
 - \*SECTION\_SOLID

The other keywords are preserved as raw text, which can be written out unchanged, allowing
the complete deck to be edited.



# Usage
To read a file and print the keywords:

```
import sys
from dynakw import DynaKeywordReader, KeywordType

with DynaKeywordReader('lsdyna_exa.k') as dkr:

    # to access all keywords
    for kw in dkr.keywords():
        kw.write(sys.stdout)

    # reading a specific keyword
    for kw in dkr.find_keywords(KeywordType.NODE):
        kw.write(sys.stdout)
```

A keywords have a `type` and a `cards` member. 
The values inside the `cards` member are
dictionaries containing the data stored as numpy arrays
following the LS-DYNA documentation.
For example, a scale factor can be changed as follows:

```
# To modify data in a specific keyword
if kw.type == KeywordType.BOUNDARY_PRESCRIBED_MOTION:
    kw.cards['Card 1']['SF'] = kw.cards['Card 1']['SF'] * 1.5

# The edited file can be saved: 
dkr.write('exa2.k')
```

To change the parameter values specified using \*PARAMETER:

```
parameters_to_change = {
        "rterm": 0.5,
        "rplot": "term/(states-50) * 2.0"
}
dkr.edit_parameters(parameters_to_change)
dkr.write(output_file)
```

See also the code in the examples directory for more usage.


# Installation

Install dynakw using pip:

```
pip install dynakw
```



# Example problems
The example problems demonstrate:

 - Printing the content of an LS-DYNA input deck.
 - Editing an LS-DYNA input deck.
 - Setting parameter values in an LS-DYNA input deck.
 - Displaying the mesh using PyVista [^1].
 - Converting LS-DYNA input to Radioss input.



# More documentation
See the docs directory.




# Contributing
Contributions are welcome! You can contribute either keywords examples for the QA or enhancements to the code reading the keywords.

This is easily done using AI coding agents considering the relevant LS-DYNA keyword chapter,
an example keyword deck, and the existing code.


## Adding a keyword using the Gemini CLI
Use the following slash commands:

```
\generate_instructions SECTION_SPH
\implement_keyword SECTION_SPH
\update_qa
```

The `\generate_instructions SECTION_SPH` with create a file named `SECTION_SPH_instructions.txt`,
which is used by `\implement_keyword`.

See .gemini/commands/\*.toml for the prompts and the GEMINI.md files for an explanation of the code structure.


## Manually adding a new keyword
To add a keyword manually:

1. Add the new keyword to the `KeywordType` enum in `dynakw/core/enums.py`.
2. Create a new Python file in the `dynakw/keywords/` directory named after the keyword.
3. Implement the keyword class, inheriting from `LSDynaKeyword` and providing the `_parse_raw_data` and `write` methods.
4. The unit tests should work for your new keyword (they use the enum from step 1). This requires that the keyword be present in test/full\_files/\*.k.



## Contributing LS-DYNA keyword examples
If you have LS-DYNA input decks, please consider contributing them as examples. This helps ensure the quality and
correctness of the library. A contribution can be as small as a single keyword definition.
Contributing a keyword is how you ensure that it will always be read correctly by the library.

The keywords should be added to the test/full\_files/ directory.

Having many keyword contributions is important because LS-DYNA has evolved to accomodate
many variations of the keywords.



## Testing
The code in the test directory can be exercised using 'python3 run_tests.py'.
This step is essential in a new checkout because it create test data from the keyword contributions.

The `\update_qa` slash command can be used to update the tests.


# Trademarks and related
LS-DYNA® is a registered trademark of ANSYS® Inc.

LS-DYNA examples can be downloaded at https://www.dynaexamples.com/ [^2].


# License
This project is licensed under the MIT License.


[^1]: If this is your only use case then `lsdyna-mesh-reader` is an alternative. `lsdyna-mesh-reader` however only supports the reading of the nodes and linear elements, so the plotting of loads etc. is not possible.

[^2]: The examples are currently provided free of charge, please see the instructions on the website, specifically the home page.

