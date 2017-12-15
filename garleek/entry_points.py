#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
from .qm.gaussian import parse_gaussian_EIn, prepare_gaussian_EOu
from .mm.tinker import prepare_tinker_xyz, run_tinker
from .atom_types import parse_atom_types
from .units import *


def gaussian_tinker(ein_filename, eou_filename=None, atom_types=None,
                    forcefield=None, write_file=True):
    # Defaults
    if atom_types is not None:
        atom_types = parse_atom_types(atom_types)
    if forcefield is None:
        forcefield = 'mmff.prm'
    # Gaussian Input
    ein = parse_gaussian_EIn(ein_filename)
    # TINKER inputs
    xyz = prepare_tinker_xyz(ein['atoms'], ein['bonds'], atom_types=atom_types)
    with_gradients = ein['derivatives'] > 0
    with_hessian = ein['derivatives'] == 2
    mm = run_tinker(xyz, n_atoms=ein['n_atoms'], energy=True, dipole_moment=True,
                    gradients=with_gradients, hessian=with_hessian)
    # Unit conversion from Tinker to Gaussian
    mm['energy'] = mm['energy'] * KCALMOL_TO_HARTREE
    mm['dipole_moment'] = mm['dipole_moment'] * DEBYES_TO_EBOHR
    if with_gradients:
        mm['gradients'] = mm['gradients'] * KCALMOLEANGSTROM_TO_HARTREEBOHR
    if with_hessian:
        mm['hessian'] = mm['hessian'][np.tril_indices(ein['n_atoms']*3)] \
                        * KCALMOLEANGSTROMSQ_TO_HARTREEBOHRSQ
    # Generate files requested by Gaussian
    eou_data = prepare_gaussian_EOu(ein['n_atoms'], **mm)
    if write_file:
        if eou_filename is None:
            eou_filename = os.path.splitext(ein_filename)[0] + '.EOu'
        with open(eou_filename, mode='w') as f:
            f.write(eou_data)
    return eou_data
