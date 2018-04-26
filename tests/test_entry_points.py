#!/usr/bin/env python

from __future__ import print_function, division, absolute_import
import os
import sys
import shutil
import re
import pytest
import cclib
from contextlib import contextmanager
from tempfile import mkdtemp
from subprocess import call
import numpy as np

from garleek.cli import frontend_app as frontend_garleek, _extant_file_types, _extant_file_prm
here = os.path.abspath(os.path.dirname(__file__))
data = os.path.join(here, 'data')
gaussian_exe = os.environ.get('g16') or os.environ.get('g09') or 'g16'


def isclose(a, b, rel_tol=1e-06, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def oniom_energy(path):
    energy = None
    with open(path) as f:
        for line in f:
            if 'extrapolated' in line:
                energy = float(line.split()[-1])
    return energy


@contextmanager
def temporary_directory(enter=True, **kwargs):
    """Create and enter a temporary directory; used as context manager."""
    temp_dir = mkdtemp(**kwargs)
    if enter:
        cwd = os.getcwd()
        os.chdir(temp_dir)
    yield temp_dir
    if enter:
        os.chdir(cwd)
    shutil.rmtree(temp_dir)


@pytest.mark.parametrize("directory", sorted(next(os.walk(data))[1]))
def test_gaussian_tinker(directory):
    if directory.endswith('UFF'):
        pytest.skip()

    with temporary_directory() as tmp:
        infilename = directory + '.in'
        indir = os.path.join(data, directory)
        indircopy = os.path.join(tmp, directory)
        infilecopy = os.path.join(tmp, directory, infilename)
        shutil.copytree(indir, indircopy)
        # guess forcefield from inp.key
        ff = 'mm3.prm'
        with open(os.path.join(indircopy, 'atom.types')) as f:
            for line in f:
                if line.startswith('# forcefield:'):
                    ff = line.split(':', 1)[1].strip()
        # patch inputfile
        garleek_in = frontend_garleek(infilecopy,  qm='gaussian', mm='tinker',
                                              ff=_extant_file_prm(ff), 
                                              types=os.path.join(indircopy, 'atom.types'))
        
        call([gaussian_exe, garleek_in])

        garleek_out = os.path.splitext(garleek_in)[0] + '.log'
        original_out = os.path.join(indir, directory + '.out')
        assert os.path.isfile(garleek_out)
        cc_original = cclib.ccopen(original_out).parse()
        cc_calculated = cclib.ccopen(garleek_out).parse()
        assert isclose(cc_original.scfenergies[-1], cc_calculated.scfenergies[-1])
        assert np.sqrt(np.mean(np.square(cc_original.atomcoords[-1]-cc_calculated.atomcoords[-1]))) < 0.001
        assert isclose(oniom_energy(original_out), oniom_energy(garleek_out))
