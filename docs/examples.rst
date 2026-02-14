Examples
========

==============
Object parsing
==============

The following code parses a simple JSON object (dictionary)
with two attributes: ``name`` is mandatory, while ``height``
defaults to 100 if missing. The context manager makes sure
that the object contains only keys referenced by the parser.

.. literalinclude:: example1.py
