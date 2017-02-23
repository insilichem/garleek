#!/usr/bin/env python

"""
Garleek
"""

import os
from collections import OrderedDict
from distutils.spawn import find_executable
from subprocess import check_output
from tempfile import NamedTemporaryFile
import numpy as np

# tinker_analyze = find_executable('analyze')
# tinker_testgrad = find_executable('testgrad')
# tinker_testhess = find_executable('testhess')

tinker_analyze = '/home/jrodriguez/dev/garleek/sictwo/oldsrc/analyze'
tinker_testgrad = '/home/jrodriguez/dev/garleek/sictwo/oldsrc/testgrad'
tinker_testhess = '/home/jrodriguez/dev/garleek/sictwo/oldsrc/testhess'

# xyz units conversion
RBOHR_TO_AMSTRONG = 0.52917720859

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


#########################################################
#
# Generalities
#
#########################################################


def parse_atom_types(atom_types_filename):
    d = {}
    with open(atom_types_filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue 
            fields = line.split('#', 1)[0].split()
            d[fields[0]] = fields[1]
    return d

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
            atoms[i] = {'element': 'E'+atom_element, 
                        'type': atom_type, 
                        'xyz': np.array([x, y, z]),
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


def prepare_gaussian_EOu(n_atoms, energy, dipole_moment, gradients=None, hessian=None,
                         polarizability=None, dipole_polarizability=None):
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
    lines = [[energy] + list(dipole_moment)]
    template = '{: 20.12E}'
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
    return '\n'.join([(template*len(line)).format(*line) for line in lines])


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
                (atom['xyz'] * RBOHR_TO_AMSTRONG).tolist() + 
                [atom_types.get(atom['type'], atom['type'])] +
                [bonded_to for (bonded_to, bond_index) in bonds[index]
                 if bond_index >= 0.5])
        out.append(' '.join(map(str, line)))
    return '\n'.join(out)


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
            dipole = map(float, line.split()[3:6])
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
        gradients.append(map(float, fields[2:5]))

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
                nums = map(float, ' '.join(block).split())
                for i, num in enumerate(nums):
                    hessian[i,i] = num
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
                nums = map(float, ' '.join(block).split())
                j = 3*atom_pos+axis_pos
                for i, num in enumerate(nums):
                    hessian[i+j+1, j] = num
    os.remove(hesfile)
    return hessian


def run_tinker(xyz_data, n_atoms, energy=True, dipole_moment=True,
               gradients=True, hessian=True, forcefield='mmff.prm'):
    error = 'Could not obtain {}! Command run:\n  {}\n\nTINKER output:\n{}'
    ff = os.path.join(os.path.dirname(tinker_analyze), forcefield)
    with NamedTemporaryFile(suffix='.xyz', delete=False) as f:
        f.write(xyz_data)
        xyz = f.name
    results = {}
    if energy or dipole_moment:
        args = ','.join(['E' if energy else '', 'M' if dipole_moment else ''])
        command = [tinker_analyze, xyz, ff, args]
        output = check_output(command)
        energy, dipole = _parse_tinker_analyze(output)
        if energy is None:
            raise ValueError(error.format('energy', ' '.join(command), output))
        results['energy'] = energy
        if dipole is None:
            raise ValueError(error.format('dipole', ' '.join(command), output))
        results['dipole_moment'] = dipole

    if gradients:
        output = check_output([tinker_testgrad, xyz, ff, 'y', 'n', '0.1D-04'])
        gradients = _parse_tinker_testgrad(output)
        if gradients is None:
            raise ValueError(error.format('gradients', ' '.join(command), output))
        results['gradients'] = gradients

    if hessian:
        output = check_output([tinker_testhess, xyz, ff, 'y', 'n'])
        hessian = _parse_tinker_testhess(output, n_atoms)
        if hessian is None:
            raise ValueError(error.format('hessian', ' '.join(command), output))
        results['hessian'] = hessian

    f.unlink(xyz)
    return results


#########################################################
#
# Entry points
#
#########################################################


def gaussian_tinker(ein_filename, atom_types=None, forcefield=None, write_file=True):   
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
                    gradients=with_gradients, hessian=with_hessian, forcefield=forcefield)
    # Unit conversion from Tinker to Gaussian
    mm['energy'] = mm['energy'] * KCALMOL_TO_HARTREE
    mm['dipole_moment'] = mm['dipole_moment'] * DEBYES_TO_EBOHR
    if with_gradients:
        mm['gradients'] = mm['gradients'] * KCALMOLEANGSTROM_TO_HARTREEBOHR
    if with_hessian:
        mm['hessian'] = mm['hessian'][np.tril_indices(15)] * KCALMOLEANGSTROMSQ_TO_HARTREEBOHRSQ
    # Generate files requested by Gaussian
    eou_data = prepare_gaussian_EOu(ein['n_atoms'], **mm)
    if write_file:
        eou_filename = os.path.splitext(ein_filename)[0] + '.EOu'
        with open(eou_filename, mode='w') as f:
            f.write(eou_data)
    return eou_data

