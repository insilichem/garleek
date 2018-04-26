#!/usr/bin/env python

import pytest
import numpy as np
from get_epout import read_energy_epout, read_dipole_epout
from get_EOu import read_energy_dipole_EOu

debyes_to_ebohr = 0.393430307
H_to_kcalmol = 627.509391
@pytest.mark.parametrize("filename_epout,filename_EOu", [
	("A_1.epout","A_1.EOu"),
	("A_2.epout","A_2.EOu"),
	("A_3.epout","A_3.EOu"),
	("A_4.epout","A_4.EOu"),
	("A_5.epout","A_5.EOu"),
	("C_1.epout","C_1.EOu"),
	("C_2.epout","C_2.EOu"),
	("C_3.epout","C_3.EOu"),
	("C_4.epout","C_4.EOu"),
	("C_5.epout","C_5.EOu"),
	("F_1.epout","F_1.EOu"),
	("F_2.epout","F_2.EOu"),
	("F_3.epout","F_3.EOu"),
	("F_4.epout","F_4.EOu"),
	("F_5.epout","F_5.EOu"),
	("I_1.epout","I_1.EOu"),
	("I_2.epout","I_2.EOu"),
	("I_3.epout","I_3.EOu"),
	("I_4.epout","I_4.EOu"),
	("I_5.epout","I_5.EOu")
])

def test_xyz(filename_epout,filename_EOu):
	energy_H, dipole_eao = read_energy_dipole_EOu(filename_EOu)
	assert abs(read_energy_epout(filename_epout) - energy_H * H_to_kcalmol) < 0.00001
	assert (np.fabs(read_dipole_epout(filename_epout) * debyes_to_ebohr - dipole_eao) < 0.00001).all()


