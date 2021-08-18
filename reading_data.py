import csv
import os
from math import sqrt
import subprocess

datafolder = "data/scenario1"

def find_power_in_A_real(filename):
	with open(filename) as csv_file:
		csv_reader = csv.reader(csv_file)
		# Find the power_in_A.real which is always column 5 row 10
		a = 0
		for row in csv_reader:
			if a == 9:
				power_in_A_real = row[4]
			a+=1
	return power_in_A_real

def find_all_powers_in_A_real(datafolder):
	reg_outputs = [f for f in os.listdir(datafolder) 
		if os.path.isfile(os.path.join(datafolder,f)) and f[-4:] == ".csv" and "reg" in f]
	reg_outputs.sort()

	with open('datapowerinA.csv', 'w', newline='') as csv_file:
		csv_writer = csv.writer(csv_file)
		for f in reg_outputs:
			csv_writer.writerow([f,find_power_in_A_real(os.path.join(datafolder,f))])

#find_all_powers_in_A_real(datafolder)

def overvoltage(filename_volts,filename_nominal):
	# Returns the list of nodes that have overvoltages, and by how much
	with open(filename_nominal)	as csv_file_nominal:
		csv_reader_nominal = csv.reader(csv_file_nominal)
		nominal_voltages = []
		# Find the nominal voltages, which are in row 10
		a = 0	
		for row in csv_reader_nominal:
			if a == 9:
				nominal_voltages = row[1:]
			a += 1
		for i in range(len(nominal_voltages)):
			nominal_voltages[i] = int(nominal_voltages[i])
	with open(filename_volts) as csv_file_volts:
			csv_reader_volts = csv.reader(csv_file_volts)
			a = 0
			for row in csv_reader_volts:
				if a >= 9:
					if a == 9:
						row_length = len(row)
						is_overvoltaged = [False]*(row_length-1)
						overvoltages = [0]*(row_length-1)
					for i in range(row_length-1):
						voltage_A_str = row[i+1]
						voltage_A_complex = complex(voltage_A_str)
						absolute_voltage = abs(voltage_A_complex)
						# Sometimes we need sqrt(3) here to convert from three phase power flow
						if absolute_voltage < 0.1:
							is_overvoltaged[i] = -1
						#elif absolute_voltage > 1.1*nominal_voltages[i]:

						# We test a 5% limit
						elif absolute_voltage > 1.05*nominal_voltages[i]:
							is_overvoltaged[i] = True
						if absolute_voltage > overvoltages[i]:
							overvoltages[i] = absolute_voltage
				a+=1
	return is_overvoltaged,overvoltages
"""
n = 20
for alpha in range(n+1):
	f = "optimal_PF/scenario3_GFC_alpha_" + str(alpha) + "_" + "R3-12.47-3_fixed.glm"
	subprocess.run(["/usr/local/bin/gridlabd",f])
	filename_volts = str(alpha) + "GFCbatt_node_volts_A_fixed.csv"
	filename_nominal = str(alpha) + "GFCbatt_node_nominal_volts_fixed.csv"
	overvoltages = is_overvoltaged(filename_volts,filename_nominal)
	S = 0
	nb_nodes = 0
	for b in overvoltages:
		if b == True:
			S += 1
			nb_nodes += 1
		elif b == False:
			nb_nodes += 1
	print(S,nb_nodes,S/nb_nodes)

"""
def max_overvoltage(filename_volts,filename_nominal):
	with open(filename_nominal)	as csv_file_nominal:
		csv_reader_nominal = csv.reader(csv_file_nominal)
		nominal_voltages = []
		# Find the nominal voltages which are in row 10

		a = 0	
		for row in csv_reader_nominal:
			if a == 9:
				nominal_voltages = row[1:]
			a += 1
		for i in range(len(nominal_voltages)):
			nominal_voltages[i] = int(nominal_voltages[i])
	with open(filename_volts) as csv_file_volts:
			csv_reader_volts = csv.reader(csv_file_volts)
			a = 0
			for row in csv_reader_volts:
				if a >= 9:
					if a == 9:
						row_length = len(row)
						overvoltages = [0]*(row_length-1)
					for i in range(row_length-1):
						voltage_A_str = row[i+1]
						voltage_A_complex = complex(voltage_A_str)
						absolute_voltage = abs(voltage_A_complex)
						# sqrt(3) ?
						if absolute_voltage > overvoltages[i]:
							overvoltages[i] = absolute_voltage
				a+=1
	return overvoltages

"""
n = 20

for alpha in range(n+1):

	filename_volts = str(alpha) + "GFCbatt_node_volts_A_fixed.csv"
	filename_nominal = str(alpha) + "GFCbatt_node_nominal_volts_fixed.csv"
	overvoltages = max_overvoltage(filename_volts,filename_nominal)
	if alpha == 0:
		max_alpha = [0]*len(overvoltages)
		max_overvoltages = overvoltages.copy()
	for i in range(len(max_alpha)):
		if overvoltages[i] > max_overvoltages[i]:
			max_alpha[i] = alpha
			max_overvoltages[i] = overvoltages[i]

alphas = [0]*21

for a in max_alpha:
	alphas[a] += 1

print(alphas)"""



folder = "data/scenario3/"

nominal_filename = "node_nominal_volts_fixed.csv"
volts_filename = "node_volts_A_fixed.csv"
prefixes = ["","2035","GFC","HP","hacked_2035","hacked_GFC","hacked_HP","hacked_reactive_2035",
"hacked_reactive_HP","hacked_reactive_GFC"]

"""
for p in prefixes:
	f = "testcases/scenario3/" + "scenario3_" + p + "R3-12.47-3_fixed.glm" 
	subprocess.run(["/usr/local/bin/gridlabd",f])
"""
for p in prefixes:
	full_nominal_filename = folder + p + nominal_filename
	full_volts_filename = folder + p + volts_filename
	is_overvoltaged,overvoltages = overvoltage(full_volts_filename,full_nominal_filename)
	S = 0
	total = 0
	for b in is_overvoltaged:
		if b == False:
			S+=1
		elif b == True:
			S+=1
			total += 1
	print(p,total,S,total/S)