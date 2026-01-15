
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


Setting parameters (*PARAMETER) values
--------------------------------------

The library can be used to set the values of parameters
inside a keyword file. The file must be saved afterwards for
the setting to take effect.

To obtain the parameter names and values specified using *PARAMETER:

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
* Check out more :doc:`examples` for advanced use cases
* Learn about different :doc:`keyword_types` available in LS-DYNA

