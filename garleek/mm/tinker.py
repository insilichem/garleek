#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
mm.tinker.py
============

Garleek - Tinker bridge
"""

from __future__ import print_function, absolute_import, division
import os
import sys
import shutil
from distutils.spawn import find_executable
from subprocess import check_output
from tempfile import NamedTemporaryFile
import numpy as np
from  .. import units as u

supported_versions = '8', '8.1', 'qmcharges'
default_version = '8.1'

tinker_testhess = os.environ.get('TINKER_TESTHESS') or find_executable('testhess')
tinker_analyze = os.environ.get('TINKER_ANALYZE') or find_executable('analyze')
tinker_testgrad = os.environ.get('TINKER_TESTGRAD') or find_executable('testgrad')


def prepare_tinker_xyz(atoms, bonds=None, version=None):
    """
    Write a TINKER-style XYZ file. This is similar to a normal XYZ, but with more
    fields::

        atom_index element x y z type bonded_atom_1 bonded_order_1 ...

    TINKER expects coordinates in Angstrom.

    Parameters
    ----------
    atoms : OrderedDict
        Set of atoms to write, following convention defined in :mod:`garleek.qm`.
    bonds : OrderedDict
        Connectivity information, following convention defined in :mod:`garleek.qm`.
    version : str, optional=None
        Specific behavior flag, if needed. Like 'qmcharges'
    Returns
    -------
    xyzblock : str
        String with XYZ contents
    """
    out = [str(len(atoms))]
    for index, atom in atoms.items():
        if not bonds:
            atom_bonds = ''
        else:
            atom_bonds = ' '.join([str(bonded_to) for (bonded_to, bond_index) in bonds[index]
                                   if bond_index >= 0.5])
        line = '{index} E{element} {xyz[0]} {xyz[1]} {xyz[2]} {type} {bonds}'
        line = line.format(index=index, element=atom['element'], type=atom['type'],
                           xyz=atom['xyz'] * u.RBOHR_TO_ANGSTROM, bonds=atom_bonds)
        out.append(line)

    return '\n'.join(out)


def prepare_tinker_key(forcefield, atoms=None, version=None):
    """
    Prepare a file ready for TINKER's -k option.

    Parameters
    ----------
    forcefield : str
        ``forcefield`` should be either a:

        - ``*.prm``: proper forcefield file
        - ``*.key``, ``*.par``: key file that can call ``*.prm files`` and
        add more parameters

        If a .prm file is provided, a .key file will be written to
        accommodate the forcefield in a ``parameters *`` call.
    atoms : OrderedDict, optional=None
        Set of atoms to write, following convention defined in :mod:`garleek.qm`.
    version : str, optional=None
        Specific behavior flag. Supports:
        - ``qmcharges``, which would write charges provided by QM engine.
          Needs ``atoms`` to be passed.

    Returns
    -------
    path: str
        Absolute path to the generated TINKER .key file
    """
    if forcefield.lower().endswith('.prm'):
        with open('garleek.key', 'w') as f:
            print('parameters', os.path.abspath(forcefield), file=f)
        keypath = os.path.abspath('garleek.key')
    elif os.path.splitext(forcefield)[1].lower() in ('.par', '.key'):
        keypath = os.path.abspath(forcefield)
    else:
        raise ValueError('TINKER key file must be .prm, .key or .par')
    if version == 'qmcharges' and atoms:
        keypath_original = keypath
        keypath = os.path.splitext(keypath_original)[0] + '.charges.key'
        shutil.copyfile(keypath_original, keypath)
        with open(keypath, 'a') as f:
            print('', file=f)
            for index, atom in atoms.items():
                print('CHARGE', -1 * index, atom['charge'], file=f)
    return keypath

def _decode(data):
    try:
        return data.decode()
    except UnicodeDecodeError:
        return data.decode('utf-8', 'ignore')


def _parse_tinker_analyze(data):
    """
    Takes the output of TINKER's ``analyze`` program and obtain
    the potential energy (kcal/mole) and the dipole x, y, z
    components (debyes).
    """
    energy, dipole = None, None
    for line in _decode(data).splitlines():
        line = line.strip()
        if line.startswith('Total Potential Energy'):
            energy = float(line.split()[4])
        elif line.startswith('Dipole X,Y,Z-Components'):
            dipole = list(map(float, line.split()[3:6]))
            break
    return energy, np.array(dipole)


def _parse_tinker_testgrad(data):
    """

    """
    gradients = []
    lines = _decode(data).splitlines()
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('Cartesian Gradient Breakdown over Individual Atoms'):
            break

    for line in lines[i+4:]:
        line = line.strip()
        if not line or line.startswith('Total Gradient'):
            break
        fields = line.split()
        gradients.append(list(map(float, fields[2:5])))

    return np.array(gradients)


def _parse_tinker_testhess(hesfile, n_atoms):
    """

    """
    hessian = np.zeros((n_atoms * 3, n_atoms * 3))
    xyz_to_int = {'X': 0, 'Y': 1, 'Z': 2}
    with open(hesfile) as lines:
        for line in lines:
            line = line.strip()
            if not line:
                continue
            elif line.startswith('Diagonal'):
                _, line = next(lines), next(lines).strip()  # skip blank line
                block = []
                while line:
                    block.append(line)
                    line = next(lines).strip()
                nums = list(map(float, ' '.join(block).split()))
                for i, num in enumerate(nums):
                    hessian[i, i] = num
            elif line.startswith('Off-diagonal'):
                fields = line.split()
                atom_pos, axis_pos = int(fields[-2])-1, xyz_to_int[fields[-1]]
                _, line = next(lines), next(lines).strip()  # skip blank line
                block = []
                while line:
                    block.append(line)
                    try:
                        line = next(lines).strip()
                    except StopIteration:
                        break
                nums = list(map(float, ' '.join(block).split()))
                j = 3*atom_pos+axis_pos
                for i, num in enumerate(nums):
                    hessian[i+j+1, j] = num
    os.remove(hesfile)
    return hessian


def run_tinker(xyz_data, n_atoms, key, energy=True, dipole_moment=True,
               gradients=True, hessian=True):
    if not all([tinker_testhess, tinker_analyze, tinker_testgrad]):
        raise RuntimeError('TINKER executables could not be found in $PATH')

    error = 'Could not obtain {}! Command run:\n  {}\n\nTINKER output:\n{}'

    with NamedTemporaryFile(suffix='.xyz', delete=False, mode='w') as f_xyz:
        f_xyz.write(xyz_data)
        xyz = f_xyz.name

    results = {}
    if energy or dipole_moment:
        args = ','.join(['E' if energy else '', 'M' if dipole_moment else ''])
        command = [tinker_analyze, xyz, '-k', key, args]
        print('Running TINKER:', *command)
        output = check_output(command)
        energy, dipole = _parse_tinker_analyze(output)
        if energy is None:
            raise ValueError(error.format('energy', ' '.join(command), _decode(output)))
        results['energy'] = energy
        if dipole is None:
            raise ValueError(error.format('dipole', ' '.join(command), _decode(output)))
        results['dipole_moment'] = dipole

    if gradients:
        command = [tinker_testgrad, xyz, '-k', key,  'y', 'n', '0.1D-04']
        print('Running TINKER:', *command)
        output = check_output(command)
        gradients = _parse_tinker_testgrad(output)
        if gradients is None:
            raise ValueError(error.format('gradients', ' '.join(command), _decode(output)))
        results['gradients'] = gradients

    if hessian:
        command = [tinker_testhess, xyz, '-k', key, 'y', 'n']
        print('Running TINKER:', *command)
        output = check_output(command)
        hesfile = os.path.splitext(xyz)[0] + '.hes'
        hessian = _parse_tinker_testhess(hesfile, n_atoms)
        if hessian is None:
            raise ValueError(error.format('hessian', ' '.join(command), _decode(output)))
        results['hessian'] = hessian

    inactive_indices = []
    with open(key) as f:
        for line in f:
            if line.lower().startswith('inactive'):
                inactive_indices.extend([int(i) for i in line.split()[1:]])

    if inactive_indices:
        results = patch_tinker_output_for_inactive_atoms(results, inactive_indices, n_atoms)

    os.remove(xyz)
    return results


def patch_tinker_output_for_inactive_atoms(results, indices, n_atoms):
    """
    TODO: Patch 'hessian' to support FREQ calculations with inactive
    """
    values = results['gradients']
    shape = (n_atoms, 3)
    idx = np.array(indices) - 1
    filled = np.zeros(shape, dtype=values.dtype)
    mask = np.ones(shape[0], np.bool)
    mask[idx] = 0
    filled[mask] = values
    results['gradients'] = filled
    return results
