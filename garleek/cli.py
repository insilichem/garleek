#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser, REMAINDER, SUPPRESS
import os
import sys
from .entry_points import gaussian_tinker
from .atom_types import get_file, parse as parse_atom_types
from .qm.gaussian import patch_gaussian_input


CONNECTORS = {
    'gaussian': {
        'tinker': gaussian_tinker
    }
}
QM_ENGINES = set(CONNECTORS)
MM_ENGINES = set([k for (qm, mm) in CONNECTORS.items() for k in mm])


def run_app(argv=None):
    args = run_args(argv)
    try:
        connector = CONNECTORS[args.qm][args.mm]
    except KeyError:
        sys.exit("ERROR: Connector with QM={} and MM={} "
                 "is not available".format(args.qm, args.mm))

    connector(forcefield=args.ff, *args.qmargs)


def run_args(argv=None):
    p = ArgumentParser()
    p.add_argument('--qm', type=str, default='gaussian', choices=QM_ENGINES,
                   help='QM program calling Garleek. Defaults to Gaussian')
    p.add_argument('--mm', type=str, default='tinker', choices=MM_ENGINES,
                   help='MM engine to use. Defaults to Tinker')
    p.add_argument('--ff', type=str, default='mm3',
                   help='Forcefield to be used by the MM engine')
    # Arguments injected by the QM program
    p.add_argument('qmargs', nargs=REMAINDER, help=SUPPRESS)

    return p.parse_args(argv)


# ATOM TYPES
PATCHERS = {
    'gaussian': patch_gaussian_input
}


def types_app(argv=None):
    args = types_args(argv)
    rosetta = parse_atom_types(get_file(args.types))
    patcher = PATCHERS[args.qm]
    patched = patcher(args.input_file, rosetta, engine=args.mm, forcefield=args.ff)
    filename, ext = os.path.splitext(args.input_file)
    with open(filename + '.garleek' + ext, 'w') as f:
        f.write(patched)


def types_args(argv=None):
    p = ArgumentParser()
    p.add_argument('--qm', type=str, default='gaussian', choices=QM_ENGINES,
                   help='QM program calling Garleek. Defaults to Gaussian')
    p.add_argument('--mm', type=str, default='tinker', choices=MM_ENGINES,
                   help='MM engine to use. Defaults to Tinker')
    p.add_argument('--ff', type=str, default='mm3',
                   help='Forcefield to be used by the MM engine')
    p.add_argument('--types', default='uff_to_mm3',
                   help='Dictionary of QM-provided and MM-needed atom types')
    p.add_argument('input_file')

    return p.parse_args(argv)
