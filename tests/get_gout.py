#!/usr/bin/env python

import numpy as np


def read_gradient_gout(filename):
    parse_dxdydz = []
    with open(filename) as file:
        for line in file:
            fields = line.split()
            if len(fields) == 1:
                NAtoms = int(line)
            else:
                idx = fields[0]
                element = fields[1]
                dx,dy,dz = map(float, fields[2:5])
                parse_dxdydz.append([dx,dy,dz])

        dxdydzfromgout = np.array(parse_dxdydz)
    return NAtoms, xyzfromTinker


