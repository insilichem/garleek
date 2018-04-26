#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
import os


BUILTIN_TYPES = sorted(os.listdir(os.path.join((os.path.dirname(__file__)), 'data', 'atom_types')))


def get_file(filename):
    if os.path.exists(filename):
        return filename
    datapath = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'atom_types', filename)
    if os.path.exists(datapath):
        return datapath
    raise ValueError('Atom types definitions `{}` could not be found'.format(filename))


def parse(atom_types_filename):
    d = {}
    with open(atom_types_filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            fields = line.split('#', 1)[0].split()
            d[fields[0]] = fields[1]
    return d
