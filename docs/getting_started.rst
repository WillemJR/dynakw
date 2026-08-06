
Getting Started
===============

This guide will help you get started with dynakw for reading and manipulating LS-DYNA keyword files.

Installation
------------

Install dynakw using pip:

.. code-block:: bash

   pip install dynakw

Basic Usage
-----------

Reading and Printing Keywords
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To read a file and print all keywords:

.. code-block:: python

   import sys
   from dynakw import DynaKeywordReader, KeywordType

   with DynaKeywordReader('lsdyna_exa.k') as dkr:
       # Access all keywords
       for kw in dkr.keywords():
           kw.write(sys.stdout)

Reading Specific Keywords
~~~~~~~~~~~~~~~~~~~~~~~~~

You can filter and read specific keyword types:

.. code-block:: python

   import sys
   from dynakw import DynaKeywordReader, KeywordType

   with DynaKeywordReader('lsdyna_exa.k') as dkr:
       # Reading only NODE keywords
       for kw in dkr.find_keywords(KeywordType.NODE):
           kw.write(sys.stdout)

Understanding Keyword Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each keyword has two main members:

* **type** - The keyword type (e.g., ``KeywordType.NODE``, ``KeywordType.BOUNDARY_PRESCRIBED_MOTION``)
* **cards** - Dictionary containing the data stored as numpy arrays following the LS-DYNA documentation

Modifying Keyword Data
----------------------

You can modify data within keywords by accessing the cards dictionary. For example, to change a scale factor:

.. code-block:: python

   from dynakw import DynaKeywordReader, KeywordType

   with DynaKeywordReader('lsdyna_exa.k') as dkr:
       for kw in dkr.keywords():
           # Modify data in a specific keyword
           if kw.type == KeywordType.BOUNDARY_PRESCRIBED_MOTION:
               kw.cards['Card 1']['SF'] = kw.cards['Card 1']['SF'] * 1.5

Saving Modified Files
~~~~~~~~~~~~~~~~~~~~~

After making changes, save the modified file:

.. code-block:: python

   from dynakw import DynaKeywordReader, KeywordType

   with DynaKeywordReader('lsdyna_exa.k') as dkr:
       # Make your modifications
       for kw in dkr.keywords():
           if kw.type == KeywordType.BOUNDARY_PRESCRIBED_MOTION:
               kw.cards['Card 1']['SF'] = kw.cards['Card 1']['SF'] * 1.5

       # Save the edited file
       dkr.write('exa2.k')


Setting parameters (``*PARAMETER``) values
------------------------------------------

The library can be used to set the values of parameters
inside a keyword file. The file must be saved afterwards for
the setting to take effect.

To obtain the parameter names and values specified using ``*PARAMETER``:

.. code-block:: python

   par_dict = dkr.parameters()

To change the parameter values:

.. code-block:: python

    # Configuration
    input_file = 'test/full_files/parameter.k'
    output_file = 'modified_parameters.k'

    # Parameters to change (Name -> New Value)
    parameters_to_change = {
        "rterm": 0.5,
        "istates": 100,
        "cpar2": "baz",
        "rplot": "term/(states-50) * 2.0"
    }


    with DynaKeywordReader(input_file) as dkr:
        dkr.set_parameters(parameters_to_change)

        dkr.write(output_file)



Discovering what is supported
-----------------------------

Rather than consulting a list that may have moved on, ask the library.  The
report is generated from the same card definitions that drive reading and
writing, so it always describes what the code actually does.

From the command line:

.. code-block:: bash

   python -m dynakw.manifest                            # summary table
   python -m dynakw.manifest --pattern '*SET_*'         # filter
   python -m dynakw.manifest --describe '*MAT_ELASTIC'  # cards and fields
   python -m dynakw.manifest --format json              # machine-readable

The summary lists every keyword, how many cards it has and whether it can be
built from data as well as read::

   KEYWORD                      CARDS  BUILD  NOTE
   *MAT_ELASTIC                     1  yes    schema-driven
   *NODE                            1  yes    schema-driven
   *PART                            2  yes    custom parse and write

``BUILD`` says whether a keyword can be *constructed* from data, which is the
question a program generating decks needs answered; see
:ref:`building-a-keyword`.  Writing back a keyword that was read from a file
works whatever it says.

And from Python:

.. code-block:: python

   import dynakw

   for spec in dynakw.supported_keywords():
       print(spec.keyword, spec.description)

.. note::

   Every keyword name begins with ``*``, which is also the wildcard character,
   so the pattern ``'*NODE'`` matches ``*SET_NODE`` as well as ``*NODE``.
   Bracket the star — ``'[*]NODE'`` — to match only ``*NODE``.

Inspecting a keyword's fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:func:`~dynakw.describe_keyword` describes one *concrete variant*, so a keyword
option that changes the card layout is reflected in the answer:

