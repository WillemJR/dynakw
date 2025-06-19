# LS-DYNA Keywords Reader Library (dynakw)

A Python library for reading, parsing, editing, and writing LS-DYNA keyword files.

The library is designed that it can improve itself when presented
with more ls-dyna examples and documentation.
Also it runs QA on every keyword contributed to the project.

# WORK IN PROGRESS
This is projected to be useful to all at the end of June 2025.


# Contributing
It has a architechture that works as follows:
1) It has a core facility that allows itself to grow.
2) And it can generate code for any keyword using:
2.1) the chapter in the LS-Dyna manual and
2.2) actual ls-dyna input decks containing the keywords.
3) It runs QA on every keyword ever presented to it (the decks in 2.2).
So if you upload your LS-DYNA input deck, then it will forever run correctly.

## Contributing LS-DYNA examples
As stated, if you upload your LS-DYNA input deck to the project, then it will forever run correctly.
It is therefore the contribution of LS-DYNA input decks that insures the quality of the library.

A contribution can be as small as a single keyword.
There is no requirement for the input deck  to run, or to make sense to LS-DYNA.
It is only required that the keyword is correctly specfied for LS-DYNA.

If we keep on adding large input decks then at a point we will exceed the github size limits.
Solutions for this will be possible, but lets delay that day. So please trim down the input deck to be
small -- deleting \*NODE and \*ELEMENT should make a big difference.


# Getting Started


## General Prerequisites


## Building


# License


