#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
qm.gaussian.py
==============

Garleek - Gaussian bridge
"""

from __future__ import print_function, absolute_import, division
from collections import OrderedDict
import re
import sys
import numpy as np
from .. import __version__
from ..atom_types import ELEMENTS


supported_versions = '09a', '09b', '09c', '09d', '16'
default_version = '16'


class GaussianPatcher(object):

    def __init__(self, filename, atom_types, mm='tinker', qm='gaussian', forcefield=None, version=default_version):
        self.filename = filename
        self.atom_types = atom_types
        self.mm = mm
        self.qm = qm
        self.forcefield = forcefield
        self.version = version
        self.basis_patch = None

        self._external_rx = r'#.*oniom=?\(\w+\/([^\s:/]+):((external|amber|uff|dreiding)(=?("[^"]+"|\w+))?)(\/\S+)?\).*'
        self._opt_rx = r'#.*((opt\w*)=?\(?([^\s\)]+)?\)?).*'

    def _is_route(self, line):
        return line.startswith('#')

    def _patch_oniom_keyword(self, line):
        matches = re.search(self._external_rx, line, re.IGNORECASE)
        if not matches:
            return line
        basis_patch = matches.group(1)
        mm_basis = matches.group(6)
        if basis_patch and mm_basis is None:
            gen = '/gen' if basis_patch.lower() in ('gen', 'genecp') else '/' + basis_patch
            self.basis_patch = basis_patch.lower()
        command = 'garleek-backend --qm {} --mm {}'.format(self.qm, self.mm)
        if self.forcefield:
            command += " --ff '{}'".format(self.forcefield)
        return line.replace(matches.group(2), 'external="{}"{}'.format(command, gen))

    def _patch_opt_keyword(self, line):
        searches = re.search(self._opt_rx, line, re.IGNORECASE)
        if not searches:
            return line
        matches = searches.groups()
        opt_options = matches[2] or ''
        if 'nomicro' in opt_options.lower():  # already present, not needed
            return line
        print('Patching opt with nomicro...')
        opt_options = ','.join(['nomicro'] + (opt_options.split(',') if opt_options else []))
        return line.replace(matches[0], '{}({})'.format(matches[1], opt_options))

    def _patch_atom_type(self, line):
        """
        Atom types in Gaussian cannot contain the following characters:
        ``()=-``. Additionally, the type length is truncated to 8 chars in the
        resulting *.EIn file.However, sometimes a type definition is given
        after the charge::

            C-C-0.597300(PDBName=C,ResName=ILE,ResNum=2)
            O-O--0.567900(PDBName=O,ResName=ILE,ResNum=2)
            N-N--0.415700(PDBName=N,ResName=VAL,ResNum=3)
            H-H-0.271900(PDBName=H,ResName=VAL,ResNum=3)

        While that extra PDB* info is not reported in the *.EIn, we do use
        that for atom typing as well: if available, it will be used INSTEAD
        of the original atom type with this syntax: ``<ResName>_<PDBName>``.

        Numbers in PDBName will be IGNORED.
        """

        fields = line.split()
        atom_fields = fields[0].split('-')
        atom_matches = re.search(r'(\w+)-(\w+)?(--?[0-9.]*)?(\(([\w=,]*)\))?', fields[0])
        pdbinfo = atom_matches.group(5)
        if pdbinfo:
            pdb_dict = dict(map(str.upper, f.split('='))
                            for f in pdbinfo.split(','))
            atom_fields[1] = pdb_dict['RESNAME'] + '_' + pdb_dict['PDBNAME']
        # Atom types are always uppercased!
        atom_type = self.atom_types.get(atom_fields[1].upper())
        if atom_type is None:
            if pdbinfo:
                raise KeyError(atom_fields[1].upper())
            anumber = ELEMENTS.get(atom_fields[0].title(), atom_fields[0])
            print('Warning: Atom type', atom_fields[1], 'not found, using element', atom_fields[0].title(),
                  'with atomic number', anumber, 'as fallback')
            atom_type = self.atom_types[str(anumber)]
        atom_fields[1] = atom_type
        patched_atom = '-'.join(atom_fields)
        line = line.replace(fields[0], patched_atom, 1)
        if len(fields) > 6:
            link_atom = fields[6]
            link_atom_fields = link_atom.split('-')
            if pdbinfo:
                link_atom_fields[1] = pdb_dict['RESNAME'] + '_' + link_atom_fields[1]
            link_atom_fields[1] = self.atom_types[link_atom_fields[1]]
            patched_link_atom = '-'.join(link_atom_fields)
            line = line.replace(link_atom, patched_link_atom, 1)
        return line

    def patch(self):
        skipped_mult_charges = False
        blocks = [['! Created with Garleek v{}\n'.format(__version__)]]
        basis_index = []
        errors = []
        with open(self.filename) as f:
            for line in f:
                orig_line, line = line, line.strip()
                if line.startswith('!'):
                    continue
                elif not line:
                    blocks.append([])
                elif self._is_route(line):
                    orig_line = self._patch_oniom_keyword(orig_line)
                    orig_line = self._patch_opt_keyword(orig_line)
                elif line and len(blocks) == 3:
                    if skipped_mult_charges:
                        try:
                            orig_line = self._patch_atom_type(orig_line)
                        except Exception as e:
                            errors.append('{}: {} at line `{}`'.format(e.__class__.__name__, e, orig_line.rstrip()))
                    else:
                        skipped_mult_charges = True
                elif len(blocks) > 3 and line.strip() == '****' and len(blocks)-1 not in basis_index:
                    basis_index.append(len(blocks) - 1)
                blocks[-1].append(orig_line)

        if errors:
            print('! One or more errors were found. Patching will continue, but the calculation will probably fail')
            print(*errors, sep='\n')
        # patch basis set now
        if len(basis_index) == 1:
            idx = basis_index[0]
            if self.basis_patch == 'gen':
                print('Patching basis sets for MM...')
                blocks.insert(idx, blocks[idx])
                blocks.insert(idx, blocks[idx])
            elif self.basis_patch == 'genecp':
                print('Patching basis sets for MM...')
                blocks.insert(idx, blocks[idx])
                blocks.insert(idx+3, blocks[idx+1])

        return ''.join([l for b in blocks for l in b])


def patch_gaussian_input(*a, **kw):
    patcher = GaussianPatcher(*a, **kw)
    return patcher.patch()


def parse_gaussian_EIn(ein_filename, version=default_version):
    """
    Parse the ``*.EIn`` file produced by Gaussian ``external`` keyword.

    This file contains the following data (taken from http://gaussian.com/external)

    ::

        n_atoms  derivatives-requested  charge  spin
        atom_name  x  y  z  MM-charge [atom_type]
        atom_name  x  y  z  MM-charge [atom_type]
        atom_name  x  y  z  MM-charge [atom_type]
        ...

    - ``derivatives-requested`` can be ``0`` (energy only), ``1`` (first derivatives)
      or ``2`` (second derivatives).
    - ``version`` must be one of ``garleek.qm.gaussian.supported_versions``
    """
    with open(ein_filename) as f:
        n_atoms, derivatives, charge, spin = list(map(int, next(f).split()))
        atoms = OrderedDict()
        j = 0  # actual sequential index
        atom_map = {}  # maps original indices to new sequential indices
                       # only different if EmbedCharge == version
        for i in range(n_atoms):  # original atom index
            fields = next(f).strip().split()
            atom_element = fields[0]
            atom_type = fields[5] if len(fields) == 6 else None
            if atom_type.startswith('#'):
                continue
            x, y, z, charge = list(map(float, fields[1:5]))
            j += 1
            atoms[j] = {'element': atom_element,
                        'type': atom_type,
                        'xyz': np.array([x, y, z]),
                        'charge': charge}
            atom_map[i+1] = j

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
            frombondindex = int(fields[bond_index_pos])
            if frombondindex not in atom_map:
                line = next(f, '')
                continue
            bonds[atom_map[frombondindex]] = bond_list = []
            for to_atom, bond_order in zip(fields[bond_list_pos::2], fields[bond_list_pos+1::2]):
                to_atom_int = int(to_atom)
                if to_atom_int in atom_map:
                    bond_list.append((atom_map[to_atom_int], float(bond_order)))
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

    +-----------------------------+---------------------------------------+-------------+
    | Items                       | Pseudo Code                           | Line Format |
    +=============================+=======================================+=============+
    | energy, dipole-moment (xyz) | E, Dip(I), I=1,3                      |     4D20.12 |
    +-----------------------------+---------------------------------------+-------------+
    | gradient on atom (xyz)      | FX(J,I), J=1,3; I=1,NAtoms            |     3D20.12 |
    +-----------------------------+---------------------------------------+-------------+
    | polarizability              | Polar(I), I=1,6                       |     3D20.12 |
    +-----------------------------+---------------------------------------+-------------+
    | dipole derivatives          | DDip(I), I=1,9*NAtoms                 |     3D20.12 |
    +-----------------------------+---------------------------------------+-------------+
    | force constants             | FFX(I), I=1,(3*NAtoms*(3*NAtoms+1))/2 |     3D20.12 |
    +-----------------------------+---------------------------------------+-------------+

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
