#!/usr/bin/env python

import numpy as np


def read_energy_epout(filename):
    with open(filename) as file:
        for line in file:
            if 'Total Potential Energy' in line:
                fields = line.split()
                energy_kcal = float(fields[4])
                return energy_kcal




def read_dipole_epout(filename):
    with open(filename) as file:
        for line in file:
            if 'Dipole X,Y,Z-Components' in line:
                fields = line.split()
                x, y, z = map(float, fields[3:6])
                return np.array([x,y,z])


