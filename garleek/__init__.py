#!/usr/bin/env python

"""
Garleek
"""

from collections import OrderedDict
from distutils.spawn import find_executable
from subprocess import check_output

tinker_analyze = find_executable('analyze')
tinker_testgrad = find_executable('testgrad')
tinker_testhess = find_executable('testhess')


#########################################################
#
# Generalities
#
#########################################################


def parse_atom_types(atom_types_filename):
    pass


#########################################################
#
# Gaussian
#
#########################################################


def parse_gaussian_EIn(ein_filename):
    """
    Parse the `*.EIn`file produced by Gaussian `external` keyword.

    This file contains the following data (taken from http://gaussian.com/external)

    n_atoms  derivatives-requested  charge  spin  
    atom_name  x  y  z  MM-charge [atom_type]
    atom_name  x  y  z  MM-charge [atom_type]
    atom_name  x  y  z  MM-charge [atom_type]

    ...

    `derivatives-requested` can be 0 (energy only), 1 (first derivatives)
    or 2 (second derivatives).
    """
    with open(ein_filename) as f:
        n_atoms, derivatives, charge, spin = map(int, next(f).split())
        atoms = OrderedDict()
        i, line = 1, next(f)
        while not line.strip().startswith('Connectivity'):
            fields = line.strip().split()
            atom_element = fields[0]
            atom_type = fields[5] if len(fields) == 6 else None
            x, y, z, mm_charge = map(float, fields[1:5])
            atoms[i] = {'element': atom_element, 
                        'type': atom_type, 
                        'xyz': (x, y, z),
                        'mm_charge': mm_charge}
            i, line = i+1, next(f)

        line = next(f) # Skip the "connectivity" header
        bonds = OrderedDict()
        while line.strip():
            fields = line.strip().split()
            bonds[int(fields[0])] = bond_list = []
            for to_atom, bond_index in zip(fields[1::2], fields[2::2]):
                bond_list.append((int(to_atom), float(bond_index)))
            line = next(f, '')

    return {'n_atoms': n_atoms,
            'derivatives': derivatives,
            'charge': charge,
            'spin': spin,
            'atoms': atoms,
            'bonds': bonds}


def prepare_gaussian_EOu(energy, dipole_moment, gradients=None, 
                         polarizability=None, hessian=None, force_constants=None):
    """
    Generate the `*.EOu` file Gaussian expects after `external` launch.

    After performing the MM calculations, Gaussian expects a file with the
    following information (all in atomic units; taken from 
    http://gaussian.com/external)

    Items                        Pseudo Code                            Line Format
    -------------------------------------------------------------------------------
    energy, dipole-moment (xyz)  E, Dip(I), I=1,3                       4D20.12
    gradient on atom (xyz)       FX(J,I), J=1,3; I=1,NAtoms             3D20.12
    polarizability               Polar(I), I=1,6                        3D20.12
    dipole derivatives           DDip(I), I=1,9*NAtoms                  3D20.12
    force constants              FFX(I), I=1,(3*NAtoms*(3*NAtoms+1))/2  3D20.12
    """
    pass


#########################################################
#
# Tinker
#
#########################################################


def prepare_tinker_xyz(atoms, bonds, atom_types=None):
    if atom_types is None:
        atom_types = {}
    out = [str(len(atoms))]
    for index, atom in atoms.iteritems():
        line = ([index, atom['element']] + 
                list(atom['xyz']) + 
                [atom_types.get(atom['type'], atom['type'])] +
                [bonded_to for (bonded_to, bond_index) in bonds[index]])
        out.append(' '.join(map(str, line)))
    return '\n'.join(out)


def _parse_tinker_analyze(data):
    pass


def _parse_tinker_testgrad(data):
    pass


def _parse_tinker_testhess(data):
    pass


def run_tinker(xyz, energy=True, dipole_moment=True, gradients=True, hessian=True):
    results = {}
    if energy or dipole_moment:
        args = ','.join(['E' if energy else '', 'M' if dipole_moment else ''])
        tinker_analyze_out = check_output([tinker_analyze, xyz, args])
        energy, dipole = _parse_tinker_analyze(tinker_analyze_out)
        results['energy'] = energy
        results['dipole_moment'] = dipole

    if gradients:
        tinker_testgrad_out = check_output([tinker_testgrad, xyz, 'y', 'n', '0.1D-04'])
        gradients = _parse_tinker_testgrad(tinker_testgrad_out)
        results['gradients'] = gradients

    if hessian:
        tinker_testhess_out = check_output([tinker_testhess, xyz, 'y', 'n '])
        hessian = _parse_tinker_testhess(tinker_testhess_out)
        results['hessian'] = hessian

    return results


#########################################################
#
# Entry points
#
#########################################################

def gaussian_tinker(ein_filename, atom_types=None):
    ein = parse_gaussian_EIn(ein_filename)
    if atom_types is not None:
        atom_types = parse_atom_types(atom_types)
    xyz = prepare_tinker_xyz(ein['atoms'], ein['bonds'], 
                             atom_types=atom_types)
    mm = run_tinker(xyz, energy=True, dipole_moment=True,
                    gradients=ein['derivatives'] > 1, 
                    hessian=ein['derivatives'] == 2)
    prepare_gaussian_EOu(**mm)
