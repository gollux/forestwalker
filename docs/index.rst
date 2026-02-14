The Forest Walker
=================

Python modules for parsing JSON, TOML, YAML, and similar formats
produce simple tree structures composed of numbers, strings, Booleans,
arrays, and dictionaries. These structures are then parsed for the second
time to produce more Pythonic data structures. This usually involves
validation of some kind.

We firmly believe that parsing and validation should not be separate
steps: structure of data should have a single source of truth (doing 
otherwise opens door to security issues). Also, existing formal descriptions
of syntax (e.g., JSON schema) are too weak for many purposes and unwieldy
for others.

Enters the ``forestwalker``. A Python module that makes it easy to traverse
trees, parse values while checking types, and report invalid data with
their precise location in the tree.

Table of contents:

.. toctree::
   :maxdepth: 2

   self
   examples
   api
