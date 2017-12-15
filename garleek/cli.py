#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
import sys
from .entry_points import gaussian_tinker
from .atom_types import get_file, parse as parse_atom_types
from .qm.gaussian import patch_gaussian_input


CONNECTORS = {
    'gaussian': {
        'tinker': gaussian_tinker
    }
}


def run_app(argv=None):
    args = run_args(argv)
    try:
        connector = CONNECTORS[args.qm][args.mm]
    except KeyError:
        sys.exit("ERROR: Connector with QM={} and MM={} "
                 "is not available".format(args.qm, args.mm))

    connector(args.input_file, eou_filename=args.output_file,
              atom_types=args.atom_types, forcefield=args.ff)


def run_args(argv=None):
    p = ArgumentParser()
    p.add_argument('--mm')
    p.add_argument('--qm', default='gaussian')
    p.add_argument('--ff')
    p.add_argument('--atom_types')
    p.add_argument('layer')
    p.add_argument('input_file')
    p.add_argument('output_file')
    p.add_argument('msg_file')
    p.add_argument('fchk_file')
    p.add_argument('matel_file')

    return p.parse_args(argv)


# ATOM TYPES
PATCHERS = {
    'gaussian': patch_gaussian_input
}


def types_app(argv=None):
    args = types_args(argv)
    rosetta_path = get_file('{}_to_{}'.format(args.from_, args.to))
    rosetta = parse_atom_types(rosetta_path)
    rosetta.update(parse_atom_types(args.custom))
    patcher = PATCHERS[args.qm]
    patcher(args.input_file, rosetta, engine=args.mm, forcefield=args.ff)


def types_args(argv=None):
    p = ArgumentParser()
    p.add_argument('--qm', default='gaussian')
    p.add_argument('--mm', default='tinker')
    p.add_argument('--ff', default=None)
    p.add_argument('--from', default='uff')
    p.add_argument('--to', default='mm3')
    p.add_argument('--custom')
    p.add_argument('input_file')

    return p.parse_args(argv)
