#!/usr/bin/env python

import numpy as np


def read_xyzfromTinker(filename):
    parse_xyz = []
    with open(filename) as file:
        for line in file:
            fields = line.split()
            if len(fields) == 1:
                NAtoms = int(line)
            else:
                idx = fields[0]
                element = fields[1]
                x,y,z = map(float, fields[2:5])
                parse_xyz.append([x,y,z])

        xyzfromTinker = np.array(parse_xyz)
    return NAtoms, xyzfromTinker


def read_xyzfromEIn(filename):
    parse_xyz = []
    with open(filename) as file:
        for i,line in enumerate(file):
            fields = line.split()
            if i == 0:
                NAtoms = int(fields[0])
            elif 0 < i < NAtoms +1:
                x,y,z = map(float, fields[1:4])
                parse_xyz.append([x,y,z])

        xyz_from_EIn = np.array(parse_xyz)
    return NAtoms, xyz_from_EIn

