#!/usr/bin/env python

import pytest
import numpy as np
from get_xyz import read_xyzfromTinker, read_xyzfromEIn

bohr_to_amstrong = 0.52918
@pytest.mark.parametrize("filename_EIn,filename_xyz", [
	("A_1.EIn","A_1.xyz"),
	("A_2.EIn","A_2.xyz"),
	("A_3.EIn","A_3.xyz"),
	("A_4.EIn","A_4.xyz"),
	("A_5.EIn","A_5.xyz"),
	("C_1.EIn","C_1.xyz"),
	("C_2.EIn","C_2.xyz"),
	("C_3.EIn","C_3.xyz"),
	("C_4.EIn","C_4.xyz"),
	("C_5.EIn","C_5.xyz"),
	("F_1.EIn","F_1.xyz"),
	("F_2.EIn","F_2.xyz"),
	("F_3.EIn","F_3.xyz"),
	("F_4.EIn","F_4.xyz"),
	("F_5.EIn","F_5.xyz"),
	("I_1.EIn","I_1.xyz"),
	("I_2.EIn","I_2.xyz"),
	("I_3.EIn","I_3.xyz"),
	("I_4.EIn","I_4.xyz"),
	("I_5.EIn","I_5.xyz")	
])

def test_xyz(filename_EIn,filename_xyz):
	num_atoms_ein, parsed_coords_ein = read_xyzfromEIn(filename_EIn)
	num_atoms_xyz, parsed_coords_xyz = read_xyzfromTinker(filename_xyz)
	assert (np.fabs(parsed_coords_ein * bohr_to_amstrong - parsed_coords_xyz) < 0.0001).all()
	assert (num_atoms_ein == num_atoms_xyz)


