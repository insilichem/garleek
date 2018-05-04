#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Garleek - Gaussian bridge
"""

from __future__ import print_function, absolute_import, division
from collections import OrderedDict
import re
import string
import numpy as np

supported_versions = '09a', '09b', '09c', '09d', '16'
default_version = '16'


def patch_gaussian_input(filename, atom_types, mm='tinker', qm='gaussian', forcefield=None):

    def _is_route(line):
        return line.startswith('#') and 'external=' in line.lower()

    def _patch_mm_keyword(line):
        command = 'garleek-backend --qm {} --mm {}'.format(qm, mm)
        if forcefield:
            command += " --ff '{}'".format(forcefield)
        return line.replace('garleek', '"{}"'.format(command))

    def _patch_atom_type(line):
        """
        Atom types in Gaussian cannot contain the following characters:
        ``()=-``. Additionally, the type length is truncated to 8 chars in the
        resulting *.EIn file.However, sometimes a type definition is given
        after the charge:

            C-C-0.597300(PDBName=C,ResName=ILE,ResNum=2)
            O-O--0.567900(PDBName=O,ResName=ILE,ResNum=2)
            N-N--0.415700(PDBName=N,ResName=VAL,ResNum=3)
            H-H-0.271900(PDBName=H,ResName=VAL,ResNum=3)

        While that extra PDB* info is not reported in the *.EIn, we do use
        that for atom typing as well: if available, it will be used INSTEAD
        of the original atom type with this syntax: ``<ResName>_<PDBName>``
        """

        fields = line.split()
        atom_fields = fields[0].split('-')
        atom_matches = re.search(r'(\w+)-(\w+)(--?[0-9.]*)?(\(([\w=,]*)\))?', fields[0])
        pdbinfo = atom_matches.group(5)
        if pdbinfo:
            pdb_dict = dict(map(string.upper, f.split('=')) for f in pdbinfo.split(','))
            atom_fields[1] = pdb_dict['RESNAME'] + '_' + atom_fields[1]
        atom_fields[1] = atom_types[atom_fields[1]]
        patched_atom = '-'.join(atom_fields)
        line = line.replace(fields[0], patched_atom, 1)
        if len(fields) > 6:
            link_atom = fields[6]
            link_atom_fields = link_atom.split('-')
            link_atom_fields[1] = atom_types[link_atom_fields[1]]
            patched_link_atom = '-'.join(link_atom_fields)
            line = line.replace(link_atom, patched_link_atom, 1)
        return line

    skipped_mult_charges = False
    section = 0
    lines = []
    with open(filename) as f:
        for line in f:
            orig_line, line = line, line.strip()
            if line.startswith('!'):
                pass
            elif not line:
                section += 1
            elif _is_route(line):
                orig_line = _patch_mm_keyword(orig_line)
            elif line and section == 2:
                if skipped_mult_charges:
                    orig_line = _patch_atom_type(orig_line)
                else:
                    skipped_mult_charges = True
            lines.append(orig_line)
    return ''.join(lines)


def parse_gaussian_EIn(ein_filename, version=default_version):
    """
    Parse the ``*.EIn``file produced by Gaussian ``external`` keyword.

    This file contains the following data (taken from http://gaussian.com/external)

    n_atoms  derivatives-requested  charge  spin
    atom_name  x  y  z  MM-charge [atom_type]
    atom_name  x  y  z  MM-charge [atom_type]
    atom_name  x  y  z  MM-charge [atom_type]

    ...

    ``derivatives-requested`` can be 0 (energy only), 1 (first derivatives)
    or 2 (second derivatives).

    ``version`` must be one of ``garleek.qm.gaussian.supported_versions``
    """
    with open(ein_filename) as f:
        n_atoms, derivatives, charge, spin = list(map(int, next(f).split()))
        atoms = OrderedDict()
        for i in range(n_atoms):
            fields = next(f).strip().split()
            atom_element = fields[0]
            atom_type = fields[5] if len(fields) == 6 else None
            x, y, z, mm_charge = list(map(float, fields[1:5]))
            atoms[i+1] = {'element': atom_element,
                          'type': atom_type,
                          'xyz': np.array([x, y, z]),
                          'mm_charge': mm_charge}

        line = next(f)  # Skip the "connectivity" header
        has_bonds = False
        if 'connectivity' in line.strip().lower():
            line = next(f)
            has_bonds = True
        bonds = OrderedDict()
        if version in ('09d', '16'):
            bond_index_pos = 0
            bond_list_pos = 1
        elif version in ('03', '09a', '09b', '09c'):
            bond_index_pos = 1
            bond_list_pos = 6
        else:
            raise ValueError('`version` must be one of {}'.format(', '.join(supported_versions)))
        while line.strip():
            fields = line.strip().split()
            bonds[int(fields[bond_index_pos])] = bond_list = []
            for to_atom, bond_index in zip(fields[bond_list_pos::2], fields[bond_list_pos+1::2]):
                bond_list.append((int(to_atom), float(bond_index)))
            line = next(f, '')

    return {'n_atoms': n_atoms,
            'derivatives': derivatives,
            'charge': charge,
            'spin': spin,
            'atoms': atoms,
            'bonds': bonds}


def prepare_gaussian_EOu(n_atoms, energy, dipole_moment, gradients=None, hessian=None,
                         polarizability=None, dipole_polarizability=None):
    """
    Generate the ``*.EOu`` file Gaussian expects after ``external`` launch.

    After performing the MM calculations, Gaussian expects a file with the
    following information (all in atomic units; taken from
    http://gaussian.com/external)

    Items                        Pseudo Code                            Line Format
    -------------------------------------------------------------------------------
    energy, dipole-moment (xyz)  E, Dip(I), I=1,3                           4D20.12
    gradient on atom (xyz)       FX(J,I), J=1,3; I=1,NAtoms                 3D20.12
    polarizability               Polar(I), I=1,6                            3D20.12
    dipole derivatives           DDip(I), I=1,9*NAtoms                      3D20.12
    force constants              FFX(I), I=1,(3*NAtoms*(3*NAtoms+1))/2      3D20.12

    The second section is present only if first derivatives or frequencies were
    requested, and the final section is present only if frequencies were requested.
    In the latter case, the Hessian is given in lower triangular form: αij, i=1 to
    N, j=1 to i. The dipole moment, polarizability, and dipole derivatives can be
    zero if none are available.
    """
    lines = [[energy] + list(dipole_moment)]
    template = '{: 20.12e}'
    if gradients is not None:
        for gradient in gradients:
            lines.append(gradient)
    if hessian is not None:
        if polarizability is None:
            polarizability = np.zeros(6)
        if dipole_polarizability is None:
            dipole_polarizability = np.zeros(9*n_atoms)
        for i in range(0, polarizability.size, 3):
            lines.append(polarizability[i:i+3])
        for i in range(0, dipole_polarizability.size, 3):
            lines.append(dipole_polarizability[i:i+3])

        for i in range(0, hessian.size, 3):
            lines.append(hessian[i:i+3])
    lines.append([])  # Gaussian is very peculiar about blank lines
    return '\n'.join([(template*len(line)).format(*line) for line in lines])
