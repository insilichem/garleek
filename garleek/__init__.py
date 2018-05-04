"""
Garleek
=======

QM/MM interfacing in Python.

User documentation such as installation and usage can be found
in the ``../docs/`` directory. The following is intended for
developers only.

Code structure
--------------

Library layer
.............

- ``qm`` and``mm`` subpackages host low-level QM and MM
software interfacing. Both feature a documented, standardized
dictionary representation on the data each are expecting. The
communication logic for each ``qm`` and ``mm`` modules is
performed in the ``connectors`` module. Refer to each module
documentation for more information.

- ``atom_types`` controls ``atom_type`` file parsing, and
``units`` stores unit conversion factors.

Application layer
.................

- ``cli`` module lists the CLI entry-points for users (frontend)
  and QM softwares handling the ONIOM calculation (backend)
"""

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
__author__ = "Jaime Rodriguez-Guerra & Ignacio Funes-Ardoiz"
