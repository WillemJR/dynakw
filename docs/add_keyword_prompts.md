
# Example prompts
Below are some prompts frequently used to add keywords in the project.

The prompts may need editing; for example, replacing \*ELEMENT_SHELL with \*SECTION_TSHELL. 


## Generating instructions using claude
You are a software architect. 
We are creating a library reading LS-DYNA keywords.
Another program understands how to create the code, your responsibility is to explain
the layout of the keyword from the attached pdf file.
Use the attached pdf to create instructions to a code generating LLM on how to
read this ls-dyna keyword. The instructions should only address the layout of the keyword and the different ways the data
can be specified. Do not specify the software implementation or logic.


## Generating code using windsurf
Create a file in /core/keywords to read LS-DYNA \*PART keywords.
Example keyword input can be found in @test/keywords/PART.k 

See @docs/DESIGN.md for a description of how the architecture works.

Refer to @dynakw/utils/format_parser.py, @dynakw/keywords/lsdyna_keyword.py,
@dynakw/core/enums.py,  and @dynakw/core/parser.py to understand the implementation.

Use the implementation of the \*BOUNDARY_PRESCRIBED_MOTION
keyword in @core/keywords/ELEMENT_SOLID.py as a concrete example.

The order of implementing the keyword is:
1) First add it to @dynakw/core/enums.py.
2) Then run @test/utils/file_splitter.py.
3) Create the file reading the keyword in @dynakw/keywords similar to the concrete example given.
4) Update @dynakw/utils/format_parser.py to use the new keyword.
5) Check for any other changes needed.

Do not add a test.


<< Claude output >>


# Using windsurf to add a test
Create a test in @test directory to test the reading of \*PART. 
Use @test/test_boundary_prescribed_motion.py as a example.
The test must read @test/keywords/ELEMENT_SHELL.k and write out the keywords afterwards.



