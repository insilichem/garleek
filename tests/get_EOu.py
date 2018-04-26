#!/usr/bin/env python

import numpy as np


def read_energy_dipole_EOu(filename):
    with open(filename) as file:
        line = next(file).split()
        energy_H = float(line[0])
        x, y, z = map(float, line[1:4])
        dipole_eao = np.array([x,y,z])
        return energy_H, dipole_eao

print(read_energy_dipole_EOu("C_5.EOu"))
