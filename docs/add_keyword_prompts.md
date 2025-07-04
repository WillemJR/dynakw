
# Example prompts
Below are some prompts frequently used to add keywords in the project.

The prompts may need editing; for example, replacing \*ELEMENT_SHELL with \*SECTION_TSHELL. 

You can use @docs/extract_pdf_pages.py to extract the pages from the LS-DYNA manual.


## Prompt for generating instructions using Claude
You are a software architect. 
We are creating a library reading LS-DYNA keywords.
Another program understands how to create the code.
Your responsibility is to explain the layout of the keyword from the attached pdf file.
Use the attached pdf to create instructions to a code generating LLM on how to read this ls-dyna keyword.
The instructions should only address the layout of the keyword data and the different ways the data can be specified.

The keyword is composed of several cards. The card data is summarized in a table.
The top row of the table specifies the card name and the number of columns. Not all of the columns are used,
and the number of columns include the number of unused columns.
The variable names are also specified, and the number of variables names may be less than the number of fields.
If a variable name is not specified, then the Variable name is 'Unused'.
If a variable name spans multiple columns, then the card is double wide.
The default field width is 10.  If a card has 10 fields, state that the field width is 8.
If a card has 10 fields, and the card is double wide,  state that the field width for the card is 16.

Do not specify the software implementation or logic.


## Prompt for generating code using windsurf
Create a file in @core/keywords to read LS-DYNA \*ELEMENT_SHELL keywords.

Example keyword input can be found in @test/keywords/ELEMENT_SHELL.k 

See @docs/architecture.md for a description of how the architecture works.

Refer to @dynakw/utils/format_parser.py, @dynakw/keywords/lsdyna_keyword.py,
@dynakw/core/enums.py,  and @dynakw/core/parser.py to understand the implementation.

Use the implementation of the \*ELEMENT_SOLID keyword in @core/keywords/ELEMENT_SOLID.py as a concrete example.

The order of implementing the keyword is:
1) First add it to @dynakw/core/enums.py.
2) Then run @test/utils/file_splitter.py using the command 'python3 test/utils/file_splitter.py'
   This will create the file @test/keywords/splitted/ELEMENT_SHELL.k.
3) Create the file reading the keyword in @dynakw/keywords similar to the concrete example given.
4) Update @dynakw/utils/format_parser.py to use the new keyword.
5) Do the following checks on the code.
5.1) Check keyword.cards.keys() are "Card 1", "Card 2", etc.
5.2) Check that the keyword data is stored in the following format:
   ```
   keyword.cards['Card 1']['N1'] = numpy.array( [2,11,3,99,1], dtype=int )
   ```
5.3) Look at both @test/keywords/ELEMENT_SHELL.k and @core/keywords/ELEMENT_SHELL.py and
    think hard on whether that code will read and write that keyword file.
5.4) Check for any other changes needed.

Do not add a test.

Below is a description of the layout of the \*ELEMENT_SHELL keyword.

<< Claude output >>


# Using windsurf to add a test
Create a test in @test directory to test the reading of \*PART. 
Use @test/test_boundary_prescribed_motion.py as a example.
The test must read @test/keywords/PART.k and write out the keywords afterwards.



