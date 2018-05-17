#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
cli.py
======

This module contains the command-line interfaces for both
``garleek-prepare`` (the user-friendly patcher) and ``garleek-backend``
(the program the QM engine calls behind the scenes to handle
the MM calculations).

``garleek-preare`` takes a naive QM input file for ONIOM and patches it so
the MM part is performed through ``garleek-backend``, which will be
interfacing with the configured MM engine. For this to work, the
atom types featured in the QM input file should be understandable
by the MM engine, so ``garleek-prepare`` will replace those too, using the
``atom_types`` file mapping to do so.

In general, the worfklow is the following:

1. Build a standard ONIOM calculation, with layers, link atoms and
   so on. The ``garleek-prepare`` keyword should be present in the MM layer
   configuration so the patcher can find it and properly configure it.
2. Patch the QM input file with ``garleek-prepare``::

    garleek-prepare --qm <QM_engine> -mm <MM_engine> --ff <MM_forcefield> \\
                    --types <QM/MM_atom_type_dictionary> QM_input_file.in

3. Submit the calculation with the resulting patched file, named
   ``QM_input_file.garleek.in`` with the desired QM software::

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


def _extant_file(path, abspath=False):
    if os.path.isfile(path):
        if abspath:
            return os.path.abspath(path)
        return path
    raise ArgumentTypeError("File `{}` cannot be found".format(path))


def _extant_file_prm(path, abspath=False):
    if os.path.isfile(path):
        if abspath:
            return os.path.abspath(path)
        return path
    indatapath = os.path.join(_here, 'data', 'prm', path)
    if os.path.isfile(indatapath):
        if abspath:
            return indatapath
        return path
    if os.path.isfile(indatapath + '.prm'):
        if abspath:
            return indatapath + '.prm'
        return path
    raise ArgumentTypeError("File `{}` cannot be found".format(path))


def _extant_file_types(path, abspath=False):
    if os.path.isfile(path):
        if abspath:
            return os.path.abspath(path)
        return path
    indatapath = os.path.join(_here, 'data', 'atom_types', path)
    if os.path.isfile(indatapath):
        if abspath:
            return indatapath
        return path
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
    args = _backend_args(argv)
    msg = 'Entering Garleek v{}'.format(__version__)
    underline = '='*len(msg)
    print(underline)
    print(msg)
    print(underline)
    backend_app(**vars(args))
    print(underline)
    print('Exiting Garleek'.center(len(msg)))
    print(underline)


def backend_app(qmargs, qm='gaussian', mm='tinker', ff='mm3.prm', **kw):
    """
    ``garleek-backend`` Python entry-point

    Parameters
    ----------
    qmargs : tuple
        CLI arguments passed by the QM engine. This can be anything!
    qm : str
        QM engine to use. Must be one of ``QM_ENGINES``, optionally followed
        by ``_version`` to indicate slight differences in the QM logic.
        For example, ``gaussian`` defaults to ``gaussian_16``, but
        ``gaussian_09a`` exports the connectivity differently.
    mm : str
        MM engine to use. Must be one of ``MM_ENGINES``,optionally followed
        by ``_version`` to indicate slight differences in the MM logic.
    ff : str
        Forcefield to use in the MM part. This can be anything that the MM
        engine is able to use as a forcefield (normally a path to a file).

    Returns
    -------
    result :
        Whatever the QM-MM connector returns
    """
    qm_engine, qm_version = _parse_engine_string(qm)
    mm_engine, mm_version = _parse_engine_string(mm)
    try:
        connector = CONNECTORS[qm_engine][mm_engine]
    except KeyError:
        sys.exit("ERROR: Connector with QM={} and MM={} "
                 "is not available".format(qm_engine, qm_engine))
    return connector(qmargs, forcefield=_extant_file_prm(ff, abspath=True),
                     qm_version=qm_version, mm_version=mm_version, **kw)


def _backend_args(argv=None):
    p = ArgumentParser(description='Garleek executable called by QM engines '
                                   'to launch MM calculations. Users SHOULD NOT '
                                   'run this. Use `garleek-prepare` instead!')
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
    """ ``garleek-prepare`` CLI entry-point """
    args = _frontend_args(argv)
    out = frontend_app(**vars(args))
    print('Input file', out, 'is now ready! Please run it with your ', args.qm, 'executable!')


def frontend_app(input_file, types='uff_to_mm3', qm='gaussian', mm='tinker',
                 ff='mm3.prm', **kw):
    """
    ``garleek-prepare`` Python entry-point

    Parameters
    ----------
    input_file : str
        Path to the QM input file that should be patched so Garleek can
        handle the MM part through the desired MM engine.
    types : str, default=uff_to_mm3
        Path to a file listing the mapping between the QM atom types
        present in ``input_file`` and the MM atom types expected
        by the MM engine given the current forcefield. Atom types are
        case INSENSITIVE. They will be uppercased upon processing.
    qm : str
        QM engine to use. Must be one of ``QM_ENGINES``, optionally followed
        by ``_version`` to indicate slight differences in the QM logic.
        For example, ``gaussian`` defaults to ``gaussian_16``, but
        ``gaussian_09a`` exports the connectivity differently. This is only
        needed so the patched ``garleek-backend`` calls include this argument.
    mm : str
        MM engine to use. Must be one of ``MM_ENGINES``,optionally followed
        by ``_version`` to indicate slight differences in the MM logic. This is only
        needed so the patched ``garleek-backend`` calls include this argument.
    ff : str
        Path to the forcefield the MM engine will be using to compute
        values requested by the QM engine. It should conform to the
        specified ``types`` mapping. This is only needed so the patched
        ``garleek-backend`` calls include this argument.

    Returns
    -------
    outname : str
        Path to patched input file. It will always be a derivative of ``input_file``.
        If ``input_file`` is ``input.in``, ``outname`` will be ``input.garleek.in``.
    """
    qm_engine, qm_version = _parse_engine_string(qm)
    rosetta = parse_atom_types(get_file(types))
    patcher = PATCHERS[qm_engine]
    patched = patcher(input_file, rosetta, qm=qm, mm=mm, forcefield=ff, **kw)
    filename, ext = os.path.splitext(input_file)
    outname = filename + '.garleek' + ext
    with open(outname, 'w') as f:
        f.write(patched)
    return outname


def _frontend_args(argv=None):
    p = ArgumentParser(prog='garleek-prepare',
        description='This executable patches QM input files so they are compatible '
                    'with the selected MM engine.')
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
                   help='Dictionary of QM-provided and MM-needed, case-insensitive atom types. '
                   'Can be either one of {{{}}}, or a user-provided '
                   'two-column file'.format(','.join(BUILTIN_TYPES)))
    p.add_argument('input_file', type=_extant_file, help='QM input file (must match '
                  '--qm software requirements.)')

    return p.parse_args(argv)