.. code-block:: python

   import dynakw

   spec = dynakw.describe_keyword('*MAT_ELASTIC_FLUID')

   print(spec.description)
   for card in spec.cards:
       print(card.name, '-', card.description)
       for f in card.fields:
           units = f' [{f.units}]' if f.units else ''
           print(f'   {f.name:8s} {f.type}{f.width}{units}  {f.description}')

Which reports the fluid form of the card::

   Card 1 - Material properties for the FLUID variant.
      MID      A10  Material ID; unique number or label
      RO       F10 [mass/volume]  Mass density
      K        F10 [stress]  Bulk modulus
   Card 2 - Viscosity and cavitation, FLUID variant only.
      VC       F10  Tensor viscosity coefficient; values between 0.1 and 0.5 are reasonable
      CP       F10 [stress]  Cavitation pressure (default 1e20)

Asking about ``'*MAT_ELASTIC'`` instead gives the seven-field solid form and no
Card 2.  A name that is not implemented raises
:class:`~dynakw.KeywordNotSupported`, suggesting near matches.

This is the intended way for a program that writes decks to check its
requirements up front:

.. code-block:: python

   import dynakw

   REQUIRED = ['*NODE', '*PART', '*SECTION_SOLID', '*MAT_ELASTIC']

   have = {s.keyword: s for s in dynakw.supported_keywords()}
   missing = [k for k in REQUIRED if k not in have]
   if missing:
       raise RuntimeError(f'dynakw {dynakw.__version__} lacks: {missing}')


.. _building-a-keyword:

Building a keyword from data
----------------------------

A keyword does not have to come from a file.  Construct one with just its name,
fill in ``cards``, and write it:

.. code-block:: python

   import numpy as np
   from dynakw.keywords.NODE import Node

   nodes = Node('*NODE')
   nodes.cards['Card 1'] = {
       'NID': np.array([1, 2, 3], dtype=np.int32),
       'X':   np.array([0.0, 10.0, 10.0]),
       'Y':   np.array([0.0,  0.0, 10.0]),
       'Z':   np.zeros(3),
       'TC':  np.zeros(3, dtype=np.int32),
       'RC':  np.zeros(3, dtype=np.int32),
   }

   with open('mesh.k', 'w') as fh:
       nodes.write(fh)

The field names and types come from :func:`~dynakw.describe_keyword`, so the
library will tell you what a card wants:

.. code-block:: python

   import dynakw

   card = dynakw.describe_keyword('*NODE').card('Card 1')
   [(f.name, f.type, f.required) for f in card.fields]

Every implemented keyword can be built this way — ``can_build`` is True for all
of them.  Where a keyword needs more than its declared fields, the requirement
is documented on the class and covered by a test; the common cases are:

* An option that changes the layout is selected by the keyword *name*, so build
  ``*PART_INERTIA`` rather than ``*PART`` when you want the inertia card.
* ``*PART`` matches each optional card to its part through a ``PID`` column,
  which every such card must carry.  A keyword option applies to the whole
  block, so an optional card needs a row for *every* part.
* On ``*SECTION_SHELL`` and ``*SECTION_SOLID``, count fields must agree with the
  cards they describe: ``NIP`` with the number of composite angles, ``LMC``
  with the number of user-defined constants.
* On ``*ELEMENT_SHELL``, the composite cards are 2D arrays of shape
  ``(n_elements, max_layers)`` alongside a 1D ``N_LAYERS``, and mid-side
  thicknesses are written only for elements that have mid-side nodes.

Setting values by parameter
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A built keyword can reference a ``*PARAMETER`` instead of a literal, so the deck
stays adjustable after it is generated:

.. code-block:: python

   from dynakw import ParameterRef
   from dynakw.keywords.MAT_ELASTIC import MatElastic

   mat = MatElastic('*MAT_ELASTIC')
   mat.cards['Card 1'] = {
       'MID': np.array([1], dtype=object),
       'RO':  np.array([7.85e-9]),
       'E':   np.array([ParameterRef('Emod')], dtype=object),   # writes &Emod
       'PR':  np.array([0.3]),
       'DA':  np.zeros(1), 'DB': np.zeros(1), 'K': np.zeros(1),
   }


Using an LLM
------------
The library is set up to work with the gemini LLM.
One way of using an LLM to to download the code,
start gemini inside the main directory, and asking gemini
to create an example of what you need.



Next Steps
----------

Now that you understand the basics, you can:

* Explore the :doc:`api` for complete reference documentation
* Learn which :doc:`keyword_types` are supported
* Read the :doc:`architecture` to see how card layouts are declared, which is
  also what you need to add a keyword
* Check out the ``examples/`` directory in the source repository for advanced use cases

