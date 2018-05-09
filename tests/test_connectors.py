#!/usr/bin/env python

from __future__ import print_function, division, absolute_import
import os
import sys
import shutil
import re
from contextlib import contextmanager
from distutils.spawn import find_executable
from tempfile import mkdtemp
from subprocess import call
import pytest
import numpy as np
try:
    import cclib
    HAS_CCLIB = True
except ImportError:
    HAS_CCLIB = False

from garleek.cli import frontend_app as frontend_garleek, _extant_file_types, _extant_file_prm

here = os.path.abspath(os.path.dirname(__file__))
data = os.path.join(here, 'data')
WORKING_DIR = os.getcwd()

gaussian_exe = find_executable('g16') or find_executable('g09')  or 'g16'
if 'g09a' in gaussian_exe:
    gaussian_version = '09a'
elif 'g09b' in gaussian_exe:
    gaussian_version = '09b'
elif 'g09c' in gaussian_exe:
    gaussian_version = '09c'
elif 'g09d' in gaussian_exe:
    gaussian_version = '09d'
elif 'g09' in gaussian_exe:
    gaussian_version = '09d'
else:
    gaussian_version = '16'


def isclose(a, b, rel_tol=1e-06, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def oniom_energy(path):
    energy = None
    with open(path) as f:
        for line in f:
            if 'extrapolated' in line:
                energy = float(line.split()[-1])
    return energy


def no_errors(path):
    with open(path) as f:
        for line in f:
            if 'Failed to open output file from external program' in line:
                return False
    return True


@contextmanager
def temporary_directory(enter=True, remove=True, **kwargs):
    """Create and enter a temporary directory; used as context manager."""
    temp_dir = mkdtemp(prefix='garleek', **kwargs)
    if enter:
        cwd = os.getcwd()
        os.chdir(temp_dir)
    yield temp_dir
    if enter:
        os.chdir(cwd)
    if remove:
        shutil.rmtree(temp_dir)


@pytest.mark.parametrize("directory", sorted(next(os.walk(data))[1]))
def test_gaussian_tinker(directory):
    if directory.endswith('UFF'):
        pytest.skip()
    with temporary_directory() as tmp:
        # Original data
        data_original = os.path.join(data, directory)
        outfile_original = os.path.join(data_original, directory + '.out')
        infile_original = os.path.join(data_original, directory + '.in')
        # Copied tmp paths
        data_copy = os.path.join(tmp, directory)
        infile_copy = os.path.join(data_copy, directory + '.in')
        shutil.copytree(data_original, data_copy)
        os.chdir(data_copy)
        # We are now in /tmp/garleek*****/A_1 or similar, which
        # contains copies of the original Gaussian files and types
        # guess forcefield specified in atom.types
        ff = 'qmmm3.prm'
        types = 'uff_to_mm3'
        if os.path.isfile(directory + '.key'):
            ff = directory + '.key'
        elif os.path.isfile('atom.types'):
            types = 'atom.types'
            with open(types) as f:
                for line in f:
                    if line.startswith('# forcefield:'):
                        ff = line.split(':', 1)[1].strip()
        # patch inputfile
        garleek_in = frontend_garleek(infile_copy, qm='gaussian_'+gaussian_version, mm='tinker', ff=ff, types=types)

        call([gaussian_exe, garleek_in])
        garleek_out = os.path.splitext(garleek_in)[0] + '.log'

        # Save output in working dir
        if not os.path.exists(os.path.join(WORKING_DIR, 'outputs-'+gaussian_version)):
            os.mkdir(os.path.join(WORKING_DIR, 'outputs-'+gaussian_version))
        shutil.copy(garleek_in, os.path.join(WORKING_DIR, 'outputs-'+gaussian_version, os.path.basename(garleek_in)))
        assert os.path.isfile(garleek_out)
        shutil.copy(garleek_out, os.path.join(WORKING_DIR, 'outputs-'+gaussian_version, os.path.basename(garleek_out)))
        assert no_errors(garleek_out)
        # Check values
        assert isclose(oniom_energy(outfile_original), oniom_energy(garleek_out))
        if HAS_CCLIB:
            cc_original = cclib.ccopen(outfile_original).parse()
            cc_calculated = cclib.ccopen(garleek_out).parse()
            assert isclose(cc_original.scfenergies[-1], cc_calculated.scfenergies[-1])
            assert np.sqrt(np.mean(np.square(cc_original.atomcoords[-1]-cc_calculated.atomcoords[-1]))) < 0.001
