#!/usr/bin/env python

import pytest
from take_energy import take_oniomfirstenergy, take_oniomfinalenergy

@pytest.mark.parametrize("file_name,score_first", [
	("A_1.out",-40.5169477995),
	("A_2.out",-40.5233765232),
	("A_3.out",-40.5224734295),
	("A_4.out",-40.5143237540),
	("A_5.out",-40.4989270186),
	("C_1.out",-193.1485133856),
	("C_2.out",-193.1486944717),
	("C_3.out",-193.1480104982),
	("C_4.out",-193.1313747380),
	("C_5.out",-193.1052642230),
	("F_1.out",-230.0133144465),
	("F_2.out",-230.0099794700),
	("F_3.out",-230.0091707175),
	("F_4.out",-230.0035733534),
	("F_5.out",-229.9907611201),
	("I_1.out",-212.5596205848),
	("I_2.out",-212.5590225077),
	("I_3.out",-212.5583834737),
	("I_4.out",-212.5400761854),
	("I_5.out",-212.5120633889)	
])

def test_oniomfirstenergy(file_name,score_first):
	assert (take_oniomfirstenergy(file_name)-score_first) < 0.00001

@pytest.mark.parametrize("file_name,score_final", [
	("A_1.out",-40.5183831801),
	("A_2.out",-40.5259660665),
	("A_3.out",-40.5262224376),
	("A_4.out",-40.5191711959),
	("A_5.out",-40.5048480820),
	("C_1.out",-193.1556928840),
	("C_2.out",-193.1580142719),
	("C_3.out",-193.1584125285),
	("C_4.out",-193.1513639128),
	("C_5.out",-193.1350405352),
	("F_1.out",-230.0205763478),
	("F_2.out",-230.0199076803),
	("F_3.out",-230.0214716060),
	("F_4.out",-230.0178768869),
	("F_5.out",-230.0040765028),
	("I_1.out",-212.5822884070),
	("I_2.out",-212.5835730795),
	("I_3.out",-212.5839368256),
	("I_4.out",-212.5764202974),
	("I_5.out",-212.5592647210)
])


def test_oniomfinalenergy(file_name,score_final):
	assert (take_oniomfinalenergy(file_name)-score_final) < 0.00001


