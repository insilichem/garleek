#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module contains the command-line interfaces for both
``garleek`` (the user-friendly patcher) and ``garleek-backend``
(the program the QM engine calls behind the scenes to handle
the MM calculations).

``garleek`` takes a naive QM input file for ONIOM and patches it so
the MM part is performed through ``garleek-backend``, which will be
interfacing with the configured MM engine. For this to work, the
atom types featured in the QM input file should be understandable
by the MM engine, so ``garleek`` will replace those too, using the
``atom_types`` file mapping to do so.

In general, the worfklow is the following:

1. Build a standard ONIOM calculation, with layers, link atoms and
   so on. The ``garleek`` keyword should be present in the MM layer
   configuration so the patcher can find it and properly configure it.
2. Patch the QM input file with ``garleek``:

    garleek --qm <QM_engine> -mm <MM_engine> --ff <MM_forcefield>
    --types <QM/MM_atom_type_dictionary> QM_input_file.in

3. Submit the calculation with the resulting patched file, named
   ``QM_input_file.garleek.in`` with the desired QM software:

    QM_engine QM_input_file.garleek.in

4. Profit!
"""
from __future__ import print_function, absolute_import, division
from argparse import ArgumentParser, REMAINDER, SUPPRESS, ArgumentTypeError
import os
import sys
from . import __version__
from .connectors import CONNECTORS, PATCHERS
from .atom_types import get_file, parse as parse_atom_types, BUILTIN_TYPES


###
# VALIDATORS
###

_here = os.path.dirname(os.path.abspath(__file__))


def _extant_file(path):
    if os.path.isfile(path):
        return os.path.abspath(path)
    raise ArgumentTypeError("File `{}` cannot be found".format(path))


def _extant_file_prm(path):
    if os.path.isfile(path):
        return os.path.abspath(path)
    indatapath = os.path.join(_here, 'data', 'prm', path)
    if os.path.isfile(indatapath):
        return indatapath
    if os.path.isfile(indatapath + '.prm'):
        return indatapath + '.prm'
    raise ArgumentTypeError("File `{}` cannot be found".format(path))


def _extant_file_types(path):
    if os.path.isfile(path):
        return os.path.abspath(path)
    indatapath = os.path.join(_here, 'data', 'atom_types', path)
    if os.path.isfile(indatapath):
        return indatapath
    raise ArgumentTypeError("File `{}` cannot be found".format(path))


def _parse_engine_string(word):
    parts = word.split('_', 1)
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[1]

###
# BACKEND
###


def backend_app_main(argv=None):
    """ ``garleek-backend`` CLI entry-point """
    msg = 'Entering Garleek v{}'.format(__version__)
    underline = '='*len(msg)
    print(underline)
    print(msg)
    print(underline)
    args = _backend_args(argv)
    backend_app(**vars(args))
    print(underline)
    print('Exiting Garleek'.center(len(msg)))
    print(underline)


def backend_app(qmargs, qm='gaussian', mm='tinker', ff=_extant_file_prm('mm3.prm'), **kw):
    """ ``garleek-backend`` Python entry-point """
    qm_engine, qm_version = _parse_engine_string(qm)
    mm_engine, mm_version = _parse_engine_string(mm)
    try:
        connector = CONNECTORS[qm_engine][mm_engine]
    except KeyError:
        sys.exit("ERROR: Connector with QM={} and MM={} "
                 "is not available".format(qm_engine, qm_engine))
    connector(qmargs, forcefield=ff, qm_version=qm_version, mm_version=mm_version)


def _backend_args(argv=None):
    p = ArgumentParser()
    p.add_argument('--qm', type=str, default='gaussian',
                   help='QM program calling Garleek. Defaults to Gaussian. '
                        'Versions after an underscore: <engine>_<version>, '
                        'like gaussian_16')
    p.add_argument('--mm', type=str, default='tinker',
                   help='MM engine to use. Defaults to Tinker. '
                        'Versions after an underscore: <engine>_<version>, '
                        'like tinker_8')
    p.add_argument('--ff', type=_extant_file_prm, default='mmff.prm',
                   help='Forcefield to be used by the MM engine')
    # Arguments injected by the QM program
    p.add_argument('qmargs', nargs=REMAINDER, help=SUPPRESS)

    return p.parse_args(argv)


###
# FRONTEND
###


def frontend_app_main(argv=None):
    """ ``garleek`` CLI entry-point """
    args = _frontend_args(argv)
    frontend_app(**vars(args))


def frontend_app(input_file, types='uff_to_mm3', qm='gaussian', mm='tinker',
                 ff=_extant_file_prm('mm3.prm'), **kw):
    """ ``garleek`` Python entry-point """
    qm_engine, qm_version = _parse_engine_string(qm)
    rosetta = parse_atom_types(get_file(types))
    patcher = PATCHERS[qm_engine]
    patched = patcher(input_file, rosetta, qm=qm, mm=mm, forcefield=ff)
    filename, ext = os.path.splitext(input_file)
    outname = filename + '.garleek' + ext
    with open(outname, 'w') as f:
        f.write(patched)
    return outname


def _frontend_args(argv=None):
    p = ArgumentParser(prog='garleek')
    p.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    p.add_argument('--qm', type=str, default='gaussian',
                   help='QM program calling Garleek. Defaults to Gaussian. '
                        'Versions after an underscore: <engine>_<version>, '
                        'like gaussian_16')
    p.add_argument('--mm', type=str, default='tinker',
                   help='MM engine to use. Defaults to Tinker. '
                        'Versions after an underscore: <engine>_<version>, '
                        'like tinker_8')
    p.add_argument('--ff', type=_extant_file_prm, default='mm3.prm',
                   help='Forcefield to be used by the MM engine')
    p.add_argument('--types', type=_extant_file_types, default='uff_to_mm3',
                   help='Dictionary of QM-provided and MM-needed atom types. '
                   'Can be either one of {{{}}}, or a user-provided '
                   'two-column file'.format(','.join(BUILTIN_TYPES)))
    p.add_argument('input_file', type=_extant_file, help='QM input file (must match '
                  '--qm software)')

    return p.parse_args(argv)

