#!/usr/bin/env python

def take_oniomfirstenergy(file_name):
	with open(file_name,"r") as file:
		energy_lines = [line for line in file if "extrapolated" in line]
		return float(energy_lines[0].split()[-1])

def take_oniomfinalenergy(file_name):
	with open(file_name,"r") as file:
		energy_lines = [line for line in file if "extrapolated" in line]
		return float(energy_lines[-1].split()[-1])

print(take_oniomfirstenergy("A_3.out"))
print(take_oniomfinalenergy("A_3.out"))
