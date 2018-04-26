#!/usr/bin/env python

def take_oniomfirstenergy(file_name):
	file = open(file_name,"r")
	energy_lines = []
	for line in file:
		if "extrapolated" in line:
			energy_lines.append(line)
	file.close()
	return float(energy_lines[0].split()[-1])
	#return first_energy


#def take_oniomfinalenergy(file_name):
#	return final_energy
