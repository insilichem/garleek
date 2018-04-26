#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Garleek - Tinker bridge
"""

from __future__ import print_function, division
import os
from distutils.spawn import find_executable
from subprocess import check_output
from tempfile import NamedTemporaryFile
import numpy as np
from ..units import *


tinker_testhess = find_executable('testhess')
tinker_analyze = find_executable('analyze')
tinker_testgrad = find_executable('testgrad')


def prepare_tinker_input(atoms, bonds, forcefield=None):
    xyz = prepare_tinker_xyz(atoms, bonds)
    inpkey = prepare_tinker_inpkey(forcefield, atoms)
    return xyz, inpkey


def prepare_tinker_xyz(atoms, bonds):
    out = [str(len(atoms))]
    for index, atom in atoms.items():
        line = ([index, atom['element']] +
                (atom['xyz'] * RBOHR_TO_ANGSTROM).tolist() +
                [atom['type']] +
                [bonded_to for (bonded_to, bond_index) in bonds[index]
                 if bond_index >= 0.5])
        out.append(' '.join(map(str, line)))

    return '\n'.join(out)


def prepare_tinker_inpkey(forcefield, atoms):
    if 'inp.key' in os.listdir('.'):
        return ''
    return ''


def _parse_tinker_analyze(data):
    """
    Takes the output of TINKER's `analyze` program and obtain
    the potential energy (kcal/mole) and the dipole x, y, z
    components (debyes).
    """
    energy, dipole = None, None
    lines = data.splitlines()
    for line in lines:
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
               gradients=True, hessian=True, params_fn='mm3.prm'):
    error = 'Could not obtain {}! Command run:\n  {}\n\nTINKER output:\n{}'

    with NamedTemporaryFile(suffix='.xyz', delete=False, mode='w') as f_xyz:
        f_xyz.write(xyz_data)
        xyz = f_xyz.name

    results = {}
    if energy or dipole_moment:
        args = ','.join(['E' if energy else '', 'M' if dipole_moment else ''])
        command = [tinker_analyze, xyz, params_fn, args]
        output = check_output(command).decode("utf-8")
        energy, dipole = _parse_tinker_analyze(output)
        if energy is None:
            raise ValueError(error.format('energy', ' '.join(command), output))
        results['energy'] = energy
        if dipole is None:
            raise ValueError(error.format('dipole', ' '.join(command), output))
        results['dipole_moment'] = dipole

    if gradients:
        output = check_output([tinker_testgrad, xyz, params_fn,  'y', 'n', '0.1D-04']).decode("utf-8")
        gradients = _parse_tinker_testgrad(output)
        if gradients is None:
            raise ValueError(error.format('gradients', ' '.join(command), output))
        results['gradients'] = gradients

    if hessian:
        output = check_output([tinker_testhess, xyz, params_fn, 'y', 'n']).decode("utf-8")
        hessian = _parse_tinker_testhess(output, n_atoms)
        if hessian is None:
            raise ValueError(error.format('hessian', ' '.join(command), output))
        results['hessian'] = hessian

    os.remove(xyz)
    return results
