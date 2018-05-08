#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
atom_types.py
=============

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

This is valid syntax:

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
ELEMENTS = {
    'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9,
    'Ne': 10, 'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17,
    'Ar': 18, 'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25,
    'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29, 'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33,
    'Se': 34, 'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40, 'Nb': 41,
    'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49,
    'Sn': 50, 'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57,
    'Ce': 58, 'Pr': 59, 'Nd': 60, 'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64, 'Tb': 65,
    'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70, 'Lu': 71, 'Hf': 72, 'Ta': 73,
    'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80, 'Tl': 81,
    'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86, 'Fr': 87, 'Ra': 88, 'Ac': 89,
    'Th': 90, 'Pa': 91, 'U': 92, 'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96, 'Bk': 97,
    'Cf': 98, 'Es': 99, 'Fm': 100, 'Md': 101, 'No': 102, 'Lr': 103, 'Rf': 104,
    'Db': 105, 'Sg': 106, 'Bh': 107, 'Hs': 108, 'Mt': 109, 'Ds': 110, 'Rg': 111,
    'Cn': 112, 'Nh': 113, 'Fl': 114, 'Mc': 115, 'Lv': 116, 'Ts': 117, 'Og': 118
}
PERIODIC_TABLE = dict((v, k) for (k, v) in ELEMENTS.items())


def get_file(filename):
    """
    Get file from one of the default locations
    """
    if os.path.exists(filename):
        return filename
    datapath = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'atom_types', filename)
    if os.path.exists(datapath):
        return datapath
    raise ValueError('Atom types definitions `{}` could not be found'.format(filename))


def parse(atom_types_filename):
    """
    Parse ``atom_types`` file
    """
    d = {}
    with open(atom_types_filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            fields = line.split('#', 1)[0].split()
            d[fields[0].upper()] = fields[1]
    return d

