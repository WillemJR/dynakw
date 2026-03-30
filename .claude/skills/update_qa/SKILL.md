---
description: Review and update QA reference files in test/results
---

You are helping a software developer test a library.
The library reads and writes LS-DYNA keywords.

The test program results are stored in test/results and are named
<<KEYWORD>>_new.k and must be compared to the correct file named <<KEYWORD>>_reference.k.
The input file to the test is stored in test/keywords/<<KEYWORD>>.k

Update the test using the following steps:
 1 Consider only the KEYWORDs where test/results/<<KEYWORD>>_new.k and
   test/results/<<KEYWORD>>_reference.k differ.
 2 Display test/results/<<KEYWORD>>_reference.k and test/results/<<KEYWORD>>_new.k
   to the user using the meld tool.
 3 Ask the user if the new version is correct.
 4 If the new version is correct, replace test/results/<<KEYWORD>>_reference.k
   with test/results/<<KEYWORD>>_new.k.

If the user asks to see the original input then display test/keywords/<<KEYWORD>>.k,
test/results/<<KEYWORD>>_reference.k and test/results/<<KEYWORD>>_new.k to the user
using the meld tool.
