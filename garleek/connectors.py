#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
connectors.py
=============

This module hosts high-level functions that *connect* different
engines together, handling input/output files delivery and
unit conversion.

A ``CONNECTORS`` dict is maintained at the end of the file
listing the connectors available. It's a dict of dicts, where
the primary keys are QM engines and secondary keys, MM engines.
"""

from __future__ import print_function, absolute_import, division
import os
import shutil
import numpy as np
from .qm.gaussian import (parse_gaussian_EIn, prepare_gaussian_EOu,
                          supported_versions as gaussian_supported_versions,
                          default_version as gaussian_default_version,
                          patch_gaussian_input)
from .mm.tinker import prepare_tinker_xyz, run_tinker, prepare_tinker_key
from .atom_types import parse as parse_atom_types
from . import units as u


def gaussian_tinker(qmargs, forcefield='mm3.prm', write_file=True, qm_version='16',
                    mm_version=None, **kwargs):
    """
    Connects QM engine ``gaussian`` with MM engine ``tinker``.

    When Gaussian does an ONIOM calculation with Garleek, the MM part
    is configured with the ``external`` keyword, meaning that Gaussian
    will write a series of files to disk and call the requested program.
    Gaussian expects some data written back to an ``*.EOu`` file, which should
    contain potential energy, dipole moment, polarizability and/or hessian
    matrix, depending on the calculation. The called program is expected
    to take those input files, convert them to the format expected by
    the MM program, obtaint the needed data and write them to the EOu file
    with the adequate syntax. So, that's what we are doing here:

        1. Parse Gaussian EIn file
        2. Convert it to TINKER's XYZ and KEY files
        3. Run TINKER to obtain energy, dipole, etc
        4. Convert units and write the EOu file

    Parameters
    ----------
    qmargs : tuple
        CLI arguments passed by Gaussian. Depending on the version,
        its length can vary, but we only care about qmargs[1], so
        it's not usually a problem

    forcefield : str, optional=mm3.prm
        Path to file listing the TINKER forcefield to use. It can be a ``*.prm``
        file or a ``*.key`` file. PRM files are full forcefields with no modifications.
        KEY files can import PRM files with ``parameters`` and then list custom
        parameters below.

    write_file : bool, optional=True
        Wether to write the resulting EOu file to disk.

    qm_version : string, optional=16
        Gaussian version in use. Needed to cover the slight differences
        between Gaussian versions (EIn/EOu syntax, number of args, and so on).

    mm_version : string, optional=None
        TINKER behavior. If QM-charges must be considered for the MM
        part, set it to 'qmcharges'

    Returns
    -------
    eou_data : str
        Contents of the EOu file Gaussian expects back.
    """
    if qm_version is None:
        qm_version = gaussian_default_version
    layer, ein_filename, eou_filename  = qmargs[:3]
    # In Gaussian 09d and above, two more arguments are passed
    # but we don't need them anyway
    # msg_file, fchk_file, matel_file = qmargs[3:6]
    # Gaussian Input
    ein = parse_gaussian_EIn(ein_filename, version=qm_version)
    # TINKER inputs
    xyz = prepare_tinker_xyz(ein['atoms'], ein['bonds'], version=mm_version)
    key = prepare_tinker_key(forcefield, atoms=ein['atoms'], version=mm_version)
    with_gradients = ein['derivatives'] > 0
    with_hessian = ein['derivatives'] == 2
    mm = run_tinker(xyz, n_atoms=ein['n_atoms'], key=key, energy=True, dipole_moment=True,
                    gradients=with_gradients, hessian=with_hessian)
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


CONNECTORS = {
    'gaussian': {
        'tinker': gaussian_tinker
    }
}
QM_ENGINES = sorted(CONNECTORS.keys())
MM_ENGINES = sorted([k for (qm, mm) in CONNECTORS.items() for k in mm])
PATCHERS = {
    'gaussian': patch_gaussian_input
}