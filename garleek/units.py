#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Conversion factors are listed here

The convention is to import this module when needed, using ``u`` as an alias:

    >>> from garleek import units as u
"""

from __future__ import print_function, absolute_import, division


# XYZ units conversion
RBOHR_TO_ANGSTROM = 0.52917720859
ANGSTROM_TO_RBOHR = 1/RBOHR_TO_ANGSTROM

# Energy units conversion
HARTREE_TO_KCALMOL = 627.509391
KCALMOL_TO_HARTREE = 1/HARTREE_TO_KCALMOL

# Gradients units conversion
HARTREEBOHR_TO_KCALMOLEANGSTROM = 1185.820894904
KCALMOLEANGSTROM_TO_HARTREEBOHR = 1/HARTREEBOHR_TO_KCALMOLEANGSTROM

# Hessian units conversion
HARTREEBOHRSQ_TO_KCALMOLEANGSTROMSQ = 2240.876733833
KCALMOLEANGSTROMSQ_TO_HARTREEBOHRSQ = 1/HARTREEBOHRSQ_TO_KCALMOLEANGSTROMSQ

# Dipole units conversion
DEBYES_TO_EBOHR = 0.393430307
EBOHR_TO_DEBYES = 1/DEBYES_TO_EBOHR
