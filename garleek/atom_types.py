#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilities to deal with ``atom_types`` mappings.

These files are needed to convert atom types found in the QM
engine to those expected by the MM engine. This is a key part
of the whole QM/MM calculation, so those types must be chosen
wisely. While we provide a few default mappings (check
``BUILTIN_TYPES`` list), the user is encouraged to define
his or her own conversions if needed.

An ``atom_types`` file format is very simple: just two
columns of plain text, where the first field is the QM type
and the MM type is in the second field. ``garleek`` will just
replace the QM types with the corresponding MM type. If a QM type
is not found in the file, it will throw an error.

Comments can be inserted with a preceding ``#`` character, in its
own line or after any valid content (just like Python). Blank lines
are ignored as well.

This valid syntax:

::

    # atomic number, mm3 type, description

    1          5            # H_norm
    2          51           # He
    3          163          # Li
    4          165          # Be
    5          26           # B_sp2
    6          1            # C_sp3
    7          8            # N_sp3
    8          6            # O_sp3
"""

from __future__ import print_function, absolute_import, division
import os


BUILTIN_TYPES = sorted(os.listdir(os.path.join((os.path.dirname(__file__)), 'data', 'atom_types')))


def get_file(filename):
    if os.path.exists(filename):
        return filename
    datapath = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'atom_types', filename)
    if os.path.exists(datapath):
        return datapath
    raise ValueError('Atom types definitions `{}` could not be found'.format(filename))


def parse(atom_types_filename):
    d = {}
    with open(atom_types_filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            fields = line.split('#', 1)[0].split()
            d[fields[0]] = fields[1]
    return d
