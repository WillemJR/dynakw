---
description: Implement an LS-DYNA keyword into the keyword reader
---

You are a python expert working on a library reading ls-dyna keywords.
You must create the dynakw/keywords/$ARGUMENTS.py file that reads the LS-DYNA $ARGUMENTS keyword.
You are to focus on only adding this keyword.

Read GEMINI.md for a description of how the architecture works.
Refer to dynakw/core/card_schema.py, dynakw/keywords/lsdyna_keyword.py,
dynakw/utils/format_parser.py, and dynakw/core/keyword_file.py to
understand the implementation.

Read the file $ARGUMENTS_instructions.txt for a description of the layout of the $ARGUMENTS keyword.

The preferred approach is declarative: define the keyword structure using
CardField and CardSchema class attributes. The base class then handles
parsing and writing automatically. Only override _parse_raw_data and write
when the card layout cannot be expressed declaratively (e.g. per-row
conditional cards or variable-length repeating groups).

Use dynakw/keywords/NODE.py as the reference example for a simple repeating
keyword, and dynakw/keywords/MAT_ELASTIC.py for a keyword with conditional
cards. Use dynakw/keywords/BOUNDARY_PRESCRIBED_MOTION.py as an example of
a keyword that requires a custom loop.

Example keyword input can be found in test/keywords/$ARGUMENTS.k

The steps required to implement the keyword are:
 1 First add it to dynakw/core/enums.py.
 2 Then run test/utils/file_splitter.py using the command 'python3 test/utils/file_splitter.py'
   This will create the file test/keywords/$ARGUMENTS.k.
 3 Create the file reading the keyword in dynakw/keywords using the declarative
   schema approach where possible.

Do the following checks on the code.
 1 Check keyword.cards.keys() are "Card 1", "Card 2", etc.
 2 Check that integer fields use dtype=np.int32 and float fields use dtype=np.float64.
   For example: `keyword.cards['Card 1']['N1'] = numpy.array([2, 11, 3, 99, 1], dtype=numpy.int32)`
 3 If using card_schemas: verify that CardField types ('I', 'F', 'A'), widths, and
   write_header flags match the keyword layout described in the instructions file.
 4 If using a custom write method: verify that it writes the header comment line
   before each card's data.
 5 Look at both test/keywords/$ARGUMENTS.k and dynakw/keywords/$ARGUMENTS.py and
   think hard on whether that code will correctly read and write that keyword file.
 6 Check for any other changes needed.

Do not add a test.
