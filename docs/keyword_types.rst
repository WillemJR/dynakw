
Supported Keywords
==================

Each supported LS-DYNA keyword is parsed into a dedicated class exposing its
data through the ``cards`` dictionary.  Any keyword not listed here is still
read and preserved verbatim as an ``Unknown`` block, so no data is lost when a
file is read and written back.

The ``type`` member of a keyword is a :class:`~dynakw.KeywordType` enumeration
value, which is what :meth:`~dynakw.DynaKeywordReader.find_keywords` filters on.

.. note::

   The tables on this page are written by hand, so treat the library itself as
   the authority::

      python -m dynakw.manifest

   :func:`~dynakw.supported_keywords` and :func:`~dynakw.describe_keyword`
   report the same information from the card definitions that drive reading and
   writing, down to the fields of each card, whether a keyword can be built as
   well as read, and which cards a particular option variant has.  See
   :doc:`getting_started`.

Geometry and mesh
-----------------

=============================  ==============================================
Keyword                        ``KeywordType``
=============================  ==============================================
``*NODE``                      ``KeywordType.NODE``
``*ELEMENT_SOLID``             ``KeywordType.ELEMENT_SOLID``
``*ELEMENT_SHELL``             ``KeywordType.ELEMENT_SHELL``
``*PART``                      ``KeywordType.PART``
=============================  ==============================================

Sections and materials
----------------------

=============================  ==============================================
Keyword                        ``KeywordType``
=============================  ==============================================
``*SECTION_SOLID``             ``KeywordType.SECTION_SOLID``
``*SECTION_SHELL``             ``KeywordType.SECTION_SHELL``
``*MAT_ELASTIC``               ``KeywordType.MAT_ELASTIC``
``*MAT_RIGID``                 ``KeywordType.MAT_RIGID``
=============================  ==============================================

``*MAT_ELASTIC`` is also accepted as ``*MAT_001`` and ``*MAT_RIGID`` as ``*MAT_020``.
Neither claims a longer material name that merely begins the same way:
``*MAT_ELASTIC_PLASTIC_HYDRO`` is MAT_010 and ``*MAT_RIGID_DISCRETE`` is MAT_220, so both
are preserved as ``Unknown`` rather than mis-read.

Sets
----

=============================  ==============================================
Keyword                        ``KeywordType``
=============================  ==============================================
``*SET_NODE``                  ``KeywordType.SET_NODE``
``*SET_SEGMENT``               ``KeywordType.SET_SEGMENT``
``*SET_SHELL``                 ``KeywordType.SET_SHELL``
``*SET_SOLID``                 ``KeywordType.SET_SOLID``
=============================  ==============================================

The set keywords accept the option suffixes described below.  ``COLLECT`` may
be appended to any of them; it does not change the card layout.  Whichever
option is used, the element or node data is always stored under ``'Card 2'``.

=================  ==========================================================
Keyword            Available options
=================  ==========================================================
``*SET_NODE``      *(blank)*, ``LIST``, ``COLUMN``, ``LIST_GENERATE``,
                   ``LIST_GENERATE_INCREMENT``, ``LIST_SMOOTH``, ``GENERAL``
``*SET_SHELL``     *(blank)*, ``LIST``, ``COLUMN``, ``LIST_GENERATE``,
                   ``LIST_GENERATE_INCREMENT``, ``GENERAL``
``*SET_SOLID``     *(blank)*, ``GENERATE``, ``GENERATE_INCREMENT``,
                   ``GENERAL``
=================  ==========================================================

Note that the option names differ between these keywords: ``*SET_SOLID`` uses
``GENERATE`` where ``*SET_NODE`` and ``*SET_SHELL`` use ``LIST_GENERATE``, and
it has no ``LIST`` or ``COLUMN`` option.  Its Card 1 carries ``SID`` and
``SOLVER`` only, with no ``DA1``-``DA4`` attribute defaults.

For example, to collect every solid element ID listed by an unset
(``<BLANK>``) option block:

.. code-block:: python

   import numpy as np
   from dynakw import DynaKeywordReader, KeywordType

   with DynaKeywordReader('sets.k') as dkr:
       for kw in dkr.find_keywords(KeywordType.SET_SOLID):
           if kw.option1:          # skip GENERATE / GENERAL variants
               continue
           card = kw.cards['Card 2']
           ids = np.concatenate([card[f'K{i}'] for i in range(1, 9)])
           print(kw.cards['Card 1']['SID'][0], np.sort(ids[ids != 0]))

Boundary conditions, constraints and parameters
-----------------------------------------------

