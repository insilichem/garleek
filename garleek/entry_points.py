#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
import os
import shutil
import numpy as np
from .qm.gaussian import parse_gaussian_EIn, prepare_gaussian_EOu
from .mm.tinker import prepare_tinker_xyz, run_tinker, prepare_tinker_key
from .atom_types import parse as parse_atom_types
from . import units as u


def gaussian_tinker(qmargs, forcefield='mm3.prm', write_file=True, more_params=None):
    layer, ein_filename, eou_filename, msg_file, fchk_file, matel_file = qmargs[:6]
    # Gaussian Input
    ein = parse_gaussian_EIn(ein_filename)
    # TINKER inputs
    xyz = prepare_tinker_xyz(ein['atoms'], ein['bonds'])
    key = prepare_tinker_key(forcefield, additional=more_params)
    with_gradients = ein['derivatives'] > 0
    with_hessian = ein['derivatives'] == 2
    mm = run_tinker(xyz, n_atoms=ein['n_atoms'], energy=True, dipole_moment=True,
                    gradients=with_gradients, hessian=with_hessian, key=forcefield)
    # Unit conversion from Tinker to Gaussian
    mm['energy'] = mm['energy'] * u.KCALMOL_TO_HARTREE
    mm['dipole_moment'] = mm['dipole_moment'] * u.DEBYES_TO_EBOHR
    if with_gradients:
        mm['gradients'] = mm['gradients'] * u.KCALMOLEANGSTROM_TO_HARTREEBOHR
    if with_hessian:
        mm['hessian'] = mm['hessian'][np.tril_indices(ein['n_atoms']*3)] \
                        * u.KCALMOLEANGSTROMSQ_TO_HARTREEBOHRSQ
    # Generate files requested by Gaussian
    eou_data = prepare_gaussian_EOu(ein['n_atoms'], **mm)
    if write_file:
        if eou_filename is None:
            eou_filename = os.path.splitext(ein_filename)[0] + '.EOu'
        with open(eou_filename, mode='w') as f:
            f.write(eou_data)
    return eou_data
