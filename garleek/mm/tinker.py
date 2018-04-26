#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Garleek - Tinker bridge
"""

from __future__ import print_function, absolute_import, division
import os
import sys
from distutils.spawn import find_executable
from subprocess import check_output
from tempfile import NamedTemporaryFile
import numpy as np
from  .. import units as u


tinker_testhess = os.environ.get('TINKER_TESTHESS') or find_executable('testhess')
tinker_analyze = os.environ.get('TINKER_ANALYZE') or find_executable('analyze')
tinker_testgrad = os.environ.get('TINKER_TESTGRAD') or find_executable('testgrad')


if not all([tinker_testhess, tinker_analyze, tinker_testgrad]):
    sys.exit('TINKER executables could not be found in $PATH')


def prepare_tinker_input(atoms, bonds, forcefield=None):
    xyz = prepare_tinker_xyz(atoms, bonds)
    inpkey = prepare_tinker_key(forcefield)
    return xyz, inpkey


def prepare_tinker_xyz(atoms, bonds):
    out = [str(len(atoms))]
    for index, atom in atoms.items():
        line = ([index, atom['element']] +
                (atom['xyz'] * u.RBOHR_TO_ANGSTROM).tolist() +
                [atom['type']] +
                [bonded_to for (bonded_to, bond_index) in bonds[index]
                 if bond_index >= 0.5])
        out.append(' '.join(map(str, line)))

    return '\n'.join(out)


def prepare_tinker_key(forcefield, additional=None):
    with open('garleek.key', 'w') as f:
        print('parameters ', forcefield, file=f)
        if additional is not None:
            if os.path.isfile(additional):
                with open(additional) as g:
                    additional = g.read()
            f.write(additional)
    return os.path.abspath('garleek.key')


def _parse_tinker_analyze(data):
    """
    Takes the output of TINKER's `analyze` program and obtain
    the potential energy (kcal/mole) and the dipole x, y, z
    components (debyes).
    """
    energy, dipole = None, None
    for line in data.splitlines():
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
    lines = data.splitlines()
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


def _parse_tinker_testhess(data, n_atoms):
    """

    """
    hesfile = data.splitlines()[-1].split(':')[-1].strip()
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


def run_tinker(xyz_data, n_atoms, energy=True, dipole_moment=True,
               gradients=True, hessian=True, key='mm3.prm'):
    error = 'Could not obtain {}! Command run:\n  {}\n\nTINKER output:\n{}'

    with NamedTemporaryFile(suffix='.xyz', delete=False, mode='w') as f_xyz:
        f_xyz.write(xyz_data)
        xyz = f_xyz.name

    results = {}
    if energy or dipole_moment:
        args = ','.join(['E' if energy else '', 'M' if dipole_moment else ''])
        command = [tinker_analyze, xyz, '-k', key, args]
        output = check_output(command).decode("utf-8")
        energy, dipole = _parse_tinker_analyze(output)
        if energy is None:
            raise ValueError(error.format('energy', ' '.join(command), output))
        results['energy'] = energy
        if dipole is None:
            raise ValueError(error.format('dipole', ' '.join(command), output))
        results['dipole_moment'] = dipole

    if gradients:
        output = check_output([tinker_testgrad, xyz, '-k', key,  'y', 'n', '0.1D-04']).decode("utf-8")
        gradients = _parse_tinker_testgrad(output)
        if gradients is None:
            raise ValueError(error.format('gradients', ' '.join(command), output))
        results['gradients'] = gradients

    if hessian:
        output = check_output([tinker_testhess, xyz, '-k', key, 'y', 'n']).decode("utf-8")
        hessian = _parse_tinker_testhess(output, n_atoms)
        if hessian is None:
            raise ValueError(error.format('hessian', ' '.join(command), output))
        results['hessian'] = hessian

    os.remove(xyz)
    return results