===============================  ============================================
Keyword                          ``KeywordType``
===============================  ============================================
``*BOUNDARY_PRESCRIBED_MOTION``  ``KeywordType.BOUNDARY_PRESCRIBED_MOTION``
``*BOUNDARY_SPC_SET``            ``KeywordType.BOUNDARY_SPC_SET``
``*CONSTRAINED_JOINT_TYPE``      ``KeywordType.CONSTRAINED_JOINT``
``*PARAMETER``                   ``KeywordType.PARAMETER``
``*PARAMETER_EXPRESSION``        ``KeywordType.PARAMETER_EXPRESSION``
===============================  ============================================

``*CONSTRAINED_JOINT`` is a family: the joint variant is part of the keyword name and one
of it is mandatory.  All fourteen share the same cards, and only the type decides whether
the rotational properties card is present.

=========================  ==================================================
Joint type                 Rotational properties card
=========================  ==================================================
``SPHERICAL``              no
``REVOLUTE``               no
``CYLINDRICAL``            no
``PLANAR``                 no
``UNIVERSAL``              no
``TRANSLATIONAL``          no
``LOCKING``                no
``CONSTANT_VELOCITY``      no
``TRANSLATIONAL_MOTOR``    yes
``ROTATIONAL_MOTOR``       yes
``GEARS``                  yes
``RACK_AND_PINION``        yes
``PULLEY``                 yes
``SCREW``                  yes
=========================  ==================================================

The options ``ID``, ``LOCAL`` and ``FAILURE`` may follow the type in any order, each
adding its own card.  The related keywords ``*CONSTRAINED_JOINT_COOR``,
``*CONSTRAINED_JOINT_STIFFNESS`` and ``*CONSTRAINED_JOINT_USER_FORCE`` have different
layouts and are not implemented; they are preserved as ``Unknown``.

``*BOUNDARY_SPC_SET`` accepts the ``BIRTH_DEATH`` and ``ID`` options, in that order.  With
``BIRTH_DEATH`` each node set line is followed by its own birth/death line, and
``cards['Card 2']`` holds one row per row of ``cards['Card 1']``.  ``*BOUNDARY_SPC_NODE``
is not implemented.

Contact and loads
-----------------

===========================================  ==================================================
Keyword                                      ``KeywordType``
===========================================  ==================================================
``*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE``    ``KeywordType.CONTACT_AUTOMATIC_SURFACE_TO_SURFACE``
``*LOAD_BODY_OPTION``                        ``KeywordType.LOAD_BODY``
===========================================  ==================================================

``*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE`` accepts the options ``THERMAL`` or
``THERMAL_FRICTION``, then ``ID``, ``MPP`` and ``ORTHO_FRICTION``, in the manual's order.
Its cards are stored under the manual's names: ``'Card ID'``, ``'MPP 1'``, ``'MPP 2'``,
``'Card 1'`` to ``'Card 3'``, ``'THRM 1'``, ``'THRM 2'``, ``'THRM 2.1'``, ``'ORFR 1'`` to
``'ORFR 4'`` and the optional ``'Card A'`` to ``'Card F'``.  The contact types whose names
merely begin the same way --- ``_SMOOTH``, ``_MORTAR``, ``_TIEBREAK``, ``_TIED_WELD`` and
the rest --- have their own layouts and are preserved as ``Unknown``.

``*LOAD_BODY`` takes one mandatory option.  ``X``, ``Y``, ``Z`` (base acceleration) and
``RX``, ``RY``, ``RZ`` (angular velocity) store their data in ``'Card 1a.1'``; ``VECTOR``
adds the direction in ``'Card 1a.2'``; ``PARTS`` has only ``'Card 1b'``, the part set.
``*LOAD_BODY_GENERALIZED`` and ``*LOAD_BODY_POROUS`` are separate keywords and are
preserved as ``Unknown``.

Control and curves
------------------

===============================  ============================================
Keyword                          ``KeywordType``
===============================  ============================================
``*CONTROL_TERMINATION``         ``KeywordType.CONTROL_TERMINATION``
``*DEFINE_CURVE``                ``KeywordType.DEFINE_CURVE``
===============================  ============================================

``*DEFINE_CURVE`` accepts the ``3858`` and ``5434A`` options, which select an older
rediscretization algorithm without changing the layout.  Its point cards use twenty
character fields rather than the usual ten.  The many other keywords beginning
``*DEFINE_CURVE_`` --- ``_FUNCTION``, ``_TRIM``, ``_ENTITY`` and the rest --- are separate
keywords and are preserved as ``Unknown``.

Parameter references
--------------------

A card field holding an ``&VARNAME`` reference is stored as a
:class:`~dynakw.ParameterRef` rather than a number, so the reference survives a
read/write round trip.  See :doc:`getting_started` for how to read and set the
values behind those references.
