#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
from argparse import ArgumentParser, REMAINDER, SUPPRESS, ArgumentTypeError
import os
import sys
from . import __version__
from .entry_points import gaussian_tinker
from .atom_types import get_file, parse as parse_atom_types, BUILTIN_TYPES
from .qm.gaussian import patch_gaussian_input

_here = os.path.dirname(os.path.abspath(__file__))

CONNECTORS = {
    'gaussian': {
        'tinker': gaussian_tinker
    }
}
QM_ENGINES = set(CONNECTORS)
MM_ENGINES = set([k for (qm, mm) in CONNECTORS.items() for k in mm])
PATCHERS = {
    'gaussian': patch_gaussian_input
}


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


def backend_app(argv=None):
    args = backend_args(argv)
    try:
        connector = CONNECTORS[args.qm][args.mm]
    except KeyError:
        sys.exit("ERROR: Connector with QM={} and MM={} "
                 "is not available".format(args.qm, args.mm))
    connector(args.qmargs, forcefield=args.ff)


def backend_args(argv=None):
    p = ArgumentParser()
    p.add_argument('--qm', type=str, default='gaussian', choices=QM_ENGINES,
                   help='QM program calling Garleek. Defaults to Gaussian')
    p.add_argument('--mm', type=str, default='tinker', choices=MM_ENGINES,
                   help='MM engine to use. Defaults to Tinker')
    p.add_argument('--ff', type=_extant_file, default='mmff.prm',
                   help='Forcefield to be used by the MM engine')
    # Arguments injected by the QM program
    p.add_argument('qmargs', nargs=REMAINDER, help=SUPPRESS)

    return p.parse_args(argv)


def frontend_app_main(argv=None):
    args = frontend_args(argv)
    frontend_app(**vars(args))


def frontend_app(input_file=None, types='uff_to_mm3', qm='gaussian', mm='tinker', 
                 ff=_extant_file_prm('mm3.prm'), **kw):
    rosetta = parse_atom_types(get_file(types))
    patcher = PATCHERS[qm]
    patched = patcher(input_file, rosetta, engine=mm, forcefield=ff)
    filename, ext = os.path.splitext(input_file)
    outname = filename + '.garleek' + ext
    with open(outname, 'w') as f:
        f.write(patched)
    return outname


def frontend_args(argv=None):
    p = ArgumentParser(prog='garleek')
    p.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    p.add_argument('--qm', type=str, default='gaussian', choices=QM_ENGINES,
                   help='QM program calling Garleek. Defaults to Gaussian')
    p.add_argument('--mm', type=str, default='tinker', choices=MM_ENGINES,
                   help='MM engine to use. Defaults to Tinker')
    p.add_argument('--ff', type=_extant_file_prm, default='mm3.prm',
                   help='Forcefield to be used by the MM engine')
    p.add_argument('--types', type=_extant_file_types, default='uff_to_mm3',
                   help='Dictionary of QM-provided and MM-needed atom types. '
                   'Can be either one of {{{}}}, or a user-provided '
                   'two-column file'.format(','.join(BUILTIN_TYPES)))
    p.add_argument('input_file', type=_extant_file, help='QM input file (must match '
                  '--qm software)')

    return p.parse_args(argv)
    
