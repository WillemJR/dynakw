
# Example prompts
Below are some prompts frequently used to add keywords in the project.

The prompts may need editing; for example, replacing \*ELEMENT_SHELL with \*SECTION_TSHELL. 

The steps I used to add \*SECTION_SHELL are:
* Extract the SECTION_SHELL keyword section from the manual.
* Submit this file to Claude together with prompt below.
* Edit the example prompt to Windsurf to consider SECTION_SHELL.
* Submit the prompt to Windsurf together with the Claude output.

You can use @docs/extract_pdf_pages.py to extract the pages from the LS-DYNA manual.

The use of AI coding agents for the project can be improved. Unfortunately it is not yet clear
what the best direction for an open source project is.


## Prompt for generating instructions using Claude
You are a software architect. 
We are creating a library reading LS-DYNA keywords.
Another program understands how to create the code.
Your responsibility is to explain the layout of the keyword from the attached pdf file.
Use the file to create instructions to a code generating LLM on how to read this ls-dyna keyword.
The instructions should only address the layout of the keyword data and the different ways the data can be specified.

The keyword is composed of several cards. The card data is summarized in a table.
The top row of the table specifies the card name and the number of columns. Not all of the columns are used,
and the number of columns include the number of unused columns.
The variable names are also specified, and the number of variables names may be less than the number of fields.
If a variable name is not specified, then the Variable name is 'Unused'.
If a variable name spans multiple columns, then the card is double wide.
The default field width is 10.  If a card has 10 fields, state that the field width is 8.
If a card has 10 fields, and the card is double wide,  state that the field width for the card is 16.
Specify whether a card is required, optional, or conditional.

Do not specify the software implementation or logic.


## Prompt for generating code using windsurf
Create a file in @core/keywords to read LS-DYNA \*SECTION_SHELL keywords.

Example keyword input can be found in @test/keywords/SECTION_SHELL.k 

See @docs/architecture.md for a description of how the architecture works.

Refer to @dynakw/utils/format_parser.py, @dynakw/keywords/lsdyna_keyword.py,
@dynakw/core/enums.py,  and @dynakw/core/parser.py to understand the implementation.

Use the implementation of the \*SECTION_SOLID keyword in @core/keywords/SECTION_SOLID.py as a concrete example.

The steps required to implement the keyword are:
1) First add it to @dynakw/core/enums.py.
2) Then run @test/utils/file_splitter.py using the command 'python3 test/utils/file_splitter.py'
   This will create the file @test/keywords/SECTION_SHELL.k.
3) Create the file reading the keyword in @dynakw/keywords similar to the concrete example given.
4) Update @dynakw/utils/format_parser.py to use the new keyword.
5) Do the following checks on the code.
5.1) Check keyword.cards.keys() are "Card 1", "Card 2", etc.
5.2) Check that the keyword data is stored in the following format:
   ```
   keyword.cards['Card 1']['N1'] = numpy.array( [2,11,3,99,1], dtype=int )
   ```
5.3) Look at both @test/keywords/SECTION_SHELL.k and @core/keywords/SECTION_SHELL.py and
    think hard on whether that code will read and write that keyword file.
5.4) Check for any other changes needed.

Do not add a test.

Below is a description of the layout of the \*SECTION_SHELL keyword.

<< Claude output >>


