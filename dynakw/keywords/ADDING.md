
# ------------------------  claude
You are a software architect.  Use the attached pdf to create instructions to a code generating LLM on how to
read this ls-dyna keyword. The instructions should only address the layout of the keyword and the different ways the data
can be specified. Do not specify the software implementation or logic.


# ------------------------  windsurf

Create a file in /core/keywords to read LS-DYNA \*ELEMENT_SHELL keywords.
Example keyword input can be found in @test/keywords/ELEMENT_SHELL.k 

See @dynakw/DESIGN.md for a description of how the architecture works.

Refer to @dynakw/utils/format_parser.py, @dynakw/keywords/lsdyna_keyword.py,
@dynakw/core/enums.py,  and @dynakw/core/parser.py to understand the implementation.

Use the implementation of the \*BOUNDARY_PRESCRIBED_MOTION
keyword in @core/keywords/ELEMENT_SOLID.py as a concrete example.



# ------------------------  windsurf add test
Create a test in @test directory to test the reading of \*ELEMENT_SHELL. 
Use @test/test_boundary_prescribed_motion.py as a example.
The test must read @test/keywords/ELEMENT_SHELL.k and write out the keywords afterwards.


